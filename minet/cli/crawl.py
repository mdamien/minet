# =============================================================================
# Minet Crawl CLI Action
# =============================================================================
#
# Logic of the crawl action.
#
import os
import csv
from os.path import join, isfile, dirname
from tqdm import tqdm
from shutil import rmtree

from minet.crawl import Crawler
from minet.utils import load_definition
from minet.cli.reporters import report_error
from minet.cli.utils import print_err

JOBS_HEADERS = [
    'spider',
    'url',
    'resolved',
    'status',
    'error',
    'filename',
    'encoding',
    'next',
    'level'
]


def format_job_for_csv(result):
    if result.error is not None:
        return [
            result.job.spider,
            result.job.url,
            '',
            '',
            report_error(result.error),
            '',
            '',
            '0',
            result.job.level
        ]

    resolved = result.response.geturl()

    return [
        result.job.spider,
        result.job.url,
        resolved if resolved != result.job.url else '',
        result.response.status,
        '',
        '',
        result.meta.get('encoding', ''),
        len(result.next_jobs) if result.next_jobs is not None else '0',
        result.job.level
    ]


def open_report(path, headers, resume=False):
    flag = 'w'

    if resume and isfile(path):
        flag = 'a'

    os.makedirs(dirname(path), exist_ok=True)

    f = open(path, flag)
    writer = csv.writer(f)

    if flag == 'w':
        writer.writerow(headers)

    return f, writer


class ScraperReporter(object):
    def __init__(self, path, scraper, resume=False):
        if scraper.headers is None:
            raise NotImplementedError('Scraper headers could not be inferred.')

        f, writer = open_report(path, scraper.headers, resume)

        self.headers = scraper.headers
        self.file = f
        self.writer = writer

    def write(self, items):

        # TODO: maybe abstract this once step above
        if not isinstance(items, list):
            items = [items]

        for item in items:
            if not isinstance(item, dict):
                self.writer.writerow([item])
                continue

            row = [item.get(k, '') for k in self.headers]
            self.writer.writerow(row)

    def close(self):
        self.file.close()


class ScraperReporterPool(object):
    SINGLE_SCRAPER = '$SINGLE_SCRAPER$'

    def __init__(self, crawler, output_dir, resume=False):
        self.reporters = {}

        if crawler.single_spider:
            spider = crawler.spiders['default']

            self.reporters['default'] = {}

            if spider.scraper is not None:
                path = join(output_dir, 'scraped.csv')
                reporter = ScraperReporter(path, scraper, resume)
                self.reporters['default'][ScraperReporterPool.SINGLE_SCRAPER] = reporter

            for name, scraper in spider.scrapers.items():
                path = join(output_dir, 'scraped', '%s.csv' % name)

                reporter = ScraperReporter(path, scraper, resume)
                self.reporters['default'][name] = reporter
        else:
            for spider_name, spider in crawler.spiders.items():
                self.reporters[spider_name] = {}

                if spider.scraper is not None:
                    path = join(output_dir, 'scraped', spider_name, 'scraped.csv')
                    reporter = ScraperReporter(path, scraper, resume)
                    self.reporters[spider_name][ScraperReporterPool.SINGLE_SCRAPER] = reporter

                for name, scraper in spider.scrapers.items():
                    path = join(output_dir, 'scraped', spider_name, '%s.csv' % name)

                    reporter = ScraperReporter(path, scraper, resume)
                    self.reporters[spider_name][name] = reporter

    def write(self, spider_name, scraped):
        reporter = self.reporters[spider_name]

        if scraped['single'] is not None:
            reporter[ScraperReporterPool.SINGLE_SCRAPER].writer(scraped['single'])

        for name, items in scraped['multiple'].items():
            reporter[name].write(items)

    def close(self):
        for spider_reporters in self.reporters.values():
            for reporter in spider_reporters.values():
                reporter.close()


def crawl_action(namespace):

    # Loading crawler definition
    queue_path = join(namespace.output_dir, 'queue')
    definition = load_definition(namespace.crawler)

    if namespace.resume:
        print_err('Resuming crawl...')
    else:
        rmtree(queue_path, ignore_errors=True)

    # Scaffolding output directory
    os.makedirs(namespace.output_dir, exist_ok=True)

    jobs_output_path = join(namespace.output_dir, 'jobs.csv')
    jobs_output, jobs_writer = open_report(
        jobs_output_path,
        JOBS_HEADERS,
        resume=namespace.resume
    )

    # Creating crawler
    crawler = Crawler(
        definition,
        throttle=namespace.throttle,
        queue_path=queue_path
    )

    reporter_pool = ScraperReporterPool(
        crawler,
        namespace.output_dir,
        resume=namespace.resume
    )

    # Loading bar
    loading_bar = tqdm(
        desc='Crawling',
        unit=' pages',
        dynamic_ncols=True
    )

    def update_loading_bar(result):
        state = crawler.state

        loading_bar.set_postfix(queue=state.jobs_queued, spider=result.job.spider)
        loading_bar.update()

    # Starting crawler
    crawler.start()

    # Running crawler
    for result in crawler:
        update_loading_bar(result)
        jobs_writer.writerow(format_job_for_csv(result))

        if result.error is not None:
            continue

        reporter_pool.write(result.job.spider, result.scraped)

    loading_bar.close()
    jobs_output.close()
    reporter_pool.close()

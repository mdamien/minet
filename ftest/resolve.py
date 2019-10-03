from minet.utils import resolve, create_safe_pool

URLS = [
    'http://bit.ly/2KkpxiW',

    # Self loop
    'https://demo.cyotek.com/features/redirectlooptest.php',
    'https://bit.ly/2gnvlgb',

    # Meta refresh & UA nonsense
    'http://bit.ly/2YupNmj',

    # Invalid URL
    'http://www.outremersbeyou.com/talent-de-la-semaine-la-designer-comorienne-aisha-wadaane-je-suis-fiere-de-mes-origines/',

    # Refresh header
    'http://la-grange.net/2015/03/26/refresh/',

    # GET & UA nonsense
    'https://ebay.us/BUkuxU'
]

http = create_safe_pool()

for url in URLS:
    print()
    error, stack = resolve(http, url, follow_meta_refresh=True)
    print(error)
    for item in stack:
        print(item)

# import csv
# from minet import multithreaded_resolve
# from tqdm import tqdm

# with open('./ftest/resources/resolutions.csv') as f, \
#      open('./ftest/resolved.csv', 'w') as of:
#     reader = csv.DictReader(f)
#     writer = csv.writer(of)
#     writer.writerow(['original', 'resolved', 'error'])

#     for result in tqdm(multithreaded_resolve(reader, key=lambda x: x['url'], threads=100), total=10000):
#         stack = result.stack
#         error = result.error

#         original = stack[0][1] if stack else ''
#         last = stack[-1][1] if stack else ''

#         writer.writerow([
#             original,
#             last if last != original else '',
#             str(error) if error else ''
#         ])

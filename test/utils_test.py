# =============================================================================
# Minet Utils Unit Tests
# =============================================================================
from minet.utils import (
    nested_get,
    parse_http_refresh,
    find_meta_refresh,
    find_javascript_relocation,
    JAVASCRIPT_LOCATION_RE
)

HTTP_REFRESH_TESTS = [
    ('0;url=https://www.youtube.com/watch?v=sTJ1XwGDcA4', (0, 'https://www.youtube.com/watch?v=sTJ1XwGDcA4')),
    ('0;url=https://www.youtube.com/watch?v=sTJ1XwGDcA4   ', (0, 'https://www.youtube.com/watch?v=sTJ1XwGDcA4')),
    ('   0;URL=https://www.youtube.com/watch?v=sTJ1XwGDcA4', (0, 'https://www.youtube.com/watch?v=sTJ1XwGDcA4')),
    ('test;url=https://www.youtube.com/watch?v=sTJ1XwGDcA4', None),
    ('0;/www.youtube.com/watch?v=sTJ1XwGDcA4', None)
]

META_REFRESH = rb'''
    <head>
        <noscript>
            <META http-equiv="refresh" content="0;URL=https://twitter.com/i/web/status/1155764949777620992">
        </noscript>
        <title>https://twitter.com/i/web/status/1155764949777620992</title>
    </head>
    <script>
        window.opener = null;
        location.replace("https:\/\/twitter.com\/i\/web\/status\/1155764949777620992")
    </script>
'''

NESTED_OBJECT = {
    'a': {
        'b': [{'c': 4}],
        'd': {
            'e': 5
        }
    }
}

JAVASCRIPT_LOCATION = rb'''
    <head>
        <title>https://twitter.com/i/web/status/1155764949777620992</title>
    </head>
    <script>
        window.opener = null;
        location = "https:\/\/twitter.com\/i\/web\/status\/0"
        window.location = "https:\/\/twitter.com\/i\/web\/status\/1"
        location.replace("https:\/\/twitter.com\/i\/web\/status\/2");location = "https:\/\/twitter.com\/i\/web\/status\/3"
        window.location.replace("https:\/\/twitter.com\/i\/web\/status\/4")
        window.location='https:\/\/twitter.com\/i\/web\/status\/5'
        window.location      ="https:\/\/twitter.com\/i\/web\/status\/6"
    </script>
'''


class TestUtils(object):
    def test_nested_get(self):
        assert nested_get('a.d.e', NESTED_OBJECT) == 5
        assert nested_get('b.d.a.a', NESTED_OBJECT) is None
        assert nested_get(['a', 'b', 0, 'c'], NESTED_OBJECT) == 4
        assert nested_get(['a', 'b', 1, 'c', 2], NESTED_OBJECT) is None

    def test_parse_http_refresh(self):
        for header_value, result in HTTP_REFRESH_TESTS:
            assert parse_http_refresh(header_value) == result

    def test_find_meta_refresh(self):
        meta_refresh = find_meta_refresh(META_REFRESH)

        assert meta_refresh == (0, 'https://twitter.com/i/web/status/1155764949777620992')

    def test_find_javascript_relocation(self):
        locations = JAVASCRIPT_LOCATION_RE.findall(JAVASCRIPT_LOCATION)

        r = set(int(m.decode().rsplit('/', 1)[-1]) for m in locations)

        assert r == set(range(7))

        location = find_javascript_relocation(JAVASCRIPT_LOCATION)

        assert location == 'https://twitter.com/i/web/status/0'

        location = find_javascript_relocation(META_REFRESH)

        assert location == 'https://twitter.com/i/web/status/1155764949777620992'

        location = find_javascript_relocation(b'NOTHING')

        assert location is None

import sys


PY2 = sys.version_info[0] == 2


if not PY2:
    import http.client as http_client
    from urllib.request import build_opener, HTTPHandler, install_opener
    from urllib.response import addinfourl
else:
    import http.client as http_client
    from urllib.request import build_opener, HTTPHandler, install_opener

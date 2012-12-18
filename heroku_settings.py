import logging, os
URL_ROOT = os.environ['URL_ROOT']
LOG_LEVEL = getattr(logging, os.environ['LOG_LEVEL'])
SEND_EMAIL = os.environ['SEND_EMAIL'] == '1'
EMAIL_LEVEL = getattr(logging, os.environ['EMAIL_LEVEL'])
MAIL_HOST = ('smtp.gmail.com', 587)
MAIL_FROMADDR = os.environ['FROMADDR']
MAIL_TOADDRS = [os.environ['ADMIN_EMAIL']]
MAIL_CREDENTIALS = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])
MAIL_SECURE = ()
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
NAVER_USERNAME = os.environ['NAVER_USERNAME']
NAVER_PASSWORD = os.environ['NAVER_PASSWORD']
CACHE_TYPE = 'memcached'
CACHE_KEY_PREFIX = 'naverwebtoonfeeds'
CACHE_MEMCACHED_SERVERS = [os.environ['MEMCACHE_SERVERS']]
CACHE_MEMCACHED_USERNAME = os.environ['MEMCACHE_USERNAME']
CACHE_MEMCACHED_PASSWORD = os.environ['MEMCACHE_PASSWORD']

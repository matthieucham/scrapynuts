# -*- coding: utf-8 -*-

# Scrapy settings for scrapynuts project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
# http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
# http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

BOT_NAME = 'scrapynuts'

SPIDER_MODULES = ['scrapynuts.spiders']
NEWSPIDER_MODULE = 'scrapynuts.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'scrapynuts (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'scrapynuts.middlewares.ScrapynutsSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapynuts.middlewares.SeleniumDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'scrapynuts.pipelines.ScrapynutsFilterPipeline': 300,
    'scrapynuts.pipelines.ScrapynutsPostStatnutsPipeline': 306,
    # 'scrapynuts.pipelines.ScrapynutsTeamFilterPipeline': 300,
    # 'scrapynuts.pipelines.ScrapynutsPostTeamStatnutsPipeline': 306,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


SELENIUM_CHROMEDRIVER_PATH = '%s\\resources\\chromedriver.exe' % ROOT_DIR
SELENIUM_CHROMEADBLOCK_PATH = '%s\\resources\\Adblock-Plus.crx' % ROOT_DIR

# TODO remove if not test
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

STATNUTS_CLIENT_ID = 'F5K43vYvKUnm9OaiLhC0HGh0Sqmq0Zr42uhFX0JS'
STATNUTS_SECRET = 'HdaNhSy3if0Qm5kkc04TfTiLjT7N97rQsjIcgn1Fx6io7Q4SboIQRctU4JU1F3prBCsJw5DS134p3nrEur9EiqCHNziM8wNqGHTArV6F1VeUju65k99JFHw7PU8SiWuT'
# STATNUTS_URL = 'http://127.0.0.1:8000/'
STATNUTS_URL = 'https://statnuts.django.group/'

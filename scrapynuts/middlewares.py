# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import time
import random

from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from . import settings


class ScrapynutsSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SeleniumDownloaderMiddleware(object):
    def __init__(self):
        chop = webdriver.ChromeOptions()
        chop.add_extension(settings.SELENIUM_CHROMEADBLOCK_PATH)
        self.driver = webdriver.Chrome(settings.SELENIUM_CHROMEDRIVER_PATH, chrome_options=chop)  # your chosen driver
        # ffprofile = webdriver.FirefoxProfile()
        # ffprofile.add_extension(settings.SELENIUM_GECKOADBLOCK_PATH)
        # self.driver = webdriver.Firefox(ffprofile, executable_path=settings.SELENIUM_GECKODRIVER_PATH)

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.engine_stopped, signal=signals.engine_stopped)
        return s

    def engine_stopped(self):
        self.driver.quit()

    def process_request(self, request, spider):
        # only process tagged request or delete this if you want all
        if not request.meta.get('selenium'):
            return
        time.sleep(random.random())  # randomize behavior to pass incap.
        self.driver.get(request.url)
        if request.meta.get('wait_for_xpath') is not None:
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                     request.meta.get(
                                                                                         'wait_for_xpath'))))
            finally:
                pass
        if request.meta.get('click_on_xpath') is not None:
            target = self.driver.find_element_by_xpath(request.meta.get('click_on_xpath'))
            time.sleep(random.random())
            try:
                target.click()
            except WebDriverException as e:
                # target is not clickable probably because of a modal in front : quantcast
                try:
                    self.driver.find_element_by_css_selector('button[class="qc-cmp-button"]').click()
                    WebDriverWait(self.driver, 10).until(
                        EC.invisibility_of_element_located((By.CLASS_NAME, 'qc-cmp-ui-container')))
                finally:
                    pass
            if request.meta.get('wait_after_click') is not None:
                try:
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                         request.meta.get(
                                                                                             'wait_after_click'))))
                finally:
                    pass
        body = self.driver.page_source
        response = HtmlResponse(url=self.driver.current_url, body=body, encoding='utf-8')
        return response

# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule

from utils import RestrictTextLinkExtractor


class MaxifootSpider(CrawlSpider):
    name = 'maxifoot'
    allowed_domains = ['maxifoot.fr']
    start_urls = ['http://www.maxifoot.fr/foot-matchs_ligue1-1.htm', 'http://www.maxifoot.fr/foot-matchs_ligue1-2.htm']

    def test_link(value):
        print(value)
        pass

    rules = (
        Rule(RestrictTextLinkExtractor(allow=('football/article',),
                                       restrict_xpaths='//div[@id="main"]',
                                       link_text_regex=u'NOTES des joueurs \(', process_value=test_link), follow=True),
    )


    def parse_item(self, response):
        i = {}
        # i['domain_id'] = response.xpath('//input[@id="sid"]/@value').extract()
        # i['name'] = response.xpath('//div[@id="name"]').extract()
        #i['description'] = response.xpath('//div[@id="description"]').extract()
        return i

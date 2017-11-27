# -*- coding: utf-8 -*-
import hashlib
import re

from scrapy.spiders import CrawlSpider, Rule
import unidecode

from utils import RestrictTextLinkExtractor

from .. import items


class HommedumatchSpider(CrawlSpider):
    name = 'hommedumatch'
    allowed_domains = ['hommedumatch.fr']
    start_urls = ['http://www.hommedumatch.fr/category/france', 'http://www.hommedumatch.fr/category/france/page/2']

    rules = (
        Rule(RestrictTextLinkExtractor(allow=('ligue\-1',), link_text_regex=u'Ligue 1.+Les notes de',
                                       unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'HDM')
        title = response.xpath('//article/header/h1/text()').extract_first()
        title_matched = re.match(
            u'Ligue 1 \W (\d+)\D+ Les notes de ([\w|\-| ]+)\s*\W\s*([\w|\-| ]+) \((\d+)\s*\W\s*(\d+)\)$',
            title)
        loader.add_value('home_team', unidecode.unidecode(title_matched.group(2).strip()))
        loader.add_value('away_team', unidecode.unidecode(title_matched.group(3).strip()))
        loader.add_value('home_score', title_matched.group(4).strip())
        loader.add_value('away_score', title_matched.group(5).strip())
        loader.add_value('step', title_matched.group(1))
        loader.add_xpath('match_date', '//time/@datetime')
        homeplayers = response.xpath('//div[@id="cspc-column-0"]/p/*[self::strong or self::b]/text()').extract()
        awayplayers = response.xpath('//div[@id="cspc-column-1"]/p/*[self::strong or self::b]/text()').extract()
        for pl in homeplayers:
            loader.add_value('players_home', self.get_player(unidecode.unidecode(pl)))
        for pl in awayplayers:
            loader.add_value('players_away', self.get_player(unidecode.unidecode(pl)))

        yield loader.load_item()

    def get_player(self, pl):
        strong_pattern = u'([\w|\-| ]+)\(([\d|,|\.]+)\)'
        matched = re.search(strong_pattern, pl)
        if matched:
            loader = items.PlayerItemLoader()
            loader.add_value('name', matched.group(1).strip())
            loader.add_value('rating', matched.group(2).strip().replace(',', '.'))
            yield dict(loader.load_item())
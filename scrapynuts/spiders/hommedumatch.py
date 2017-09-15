# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import hashlib
import re
from .. import items


class HommedumatchSpider(CrawlSpider):
    name = 'hommedumatch'
    allowed_domains = ['hommedumatch.fr']
    start_urls = ['http://www.hommedumatch.fr/category/france', 'http://www.hommedumatch.fr/category/france/page/2']

    rules = (
        Rule(LinkExtractor(allow=('ligue\-1(.*)notes\-de\-',), unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'HDM')
        title = response.xpath('//article/header/h1/text()').extract_first()
        title_matched = re.match(u'Ligue 1 \W (\d+)\D+ Les notes de ([\w|\-| ]+)\W+([\w|\-| ]+) \((\d+)\-(\d+)\)$',
                                 title)
        loader.add_value('home_team', title_matched.group(2).strip())
        loader.add_value('away_team', title_matched.group(3).strip())
        loader.add_value('home_score', title_matched.group(4).strip())
        loader.add_value('away_score', title_matched.group(5).strip())
        loader.add_value('step', title_matched.group(1))

        homeplayers = response.xpath('//div[@id="cspc-column-0"]/p/strong/text()').extract()
        awayplayers = response.xpath('//div[@id="cspc-column-1"]/p/strong/text()').extract()
        for pl in homeplayers:
            loader.add_value('players_home', self.get_player(pl))
        for pl in awayplayers:
            loader.add_value('players_away', self.get_player(pl))

        yield loader.load_item()

    def get_player(self, pl):
        strong_pattern = u'([\w|\-| ]+)\(([\d|,|\.]+)\)[ |:]+'
        print(pl)
        matched = re.search(strong_pattern, pl)
        if matched:
            loader = items.PlayerItemLoader()
            loader.add_value('name', matched.group(1).strip())
            loader.add_value('rating', matched.group(2).strip().replace(',', '.'))
            yield dict(loader.load_item())
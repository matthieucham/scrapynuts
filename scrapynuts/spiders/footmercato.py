# -*- coding: utf-8 -*-
import hashlib
import re

from scrapy.spiders import CrawlSpider, Rule
from unidecode import unidecode

from .. import items
from scrapy.linkextractors import LinkExtractor


class FootmercatoSpider(CrawlSpider):
    name = 'footmercato'
    allowed_domains = ['footmercato.net']
    start_urls = ['https://www.footmercato.net/france/ligue-1/club', ]

    rules = (
        Rule(LinkExtractor(allow=[r'actualite$']), follow=True),
        Rule(LinkExtractor(allow=[r'les\-notes\-du\-match'], unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath('//li[@class="article__date"]//time/@datetime').extract_first()
        loader.add_value('hash_url', hashlib.md5(response.url.encode('utf-8')).hexdigest())
        loader.add_value('source', 'FMERC')
        loader.add_value('match_date', md)
        
        summary = response.xpath('//ul[@class="article__matches"]')
        hteam = summary.xpath('li/a/span[@class="matchItem__team matchItem__team--home"]/span[@class="matchItem__team__name"]/text()').extract_first().strip()
        hscore = summary.xpath('li/a//span[@class="matchItem__score__value matchItem__score__value--home"]/text()').extract_first().strip()
        ateam = summary.xpath('li/a//span[@class="matchItem__team matchItem__team--away"]/span[@class="matchItem__team__name"]/text()').extract_first().strip()
        ascore = summary.xpath('li/a//span[@class="matchItem__score__value matchItem__score__value--away"]/text()').extract_first().strip()
        
        teamplayers_uls = response.xpath('//div[@class="article__content"]//ul')
        
        hpltext = teamplayers_uls[0].xpath('li/p/strong/text()').extract()
        apltext = teamplayers_uls[1].xpath('li/p/strong/text()').extract()
        
        hplset = set()
        for player in hpltext:
            if player.startswith("Remplac"):
                continue
            pl = self.get_player(player)
            if pl:
                hplset.add(pl)
            
        aplset = set()
        for player in apltext:
            if player.startswith("Remplac"):
                continue
            pl = self.get_player(player)
            if pl:
                aplset.add(pl)

        loader.add_value('home_team', hteam)
        loader.add_value('home_score', hscore)
        loader.add_value('away_team', ateam)
        loader.add_value('away_score', ascore)
        for n, r in hplset:
            loader.add_value('players_home', {'name': n, 'rating': r})
        for n, r in aplset:
            loader.add_value('players_away', {'name': n, 'rating': r})
        yield loader.load_item()

    def get_player(self, pl):
        player_regex = r'([^\s^\(]+)\s*\(([0-9,\.]{1,3})\)\s:'
        matched = re.match(player_regex, pl.replace(u'\xa0', u' '))
        if matched:
            return unidecode(matched.group(1).strip()), matched.group(2).replace(',', '.')

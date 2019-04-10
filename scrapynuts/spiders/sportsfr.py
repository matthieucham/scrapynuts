# -*- coding: utf-8 -*-
import re

from pytz import timezone
import dateparser
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from .. import items
import hashlib


class SportsfrSpider(CrawlSpider):
    name = 'sportsfr'
    allowed_domains = ['sports.fr']
    start_urls = ['http://www.sports.fr/football/ligue-1/resultats.html',
                  'http://www.sports.fr/football/ligue-1/2019/resultats/27e-journee.html']

    rules = (
        Rule(LinkExtractor(allow='football/directs/ligue-1/', restrict_xpaths='//table[@class="nwResultats"]')),
        Rule(LinkExtractor(allow='football/compte-rendu/ligue-1/',
                           restrict_xpaths='//div[@id="direct"]'), callback='parse_match')
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)

        loader = items.MatchItemLoader(items.MatchItem(), response=response)
        md = response.xpath(
            '(//div[@class="scoreboard"]/div[@class="sb-inner"]/div[@class="sb-content"]/div[@class="sb-metas"])[last()]/text()').extract_first().strip()
        try:
            date_text = re.search(u'Le ([\d|/]+)\D*(\d+h\d+)', md)
            dt = dateparser.parse('%s %s' % (date_text.group(1), date_text.group(2)), languages=['fr'])
            paristz = timezone('Europe/Paris')
            loc_dt = paristz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        loader.add_value('step', re.search(u'(\d+)\D+ journ', md).group(1))
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'SPORT')
        loader.add_value('match_date', game_date)
        loader.add_xpath('home_team',
                         '//div[@class="scoreboard"]//div[@class="sb-team sb-team1"]//div[@class="sb-team-name"]/text()')
        loader.add_xpath('away_team',
                         '//div[@class="scoreboard"]//div[@class="sb-team sb-team2"]//div[@class="sb-team-name"]/text()')
        loader.add_xpath('home_score',
                         '//div[@class="scoreboard"]//div[@class="sb-team sb-team1"]//div[@class="sb-team-score"]/text()')
        loader.add_xpath('away_score',
                         '//div[@class="scoreboard"]//div[@class="sb-team sb-team2"]//div[@class="sb-team-score"]/text()')

        field = response.xpath('//div[@class="stade"]')
        homeplayers = field.xpath('div[@class="compo team1"]/ul/li')
        awayplayers = field.xpath('div[@class="compo team2"]/ul/li')
        for pl in homeplayers:
            loader.add_value('players_home', self.get_player(pl))
        for pl in awayplayers:
            loader.add_value('players_away', self.get_player(pl))
        yield loader.load_item()

    def get_player(self, pl):
        href_pattern = "/football/joueurs/[0-9]{1,2}/([a-z\-]+)\-[0-9]{3,6}.html"
        href = pl.xpath('a/@href').extract_first().strip()

        loader = items.PlayerItemLoader()
        loader.add_value('name', re.match(href_pattern, href).group(1).replace('-', ' '))
        mark = pl.xpath('a/span[@class="numero"]/text()').extract_first()
        try:
            float(mark)
            loader.add_value('rating', mark)
            yield dict(loader.load_item())
        except ValueError:
            pass

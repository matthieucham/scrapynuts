# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from .. import items


class SportsfrSpider(CrawlSpider):
    name = 'sportsfr'
    allowed_domains = ['sports.fr']
    start_urls = ['http://www.sports.fr/football/ligue-1/resultats.html']

    rules = (
        Rule(LinkExtractor(allow='football/directs/ligue-1/', restrict_xpaths='//table[@class="nwResultats"]')),
        Rule(LinkExtractor(allow='football/compte-rendu/ligue-1/',
                           restrict_xpaths='//div[@id="direct"]'), callback='parse_match')
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)

        loader = items.MatchItemLoader(items.MatchItem(), response=response)
        loader.add_xpath('match_date',
                         '(//div[@class="scoreboard"]/div[@class="sb-inner"]/div[@class="sb-content"]/div[@class="sb-metas"])[last()]/text()')
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
        href_pattern = "/football/joueurs/[0-9]{1,2}/([a-z\-]+)\-[0-9]{3,6}.html"
        for pl in homeplayers:
            plrating = {'team': 'home'}
            href = pl.xpath('a/@href').extract_first().strip()
            plrating['read_player'] = re.match(href_pattern, href).group(1).replace('-', ' ')
            for mark in pl.xpath('a/span[@class="numero"]/text()').extract():
                if mark != '-':
                    plrating['rating'] = mark
            #result.append(plrating)
        for pl in awayplayers:
            plrating = {'team': 'away'}
            href = pl.xpath('a/@href').extract_first().strip()
            plrating['read_player'] = re.match(href_pattern, href).group(1).replace('-', ' ')
            for mark in pl.xpath('a/span[@class="numero"]/text()').extract():
                if mark != '-':
                    plrating['rating'] = mark
            #result.append(plrating)
        yield loader.load_item()

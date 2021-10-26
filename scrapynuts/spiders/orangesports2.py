# -*- coding: utf-8 -*-
import re
import hashlib

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from lxml import html
from unidecode import unidecode
from pytz import timezone
import dateparser

from .. import items


class Orangesports2Spider(CrawlSpider):
    name = 'orangesports2'
    allowed_domains = ['sports.orange.fr']
    start_urls = [
        'https://sports.orange.fr/football/ligue-1/calendrier-resultats.html', ]

    rules = (
        Rule(LinkExtractor(allow='football/ligue-1/match/[\w|-]+-apres-match-\w+\.html$', unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath(
            '//time[@itemprop="startDate"]/@content').extract_first()
        try:
            dt = dateparser.parse(md, languages=['fr'])
            paristz = timezone('Europe/Paris')
            loc_dt = paristz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        step_txt = response.xpath(
            '//span[@class="day"]/text()').extract_first()
        loader.add_value('step', re.search(
            u'(\d+)\D+ journ', step_txt).group(1))
        loader.add_value('hash_url', hashlib.md5(
            response.url.encode('utf-8')).hexdigest())
        loader.add_value('source', 'ORS')
        loader.add_value('match_date', game_date)
        loader.add_xpath(
            'home_team', '//div[@class="team" and @itemprop="homeTeam"]/@title')
        loader.add_xpath(
            'away_team', '//div[@class="team" and @itemprop="awayTeam"]/@title')
        loader.add_xpath(
            'home_score', '//div[@class="home-team"]//div[@class="score"]/text()')
        loader.add_xpath(
            'away_score', '//div[@class="guest-team"]//div[@class="score"]/text()')

        debrief_par_text = \
            html.fromstring(response.text).xpath('string(//div[@itemprop="articleBody"])').split(
                'La feuille de match', 1)[1]

        notes_zone_pattern = r'(\b[\s\w\.]+(?:\(cap\))?\s\([^()]*?\d\).*?N\'ont pas particip)'
        matches = re.findall(notes_zone_pattern, unidecode(debrief_par_text))
        loader.add_value('players_home', self.get_player(matches[0]))
        loader.add_value('players_away', self.get_player(matches[1]))
        yield loader.load_item()

    def get_player(self, zone):
        name_and_note_pattern = r'\b([\s\w\'\.\-]+)(?:\(cap\))?\s\([^()]*?(\d)\)'
        matches = re.findall(name_and_note_pattern, zone)
        for name, note in matches:
            loader = items.PlayerItemLoader()
            loader.add_value('name', unidecode(name.strip()))
            loader.add_value('rating', note)
            yield dict(loader.load_item())

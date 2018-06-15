# -*- coding: utf-8 -*-
import re
import json

from pytz import timezone
import dateparser
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from .. import items
import hashlib


def convert_to_json_link(match_link):
    # extract id from url
    match_id = re.search(u'fbl_match-([\d]+)\/$', match_link)
    if match_id:
        return u'https://www.sport-express.ru/services/match/football/%s/online/se/?json=1' % match_id.group(1)
    else:
        return None


class SportexpressruSpider(CrawlSpider):
    name = 'sportexpressru'
    allowed_domains = ['sport-express.ru']
    start_urls = ['https://www.sport-express.ru/football/L/world/calendar/']

    rules = (
        Rule(LinkExtractor(restrict_xpaths='//td[@class="fifa-table__td fifa-table__td-score"]/a',
                           process_value=convert_to_json_link),
             callback='parse_match',
             process_links='with_score_only'),
    )

    def with_score_only(self, links):
        for link in links:
            if '- : -' in link.text:
                continue
            yield link

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        json_data = json.loads(response.text)
        if json_data['status'] < 1:
            return
        loader = items.MatchItemLoader(items.MatchItem(), response=response)
        try:
            dt = dateparser.parse(json_data['date'])
            moscowtz = timezone('Europe/Moscow')
            loc_dt = moscowtz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'SPEX')
        loader.add_value('match_date', game_date)
        loader.add_value('home_team',
                         json_data['homeCommand']['name'])
        loader.add_value('away_team',
                         json_data['guestCommand']['name'])
        loader.add_value('home_score',
                         json_data['homeScore'])
        loader.add_value('away_score',
                         json_data['guestScore'])
        for pl in json_data['homeCommand']['players']:
            loader.add_value('players_home', self.get_player(pl))
        for pl in json_data['guestCommand']['players']:
            loader.add_value('players_away', self.get_player(pl))
        yield loader.load_item()

    def get_player(self, pl):
        try:
            loader = items.PlayerItemLoader()
            loader.add_value('name', pl['name'])
            loader.add_value('rating', pl['info']['seEstimation'])
            yield dict(loader.load_item())
        except KeyError:
            pass
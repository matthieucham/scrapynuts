# -*- coding: utf-8 -*-
import hashlib
import re
import json

from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request, HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.link import Link
from pytz import timezone
import dateparser
from unidecode import unidecode
from datetime import datetime
import pytz

from .. import items


class FFTimelineLinkExtractor:
    def __init__(self, searched_term=None):
        self.searched_term = searched_term

    def extract_links(self, response):
        try:
            json_timeline = json.loads(response.text)
            for it in json_timeline['items']:
                if self.searched_term in it['titre']:
                    yield it['fullUrl']
        except ValueError:
            pass


class FrancefootballSpider(CrawlSpider):
    name = 'francefootball'
    allowed_domains = ['francefootball.fr']
    start_urls = [
        'https://www.francefootball.fr/generated/json/timeline/page-1.json',
        'https://www.francefootball.fr/generated/json/timeline/page-2.json',
        'https://www.francefootball.fr/generated/json/timeline/page-3.json',
        'https://www.francefootball.fr/generated/json/timeline/page-4.json',
        'https://www.francefootball.fr/generated/json/timeline/page-5.json',
        'https://www.francefootball.fr/generated/json/timeline/page-6.json',
        'https://www.francefootball.fr/generated/json/timeline/page-7.json',
        'https://www.francefootball.fr/generated/json/timeline/page-8.json',
        'https://www.francefootball.fr/generated/json/timeline/page-9.json',
        'https://www.francefootball.fr/generated/json/timeline/page-10.json',
    ]

    rules = (
        Rule(FFTimelineLinkExtractor(searched_term=u'notes'),
             follow=True,
             callback='parse_match'),
    )

    def _requests_to_follow(self, response):
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = Request(url=link.url if isinstance(link, Link) else link, callback=self._response_downloaded)
                r.meta.update(rule=n, link_text=link.text if isinstance(link, Link) else link)
                yield rule.process_request(r)

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath(
            '//div[contains(@class, "js-analytics-timestamp")]/@data-timestamp'
        ).extract_first()
        utc_dt = pytz.utc.localize(datetime.utcfromtimestamp(int(md)))
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'FF')
        loader.add_value('match_date', utc_dt.isoformat())
        loader.add_xpath('home_team',
                         '(//h2[contains(text(),"notes")])[1]/text()')
        loader.add_xpath('away_team',
                         '(//h2[contains(text(),"notes")])[2]/text()')
        homeplayers = response.xpath(
            '(//h2[contains(text(),"notes")])[1]/following-sibling::div[@class="paragraph"][1]/div')
        for pl in homeplayers:
            loader.add_value('players_home', self.get_player(pl))
        awayplayers = response.xpath(
            '(//h2[contains(text(),"notes")])[2]/following-sibling::div[@class="paragraph"][1]/div')
        for pl in awayplayers:
            loader.add_value('players_away', self.get_player(pl))
        yield loader.load_item()

    def get_player(self, pl):
        loader = items.PlayerItemLoader()
        name = pl.xpath('text()').extract_first().strip()
        if name.startswith('Arbitre') or name.startswith('Note d') or len(name) > 50 or len(name) == 0:
            pass
        else:
            loader.add_value('name', unidecode(name))
            rating = pl.xpath('span/text()').extract_first()
            try:
                float(rating)
                loader.add_value('rating', rating)
                yield dict(loader.load_item())
            except ValueError:
                pass
            except TypeError:
                pass

# -*- coding: utf-8 -*-
import re

from pytz import timezone
import dateparser
from unidecode import unidecode
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from .. import items
import hashlib


class MadeinfootSpider(CrawlSpider):
    name = 'madeinfoot'
    allowed_domains = ['madeinfoot.com']
    start_urls = ['http://www.madeinfoot.com/ligue-1/calendrier-resultats.php']

    rules = (
        Rule(LinkExtractor(allow='/live/apres-match-ligue-1',
                           restrict_xpaths='//section[@id="une"]//ul[contains(@class, "calendrier")]')),
        Rule(LinkExtractor(allow='infos/article-l1',
                           restrict_xpaths='//section[@id="live"]'), callback='parse_match')
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)

        loader = items.MatchItemLoader(items.MatchItem(), response=response)
        md = response.xpath(
            '//time[@itemprop="datePublished"]/@content').extract_first().strip()
        dt = dateparser.parse(md)
        paristz = timezone('Europe/Paris')
        loc_dt = paristz.localize(dt)
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'MIF')
        loader.add_value('match_date', loc_dt.isoformat())
        efttd = response.xpath(
            '//div[@class="entete_fiche_technique"]/table/tbody/tr/td'
        )
        loader.add_value('home_team', efttd[0].xpath('string()').extract_first().strip())
        loader.add_value('away_team', efttd[2].xpath('string()').extract_first().strip())
        score = efttd[1].xpath('strong/text()').extract_first().split('-')
        loader.add_value('home_score', "%d" % int(score[0].strip()))
        loader.add_value('away_score', "%d" % int(score[1].strip()))

        for ah, tdidx in (('players_home', 1), ('players_away', 2)):
            for plspan in response.xpath(
                    '//div[@class="footer_fiche_technique"]/table[%d]/tbody/tr/td[2]/span' % tdidx):
                loader.add_value(ah, self.get_player(plspan))
        print loader.load_item()
        yield loader.load_item()

    def get_player(self, pl):
        loader = items.PlayerItemLoader()
        loader.add_value('name', unidecode(pl.xpath('text()').extract_first().strip()))
        try:
            mark = pl.xpath('span/text()').extract_first().strip().replace(',', '.')
            float(mark)
            loader.add_value('rating', mark)
            yield dict(loader.load_item())
        except Exception:
            pass

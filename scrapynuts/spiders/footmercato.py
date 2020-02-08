# -*- coding: utf-8 -*-
import hashlib
import re

from scrapy.spiders import CrawlSpider, Rule
from pytz import timezone
import dateparser
from unidecode import unidecode

from .. import items
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor


class FootmercatoSpider(CrawlSpider):
    name = 'footmercato'
    allowed_domains = ['footmercato.net']
    start_urls = ['http://www.footmercato.net/ligue-1/',]

    rules = (
        Rule(LxmlLinkExtractor(restrict_xpaths='//section[@class="main"]',
                               restrict_text=u'notes du match', unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath(
            '//article[@role="article"]//p[@class="article-date"]/time[@itemprop="datePublished"]/@datetime').extract_first()
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'FMERC')
        loader.add_value('match_date', md)

        crh3s = response.xpath('//article[@role="article"]//div[@itemprop="articleBody"]//h3[@class="spip"]')
        team_regex = r'(.*)\s+:$'
        hteam = None
        ateam = None
        hplset = set()
        aplset = set()
        for headline in crh3s:
            htxt = headline.xpath('text()').extract_first().replace(u'\xa0', u' ')
            m = re.match(team_regex, htxt)
            if m:
                if hteam is None:
                    hteam = m.group(1)
                    hps = headline.xpath('following-sibling::p/strong/text()').extract()
                    for hp in hps:
                        pl = self.get_player(hp)
                        if pl:
                            hplset.add(pl)
                else:
                    ateam = m.group(1)
                    aps = headline.xpath('following-sibling::p/strong/text()').extract()
                    for ap in aps:
                        pl = self.get_player(ap)
                        if pl:
                            aplset.add(pl)

        # hplset contient les joueurs des deux équipes: retirer aplset permet de ne conserver que les joueurs  h:
        hplset = hplset - aplset
        loader.add_value('home_team', hteam)
        loader.add_value('away_team', ateam)
        for n, r in hplset:
            loader.add_value('players_home', {'name': n, 'rating': r})
        for n, r in aplset:
            loader.add_value('players_away', {'name': n, 'rating': r})
        yield loader.load_item()

    def get_player(self, pl):
        matched = re.match(r'(.+)\s\(([\d,]+)\)\s*:?\s*$', pl.replace(u'\xa0', u' '))
        if matched:
            return unidecode(matched.group(1).strip()), matched.group(2).replace(',', '.')

# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from pytz import timezone
import dateparser
import hashlib
import re
from unidecode import unidecode
from .. import items

from utils import RestrictTextLinkExtractor


class MaxifootSpider(CrawlSpider):
    name = 'maxifoot'
    allowed_domains = ['maxifoot.fr']
    start_urls = ['http://www.maxifoot.fr/foot-matchs_ligue1-1.htm', 'http://www.maxifoot.fr/foot-matchs_ligue1-2.htm']

    rules = (
        Rule(RestrictTextLinkExtractor(allow=('football/article',),
                                       restrict_xpaths='//div[@id="main"]',
                                       link_text_regex=u'NOTES des joueurs \(', unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath('//article/header/div[@class="art_aut"]/span/b/text()').extract_first()
        try:
            dt = dateparser.parse(md, languages=['fr'])
            paristz = timezone('Europe/Paris')
            loc_dt = paristz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        fiche = response.xpath('//article//p[@class="fichtech"]')
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'MAXI')
        loader.add_value('match_date', game_date)
        home = fiche.xpath('b/a[1]/text()').extract_first()
        away = fiche.xpath('b/a[2]/text()').extract_first()
        loader.add_value('home_team', home)
        loader.add_value('away_team', away)
        score = re.search(u'(\d+)-(\d+)', fiche.xpath('b/text()').extract_first())
        loader.add_value('home_score', score.group(1))
        loader.add_value('away_score', score.group(2))

        notes_section = response.xpath('//article/div/p[@class="titcha"]')
        ref_text = notes_section.xpath('following-sibling::p[@class="titpar"]/u/text()').extract()
        if len(ref_text) == 2:
            notes_home = notes_section.xpath(
                'following-sibling::p/a[@class="jou1" and parent::p/preceding-sibling::p[@class="titpar"][1]/u/text()="%s"]/text()' %
                ref_text[0]).extract()
            notes_away = notes_section.xpath(
                'following-sibling::p/a[@class="jou1" and parent::p/preceding-sibling::p[@class="titpar"][1]/u/text()="%s"]/text()' %
                ref_text[1]).extract()

            for pl in notes_home:
                loader.add_value('players_home', self.get_player(unidecode(pl)))
            for pl in notes_away:
                loader.add_value('players_away', self.get_player(unidecode(pl)))
        yield loader.load_item()

    def get_player(self, pl):
        matched = re.match(u'(.+) \(([\d,]+)\)$', pl)
        if matched:
            loader = items.PlayerItemLoader()
            loader.add_value('name', matched.group(1).strip())
            loader.add_value('rating', matched.group(2).replace(',', '.'))
            yield dict(loader.load_item())
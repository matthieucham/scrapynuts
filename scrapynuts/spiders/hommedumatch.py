# -*- coding: utf-8 -*-
import hashlib
import re

from scrapy.spiders import CrawlSpider, Rule
import unidecode
import dateparser
from pytz import timezone

from utils import RestrictTextLinkExtractor

from .. import items


class HommedumatchSpider(CrawlSpider):
    name = 'hommedumatch'
    allowed_domains = ['hommedumatch.fr']
    start_urls = ['http://www.hommedumatch.fr/articles/france', 'http://www.hommedumatch.fr/articles/france/page/2']

    rules = (
        Rule(RestrictTextLinkExtractor(allow=('ligue\-1',), link_text_regex=u'Ligue 1.+Les notes de',
                                       unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'HDM')
        title = unidecode.unidecode(response.xpath('//article/header/h1/text()').extract_first())
        title_matched = re.match(
            u'Ligue 1 \W (\d+)\D+ Les notes de ([\w|\-| ]+)\s*\W\s*([\w|\-| ]+) \((\d+)\s*\W\s*(\d+)\)$',
            title)
        loader.add_value('home_team', title_matched.group(2).strip())
        loader.add_value('away_team', title_matched.group(3).strip())
        loader.add_value('home_score', title_matched.group(4).strip())
        loader.add_value('away_score', title_matched.group(5).strip())
        loader.add_value('step', title_matched.group(1))
        md = response.xpath('//time/text()').extract_first()
        try:
            dt = dateparser.parse(md, languages=['fr'])
            paristz = timezone('Europe/Paris')
            loc_dt = paristz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        loader.add_value('match_date', game_date)
        players_nodes = response.xpath(
            '//article/div[@class="td-post-text-content"]/p/*[self::strong or self::b]')
        homeplayers = []
        awayplayers = []
        pl_with_note_pattern = r'\b[\s\w\'\.\-]+\s\([\d,\.]{1,3}\)'
        next_is_home = False
        next_is_away = False
        for pn in players_nodes:
            if pn.xpath('./text()').extract_first().startswith('Homme du match'):
                continue
            if len(pn.xpath('./parent::p/@style').extract()) > 0:
                if next_is_home:
                    next_is_away = True
                    next_is_home = False
                else:
                    next_is_home = True
                    next_is_away = False
            else:
                if next_is_home:
                    homeplayers.append(pn.xpath('./text()').extract_first())
                elif next_is_away:
                    awayplayers.append(pn.xpath('./text()').extract_first())
        for pl in homeplayers:
            loader.add_value('players_home', self.get_player(unidecode.unidecode(pl)))
        for pl in awayplayers:
            loader.add_value('players_away', self.get_player(unidecode.unidecode(pl)))

        yield loader.load_item()

    def get_player(self, pl):
        strong_pattern = u'([\w|\-| ]+)\(([\d|,|\.]+)\)'
        matched = re.search(strong_pattern, pl)
        if matched:
            loader = items.PlayerItemLoader()
            loader.add_value('name', matched.group(1).strip())
            loader.add_value('rating', matched.group(2).strip().replace(',', '.'))
            yield dict(loader.load_item())

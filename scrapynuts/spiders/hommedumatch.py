# -*- coding: utf-8 -*-
import hashlib
import re

from scrapy.spiders import CrawlSpider, Rule
import unidecode
import dateparser
from pytz import timezone

from scrapy.linkextractors import LinkExtractor

from .. import items


class HommedumatchSpider(CrawlSpider):
    name = 'hommedumatch'
    allowed_domains = ['hommedumatch.fr']
    start_urls = ['http://www.hommedumatch.fr/articles/france',
                  'http://www.hommedumatch.fr/articles/france/page/2']

    rules = (
        Rule(LinkExtractor(allow=('ligue\-1',), restrict_text=u'Ligue 1.+Les notes d',
                           unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        loader.add_value('hash_url', hashlib.md5(
            response.url.encode('utf-8')).hexdigest())
        loader.add_value('source', 'HDM')
        title = unidecode.unidecode(response.xpath(
            '//article//h1/text()').extract_first())
        title_matched = re.match(
            u'Ligue 1 \W (\d+)\D+ Les notes d.\s?([\w|\-| ]+)\s*\W\s*([\w|\-| ]+) \(\s*(\d+)\s*\W\s*(\d+)\s*\)$',
            title)
        loader.add_value('home_team', title_matched.group(2).strip())
        loader.add_value('away_team', title_matched.group(3).strip())
        loader.add_value('home_score', title_matched.group(4).strip())
        loader.add_value('away_score', title_matched.group(5).strip())
        loader.add_value('step', title_matched.group(1))
        # md = response.xpath('//time/text()').extract_first()
        md = response.xpath(
            '/html/head/meta[@property="article:published_time"]/@content').extract_first()
        game_date = md
        # try:
        #     dt = dateparser.parse(md, languages=['fr', 'en'])
        #     paristz = timezone('Europe/Paris')
        #     loc_dt = paristz.localize(dt)
        #     game_date = loc_dt.isoformat()
        # except ValueError:
        #     game_date = None
        loader.add_value('match_date', game_date)
        players_nodes = response.xpath(
            '//article/div[@class="entry-content entry clearfix"]//p/*[self::strong or self::b]')
        homeplayers = []
        awayplayers = []
        pl_with_note_pattern = r'\b[\s\w\'\.\-]+\s\([\d,\.]{1,3}\)'
        next_is_home = False
        next_is_away = False
        for pn in players_nodes:
            try:
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
                        homeplayers.append(
                            pn.xpath('./text()').extract_first())
                    elif next_is_away:
                        awayplayers.append(
                            pn.xpath('./text()').extract_first())
            except AttributeError:
                pass  # skip player_node if any parsing problem
        for pl in homeplayers:
            loader.add_value('players_home', self.get_player(
                unidecode.unidecode(pl)))
        for pl in awayplayers:
            loader.add_value('players_away', self.get_player(
                unidecode.unidecode(pl)))

        yield loader.load_item()

    def get_player(self, pl):
        strong_pattern = u'([\w|\-| ]+)\(([\d|,|\.]+)\)'
        matched = re.search(strong_pattern, pl)
        if matched:
            name = matched.group(1).strip()
            rating = matched.group(2).strip().replace(',', '.')
            if name and rating:
                loader = items.PlayerItemLoader()
                loader.add_value('name', name)
                loader.add_value('rating', rating)
                yield dict(loader.load_item())

# -*- coding: utf-8 -*-
import hashlib
import re

from scrapy.spiders import CrawlSpider, Rule
from pytz import timezone
import dateparser
from unidecode import unidecode

from .. import items
from scrapy.linkextractors import LinkExtractor


class MaxifootSpider(CrawlSpider):
    name = 'maxifoot'
    allowed_domains = ['maxifoot.fr']
    start_urls = ['http://www.maxifoot.fr/foot-matchs_ligue1-1.htm',
                  'http://www.maxifoot.fr/foot-matchs_ligue1-2.htm']

    rules = (
        Rule(LinkExtractor(allow=('football/article',),
                           restrict_xpaths='//div[@id="main"]',
                           restrict_text=u'NOTES des joueurs \(', unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath(
            '//article/header/div[@class="art_aut"]/span/b/text()').extract_first()
        try:
            dt = dateparser.parse(md, languages=['fr'])
            paristz = timezone('Europe/Paris')
            loc_dt = paristz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        fiche = response.xpath('//article//p[@class="fichtech"]')
        loader.add_value('hash_url', hashlib.md5(
            response.url.encode('utf-8')).hexdigest())
        loader.add_value('source', 'MAXI')
        loader.add_value('match_date', game_date)
        summ = fiche.xpath('text()').extract_first()
        summ_matched = re.match(
            r'([\w|\-| ]+)(\d{1,2})\s*\-\s*(\d{1,2})([\w|\-| ]+)\(mi\-t.*Ligue 1.*(\d{1,2}).*journ.*$', summ, re.IGNORECASE)
        if (summ_matched):
            # WELL FORMED fiche technique
            loader.add_value('home_team', unidecode(
                summ_matched.group(1).strip()))
            loader.add_value('away_team', unidecode(
                summ_matched.group(4).strip()))
            loader.add_value('home_score', summ_matched.group(2).strip())
            loader.add_value('away_score', summ_matched.group(3).strip())
            loader.add_value('step', summ_matched.group(5))
        else:
            # DIFFERENT APPROACH:
            title = response.xpath(
                '//article/header/h1/text()').extract_first()
            title_matched = re.match(
                r'.*\(([\w|\-| ]+)(\d{1,2})\s*\-\s*(\d{1,2})([\w|\-| ]+)\)', title, re.IGNORECASE
            )
            if title_matched:
                loader.add_value('home_team', unidecode(
                    title_matched.group(1).strip()))
                loader.add_value('away_team', unidecode(
                    title_matched.group(4).strip()))
                loader.add_value('home_score', title_matched.group(2).strip())
                loader.add_value('away_score', title_matched.group(3).strip())

        # home = fiche.xpath('b/a[1]/text()').extract_first()
        # away = fiche.xpath('b/a[2]/text()').extract_first()
        # step_txt = fiche.xpath('b[2]/text()').extract_first()
        # loader.add_value('step', re.search(u'(\d+)\w+ journ', step_txt).group(1))
        # loader.add_value('home_team', unidecode(home))
        # loader.add_value('away_team', unidecode(away))
        # score = re.search(u'(\d+)-(\d+)', fiche.xpath('b/text()').extract_first())
        # loader.add_value('home_score', score.group(1))
        # loader.add_value('away_score', score.group(2))

        notes_section = response.xpath('//article/div/p[@class="titcha"]')
        titpar_ok = False
        titcha_mode = False
        if len(notes_section.extract()) > 2:
            # mode où titcha est aussi la classe des noms des clubs dans la fiche
            titres = notes_section.xpath('text()').extract()
            ref_text = [titres[1], titres[2]]
            titcha_mode = True
        else:
            ref_text = notes_section.xpath(
                'following-sibling::p[@class="titpar"]/u/text()').extract()
            titpar_ok = True
        if not ref_text:
            # Si jamais la class titpar n'est pas sur le nom des équipes, on se repère quand même par le u
            ref_text = notes_section.xpath(
                'following-sibling::p[@class="par"]//u//text()').extract()
            titpar_ok = False
        if len(ref_text) == 2:
            if titpar_ok:
                def xpath_maker(x): return (
                    'following-sibling::p[@class="par"]/b[parent::p/preceding-sibling::p[@class="titpar"][1]/u/text()="%s"]/text()' % x)
                notes_home = notes_section.xpath(
                    xpath_maker(ref_text[0])).extract()
                notes_away = notes_section.xpath(
                    xpath_maker(ref_text[1])).extract()
            elif titcha_mode:
                def xpath_maker(x): return (
                    'following-sibling::p[@class="par"]/b[parent::p/preceding-sibling::p[@class="titcha"][1]/text()="%s"]/text()' % x)
                notes_home = notes_section.xpath(
                    xpath_maker(ref_text[0])).extract()
                notes_away = notes_section.xpath(
                    xpath_maker(ref_text[1])).extract()
            else:
                def xpath_maker(x): return (
                    'following-sibling::p[@class="par"]/b[parent::p/preceding-sibling::p[@class="par"]//u//text()="%s"]/text()' % x)
                notes_home_big = notes_section.xpath(
                    xpath_maker(ref_text[0])).extract()
                notes_away = notes_section.xpath(
                    xpath_maker(ref_text[1])).extract()
                notes_home = [x for x in notes_home_big if x not in notes_away]
            for pl in notes_home:
                loader.add_value(
                    'players_home', self.get_player(unidecode(pl)))
            for pl in notes_away:
                loader.add_value(
                    'players_away', self.get_player(unidecode(pl)))
        yield loader.load_item()

    def get_player(self, pl):
        matched = re.match(u'(.+) \(([\d,]+)\)$', pl)
        if matched:
            loader = items.PlayerItemLoader()
            loader.add_value('name', unidecode(matched.group(1).strip()))
            loader.add_value('rating', matched.group(2).replace(',', '.'))
            yield dict(loader.load_item())

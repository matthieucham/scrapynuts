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


class OrangesportsSpider(CrawlSpider):
    name = 'orangesports'
    allowed_domains = ['sports.orange.fr']
    start_urls = ['https://sports.orange.fr/football/ligue-1/calendrier-resultats.html']

    rules = (
        Rule(LinkExtractor(allow='football/ligue-1/match/[\w|-]+-apres-match-\w+\.html$', unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath('//time[@itemprop="startDate"]/@content').extract_first()
        try:
            dt = dateparser.parse(md, languages=['fr'])
            paristz = timezone('Europe/Paris')
            loc_dt = paristz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        step_txt = response.xpath('//span[@class="day"]/text()').extract_first()
        loader.add_value('step', re.search(u'(\d+)\D+ journ', step_txt).group(1))
        loader.add_value('hash_url', hashlib.md5(response.url).hexdigest())
        loader.add_value('source', 'ORS')
        loader.add_value('match_date', game_date)
        loader.add_xpath('home_team', '//div[@class="team" and @itemprop="homeTeam"]/@title')
        loader.add_xpath('away_team', '//div[@class="team" and @itemprop="awayTeam"]/@title')
        loader.add_xpath('home_score', '//div[@class="home-team"]//div[@class="score"]/text()')
        loader.add_xpath('away_score', '//div[@class="guest-team"]//div[@class="score"]/text()')

        strong_in_article = html.fromstring(response.text).xpath('//div[@itemprop="articleBody"]//strong')

        next_is_home = False
        next_is_away = False
        home_pars = []
        homep_to_search = None
        away_pars = []
        awayp_to_search = None
        next_par_maybe_home = ['Avert', 'Expu', 'Exclu', 'But']
        for par in strong_in_article:
            if par.text is not None and any(par.text.startswith(maybe) for maybe in next_par_maybe_home):
                next_is_home = True
            elif next_is_home:
                if par.text is not None and not any(par.text.startswith(maybe) for maybe in next_par_maybe_home):
                    home_pars.append(self.get_first_br_with_tail(par))
                    homep_to_search = par.xpath('following-sibling::strong')
                    next_is_home = False
            elif par.text is not None and (
                    unidecode(par.text).startswith('Entraineur') or unidecode(par.text).startswith(
                'Selectionneur')) and awayp_to_search is None:
                next_is_away = True
            elif next_is_away:
                away_pars.append(self.get_first_br_with_tail(par))
                awayp_to_search = par.xpath('following-sibling::strong')
                next_is_away = False
        loader.add_value('players_home', self.get_player(home_pars, homep_to_search))
        loader.add_value('players_away', self.get_player(away_pars, awayp_to_search))
        yield loader.load_item()

    def get_player(self, pars, p_to_search):
        name_pattern_1 = u'(?:puis )*([\w\.\'][\w\.\'|àéèäëâêiîïöôûüùñç\- ]+)[\s]*(?:\(cap\))*[\s]*\((?:[\d]+[^,\-]+(?:\-[\s])*)*$'
        name_pattern = re.compile(name_pattern_1, re.UNICODE)
        if p_to_search is None:
            return
        # select relevant pars
        for par in p_to_search:
            if par.text is not None:
                if unidecode(par.text).startswith('N\'ont pas participe') or unidecode(par.text).startswith(
                        'Entraineur') or unidecode(par.text).startswith('Selectionneur'):
                    break
                else:
                    pars.append(par)
        previous_tail = None
        ignore_next = False
        for blabla in pars:
            content = blabla.text
            if content is not None:
                if content.startswith('Arbitre'):
                    ignore_next = True
                if len(content) == 1 and content.isdigit:
                    matched = re.search(name_pattern, unidecode(previous_tail))
                    if matched is not None:
                        if ignore_next:
                            ignore_next = False
                        else:
                            loader = items.PlayerItemLoader()
                            loader.add_value('name', unidecode(matched.group(1).strip()))
                            loader.add_value('rating', content)
                            yield dict(loader.load_item())
            previous_tail = blabla.tail

    def get_first_br_with_tail(self, par):
        p = None
        xpath_index = 1
        while p is None or p.tail is None:
            try:
                p = par.xpath('following-sibling::br[%s]' % xpath_index)[0]
                xpath_index += 1
            except IndexError:
                return par  # new format: return the containing paragraph itself.
        return p

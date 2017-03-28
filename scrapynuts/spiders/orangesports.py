# -*- coding: utf-8 -*-
import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from .. import items


class OrangesportsSpider(CrawlSpider):
    name = 'orangesports'
    allowed_domains = ['sports.orange.fr']
    start_urls = ['http://sports.orange.fr/football/ligue-1/calendrier-resultats.html']

    rules = (
        Rule(LinkExtractor(allow='football/ligue-1/match/\w+-\w+-apres-match-\w+\.html$', unique=True),
             callback='parse_match'),
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        loader.add_xpath('match_date', '//time[@itemprop="startDate"]/@content')
        loader.add_xpath('home_team', '//div[@class="team" and @itemprop="homeTeam"]/@title')
        loader.add_xpath('away_team', '//div[@class="team" and @itemprop="awayTeam"]/@title')
        loader.add_xpath('home_score', '//div[@class="home-team"]//div[@class="score"]/text()')
        loader.add_xpath('away_score', '//div[@class="guest-team"]//div[@class="score"]/text()')

        strong_in_article = response.xpath('//div[@itemprop="articleBody"]/p//strong/text()')

        next_is_home = False
        next_is_away = False
        home_pars = []
        homep_to_search = None
        away_pars = []
        awayp_to_search = None
        for par in strong_in_article:
            if par.extract() is not None and par.extract().startswith('Avert'):
                next_is_home = True
            elif next_is_home:
                if par.extract().startswith('Expu') or par.extract().startswith('Exclu'):
                    next_is_home = True
                else:
                    home_pars.append(self.get_first_br_with_tail(par))
                    homep_to_search = par.xpath('following-sibling::strong')
                    next_is_home = False
            elif par.extract() is not None and par.extract().startswith('Entra') and awayp_to_search is None:
                next_is_away = True
            elif next_is_away:
                away_pars.append(self.get_first_br_with_tail(par))
                awayp_to_search = par.xpath('following-sibling::strong')
                next_is_away = False
        loader.add_value('players_home', self.get_player(homep_to_search))
        loader.add_value('players_away', self.get_player(awayp_to_search))
        yield loader.load_item()

    def get_player(self, p_to_search):
        name_pattern = r'(?:puis )*([\w\.\'][\w\.\'|àéèäëâêiîïöôûüù\- ]+)[\s]*(?:\(cap\))*[\s]*\((?:[\d]+[^,\-]+(?:\-[\s])*)*$'
        if p_to_search is None:
            return
        # select relevant pars
        pars = []
        for par in p_to_search:
            if par.text is not None:
                if par.text.startswith('N\'ont pas partici') or par.text.startswith('Entra'):
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
                    matched = re.search(name_pattern, previous_tail)
                    if matched is not None:
                        if ignore_next:
                            ignore_next = False
                        else:
                            loader = items.PlayerItemLoader()
                            loader.add_value('name', matched.group(1).strip())
                            loader.add_value('rating', content)
                            yield dict(loader.load_item())
            previous_tail = blabla.tail

    def get_first_br_with_tail(self, par):
        p = None
        xpath_index = 1
        while p is None or len(p) > 0:
            p = par.xpath('following-sibling::br[%s]' % xpath_index)
            xpath_index += 1
        return p
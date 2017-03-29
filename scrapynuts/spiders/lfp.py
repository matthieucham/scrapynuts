# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, Request
from .. import items


class LfpSpider(CrawlSpider):
    name = 'lfp'
    allowed_domains = ['lfp.fr']

    rules = (
        Rule(LinkExtractor(allow='ligue1\/feuille_match\/\w{4,}'), callback='parse_match',
             process_request='add_meta_selenium'),
    )

    def start_requests(self):
        req = Request('http://www.lfp.fr/competitionPluginCalendrierResultat/changeCalendrierHomeJournee?c=ligue1&js=30&id=0',
                      dont_filter=True)
        req.meta.update(selenium=True)
        return [req]

    def add_meta_selenium(self, request):
        request.meta.update(selenium=True)
        return request

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        loader.add_xpath('home_team',
                         '//div[@class="contenu_box match_stats"]/div[@class="score"]/div[@class="club_dom"]/span[contains(@class,"club")]/text()')
        loader.add_xpath('home_score',
                         '//div[@class="contenu_box match_stats"]/div[@class="score"]/div[@class="club_dom"]/span[contains(@class,"buts")]/text()')
        loader.add_xpath('away_team',
                         '//div[@class="contenu_box match_stats"]/div[@class="score"]/div[@class="club_ext"]/span[contains(@class,"club")]/text()')
        loader.add_xpath('away_score',
                         '//div[@class="contenu_box match_stats"]/div[@class="score"]/div[@class="club_ext"]/span[contains(@class,"buts")]/text()')
        md = response.xpath(
            '(//div[@class="contenu_box match_stats"]/h1/following-sibling::p)[2]/text()').extract_first().split(' - ')[
            0]
        loader.add_value('match_date', md)
        loader.add_value('players_home', self.get_player(response, 'dom'))
        loader.add_value('players_away', self.get_player(response, 'ext'))

        yield loader.load_item()

    def get_player(self, response, field):
        for player in response.xpath(
                        '//div[@id="bloc_infosMatch_data"]/h2[text()="Titulaires"]/following-sibling::div[contains(@class, "%s")][1]/ul/li/a' % field):
            loader = items.PlayerItemLoader()
            loader.add_value('name', player.xpath('@href').extract_first().strip()[len('/joueur/'):].replace('-', ' '))
            loader.add_value('stats', self.get_stats(player, response, field))
            yield dict(loader.load_item())

    def get_stats(self, player, response, field):
        min_pattern = r'\((\d{1,2})\'.*\)'
        loader = items.PlayerStatItemLoader()
        plclass = player.xpath('span[@class!="numero"]/@class').extract_first().strip()
        if len(plclass) == 0:
            loader.add_value('playtime', 90)
        elif plclass == 'entrant':
            read_minute_in = player.xpath('parent::li/text()').extract_first()
            minute_in = int(re.search(min_pattern, read_minute_in).group(1))
            if minute_in is not None:
                loader.add_value('playtime', max(90 - minute_in, 1))
        elif plclass == 'sortant':
            read_minute_out = player.xpath(
                'parent::li/following-sibling::li/a/span[contains(@class,"entrant")]/parent::a/parent::li/text()').extract_first()
            minute_out = int(re.search(min_pattern, read_minute_out).group(1))
            loader.add_value('playtime', minute_out)
        yield dict(loader.load_item())
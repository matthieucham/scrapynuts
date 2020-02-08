# -*- coding: utf-8 -*-
import re

from pytz import timezone
import dateparser
import unidecode
import hashlib
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, Request

from .. import items


class LfpSpider(CrawlSpider):
    name = 'lfp'
    allowed_domains = ['lfp.fr']

    rules = (
        Rule(LinkExtractor(allow='ligue1\/feuille_match\/\d{4,}$',
                           restrict_xpaths='//a[contains(@href,"feuille_match")]/parent::td[@class="stats"]/preceding-sibling::td[contains(@class,"horaire")]'),
             callback='parse_match'),
    )

    def start_requests(self):
        try:
            req = Request(
                'http://www.lfp.fr/competitionPluginCalendrierResultat/changeCalendrierHomeJournee?c=ligue1&js=%s&id=0' %
                self.journee,
                dont_filter=True)
        except AttributeError:
            req = Request('http://www.lfp.fr/ligue1/calendrier_resultat', dont_filter=True)
        return [req]

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)

        match_id = response.xpath('//input[@id="match_id_hidden"]/@value').extract_first()
        dom_id = response.xpath('//input[@id="dom_id_hidden"]/@value').extract_first()
        ext_id = response.xpath('//input[@id="ext_id_hidden"]/@value').extract_first()

        infos_match_url = response.urljoin('showInfosMatch?matchId=%s&domId=%s&extId=%s' % (match_id, dom_id, ext_id))
        infos_match_resp = yield Request(infos_match_url)

        stats_joueurs_url = response.urljoin(
            'showStatsJoueursMatch?matchId=%s&domId=%s&extId=%s' % (match_id, dom_id, ext_id))
        stats_joueurs_resp = yield Request(stats_joueurs_url)

        loader = items.MatchItemLoader(response=response)
        loader.add_value('hash_url', hashlib.md5(response.url.encode('utf-8')).hexdigest())
        loader.add_value('source', 'LFP')
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
                 0] + ' ' + response.meta.get('link_text').strip()
        try:
            dt = dateparser.parse(md, languages=['fr'])
            paristz = timezone('Europe/Paris')
            loc_dt = paristz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        loader.add_value('match_date', game_date)
        loader.add_value('players_home', self.get_player(response, infos_match_resp, stats_joueurs_resp, 'dom'))
        loader.add_value('players_away', self.get_player(response, infos_match_resp, stats_joueurs_resp, 'ext'))

        yield loader.load_item()

    def get_player(self, response, infos_match_resp, stats_joueurs_resp, field):
        name_pattern_1 = u'(\(c\))?([\w\.\'|àéèäëâêiîïöôûüù\-\s]+)(\(c\))?'
        name_pattern = re.compile(name_pattern_1, re.UNICODE)
        for player in infos_match_resp.xpath(
                        '//div[contains(@class, "%s")][1]/ul/li/a' % field):
            plref = player.xpath('@href').extract_first().strip()
            plread = player.xpath('span[@class!="numero"]/text()').extract_first()
            pldisplay = re.search(name_pattern, plread).group(2).strip()
            loader = items.PlayerItemLoader()
            loader.add_value('name', plref[len('/joueur/'):].replace('-', ' '))
            loader.add_value('stats',
                             self.get_stats(player, response, stats_joueurs_resp, plref,
                                            pldisplay))
            yield dict(loader.load_item())

    def get_stats(self, player, response, stats_joueurs_resp, plref, pldisplay):
        min_pattern = r'\((\d{1,2})\'.*\)'
        card_pattern = r'(\d{1,2})\'.*'
        loader = items.PlayerStatItemLoader()
        plclass = player.xpath('span[@class!="numero"]/@class').extract_first().strip()
        # playtime
        max_playtime = 90
        liredcard = response.xpath(
            '//div[@id="cartons"]//span[contains(@class,"icon_carton_rouge")]/following-sibling::a[@href="%s"]/parent::li' % plref)
        if len(liredcard) > 0:
            clean = unidecode.unidecode(''.join(liredcard.xpath('text()').extract()).strip())
            max_playtime = int(re.search(card_pattern, clean).group(1))
        if len(plclass) == 0:
            loader.add_value('playtime', max_playtime)
        elif plclass == 'entrant':
            read_minute_in = player.xpath('parent::li/text()').extract_first()
            minute_in = int(re.search(min_pattern, read_minute_in).group(1))
            if minute_in is not None:
                loader.add_value('playtime', max(max_playtime - minute_in, 1))
        elif plclass == 'sortant':
            read_minute_out = player.xpath(
                'parent::li/following-sibling::li/a/span[contains(@class,"entrant")]/parent::a/parent::li/text()').extract_first()
            minute_out = int(re.search(min_pattern, read_minute_out).group(1))
            loader.add_value('playtime', minute_out)
        # saves
        tdsaves = stats_joueurs_resp.xpath(
            '//table/caption[contains(text(), "Statistiques du gardien de but")]/parent::table[1]//td/a[@href="%s"]/parent::td' % plref)
        if len(tdsaves) > 0:
            loader.add_value('goals_saved', int(tdsaves.xpath('following-sibling::td[2]/text()').extract_first()) + int(
                tdsaves.xpath('following-sibling::td[3]/text()').extract_first()))
        # goals
        csc = 0
        goals = 0
        pen = 0
        for li in response.xpath(
                        '//div[@id="buts"]//span[contains(@class,"icon_but")]/following-sibling::a[@href="%s"]/parent::li' % plref):
            clean = unidecode.unidecode(''.join(li.xpath('text()').extract()).strip())
            if '(Pen)' in clean:
                pen += 1
            elif '(csc)' in clean:
                csc += 1
            else:
                goals += 1
        if csc > 0:
            loader.add_value('own_goals', csc)
        if pen > 0:
            loader.add_value('penalties_scored', pen)
        if goals > 0:
            loader.add_value('goals_scored', goals)
        # assists
        ass = 0
        for _ in response.xpath(
                        '//div[@id="buts"]//li/span[contains(@class,"passeur") and contains(text(), "%s")]' % pldisplay):
            ass += 1
        if ass > 0:
            loader.add_value('goals_assists', ass)
        yield dict(loader.load_item())
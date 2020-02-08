# -*- coding: utf-8 -*-
import re

from pytz import timezone
import dateparser
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from .. import items
import hashlib


class KickerdeSpider(CrawlSpider):
    name = 'kickerde'
    allowed_domains = ['kicker.de']
    start_urls = ['http://www.kicker.de/news/fussball/weltmeisterschaft/spiele/weltmeisterschaft/2018/spieltag.html',
                  'http://www.kicker.de/news/fussball/weltmeisterschaft/spiele/weltmeisterschaft/2018/1/0/spieltag.html',
                  ]

    rules = (
        Rule(LinkExtractor(allow='football/directs/ligue-1/', restrict_xpaths='//table[@class="nwResultats"]')),
        Rule(LinkExtractor(allow='spielanalyse_',
                           restrict_xpaths='//div[@id="begegnungen_maincont"]'), callback='parse_match')
    )

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)

        loader = items.MatchItemLoader(items.MatchItem(), response=response)
        md = response.xpath(
            '//div[@id="ctl00_PlaceHolderHalf_ctl03_anstoss"]/div[@class="wert"]/text()').extract_first().strip()
        try:
            dt = dateparser.parse(md, languages=['de'])
            berlintz = timezone('Europe/Berlin')
            loc_dt = berlintz.localize(dt)
            game_date = loc_dt.isoformat()
        except ValueError:
            game_date = None
        loader.add_value('hash_url', hashlib.md5(response.url).encode('utf-8').hexdigest())
        loader.add_value('source', 'KICK')
        loader.add_value('match_date', game_date)
        loader.add_xpath('home_team',
                         '(//tr[@id="SpielpaarungLiveTitleRow"]/td[@class="lttabvrnName"])[1]/h1/a/text()')
        loader.add_xpath('away_team',
                         '(//tr[@id="SpielpaarungLiveTitleRow"]/td[@class="lttabvrnName"])[2]/h1/a/text()')
        if response.xpath(
                '//div[contains(@class, "scoreboard")]//div[contains(@class,"ergBoardExtB")]/div[@class="halbzeitText"]/text()').extract_first().strip() == 'im Elfmeterschiessen':
            score = response.xpath(
                '//div[contains(@class, "scoreboard")]//div[contains(@class,"ergBoardExtB")]/div[@class="halbzeitValue"]/span[@class="verlVal"]/text()').extract_first().strip()
            grab_score_pattern = r"([\d]+)[\D]+([\d]+)"
            loader.add_value('home_score', re.search(grab_score_pattern, score).group(1))
            loader.add_value('away_score', re.search(grab_score_pattern, score).group(2))
        else:
            loader.add_xpath('home_score',
                             '//div[contains(@class, "scoreboard")]//div[@id="ovBoardExtMainH"]/text()')
            loader.add_xpath('away_score',
                             '//div[contains(@class, "scoreboard")]//div[@id="ovBoardExtMainA"]/text()')
        # field = response.xpath('//div[@class="stade"]')
        aufstellungen = response.xpath('//table[@summary="Vereinsliste"]')
        homeplayers = aufstellungen[0].xpath('//tr[@id="ctl00_PlaceHolderHalf_ctl00_heim2"]//div[@class="spielerdiv"]')
        homeplayers_remp = aufstellungen[0].xpath(
            '//tr[@id="ctl00_PlaceHolderHalf_ctl00_heim2"]//div[@id="ctl00_PlaceHolderHalf_ctl00_einwechslungenHeim"]/div/a')
        awayplayers = aufstellungen[0].xpath('//tr[@id="ctl00_PlaceHolderHalf_ctl00_auswaerts2"]//div['
                                             '@class="spielerdiv"]')
        awayplayers_remp = aufstellungen[0].xpath(
            '//tr[@id="ctl00_PlaceHolderHalf_ctl00_auswaerts2"]//div[@id="ctl00_PlaceHolderHalf_ctl00_einwechslungenAusw"]/div/a')
        for pl in homeplayers:
            loader.add_value('players_home', self.get_player(pl))
        for pl in homeplayers_remp:
            loader.add_value('players_home', self.get_remp(pl))
        for pl in awayplayers:
            loader.add_value('players_away', self.get_player(pl))
        for pl in awayplayers_remp:
            loader.add_value('players_away', self.get_remp(pl))
        yield loader.load_item()

    def get_player(self, pl):
        href_pattern = ".*/spieler_(.+).html$"
        mark_pattern = "^\(([0-9,]{1,3})\).*$"
        href = pl.xpath('a/@href').extract_first().strip()
        m = pl.xpath('text()').extract_first().strip()
        loader = items.PlayerItemLoader()
        loader.add_value('name', re.match(href_pattern, href).group(1).replace('-', ' '))
        mark = re.match(mark_pattern, m)
        if mark:
            try:
                mark = mark.group(1).replace(',', '.')
                float(mark)
                loader.add_value('rating', mark)
                yield dict(loader.load_item())
            except ValueError:
                pass

    def get_remp(self, pl):
        href_pattern = ".*/spieler_(.+).html$"
        mark_pattern = "^\(([0-9,]{1,3})\).*$"
        href = pl.xpath('@href').extract_first().strip()
        m = pl.xpath('following-sibling::text()[1]').extract_first()
        if not m:
            return
        loader = items.PlayerItemLoader()
        loader.add_value('name', re.match(href_pattern, href).group(1).replace('-', ' '))
        mark = re.match(mark_pattern, m.strip())
        if mark:
            try:
                mark = mark.group(1).replace(',', '.')
                float(mark)
                loader.add_value('rating', mark)
                yield dict(loader.load_item())
            except ValueError:
                pass

# -*- coding: utf-8 -*-
import hashlib
import re
import json

from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.link import Link
from unidecode import unidecode
from datetime import datetime
import pytz

from .. import items


class IdleLinkExtractor:
    def __init__(self, url):
        self.url = url

    def extract_links(self, response):
        yield self.url


class FFTimelineLinkExtractor:
    def __init__(self, searched_term=None):
        self.searched_terms = searched_term

    def extract_links(self, response):
        try:
            json_timeline = json.loads(response.text)
            for it in json_timeline['items']:
                for st in self.searched_terms:
                    if st in it['titre']:
                        yield it['fullUrl']
        except ValueError:
            pass


class FrancefootballSpider(CrawlSpider):
    name = 'francefootball'
    allowed_domains = ['francefootball.fr']
    start_urls = [
        'https://www.francefootball.fr/generated/json/timeline/page-1.json',
        'https://www.francefootball.fr/generated/json/timeline/page-2.json',
        'https://www.francefootball.fr/generated/json/timeline/page-3.json',
        'https://www.francefootball.fr/generated/json/timeline/page-4.json',
        'https://www.francefootball.fr/generated/json/timeline/page-5.json',
        'https://www.francefootball.fr/generated/json/timeline/page-6.json',
        'https://www.francefootball.fr/generated/json/timeline/page-7.json',
        'https://www.francefootball.fr/generated/json/timeline/page-8.json',
        'https://www.francefootball.fr/generated/json/timeline/page-9.json',
        'https://www.francefootball.fr/generated/json/timeline/page-10.json',
        'https://www.francefootball.fr/generated/json/timeline/page-11.json',
        'https://www.francefootball.fr/generated/json/timeline/page-12.json',
        'https://www.francefootball.fr/generated/json/timeline/page-13.json',
        'https://www.francefootball.fr/generated/json/timeline/page-14.json',
        'https://www.francefootball.fr/generated/json/timeline/page-15.json',
        'https://www.francefootball.fr/generated/json/timeline/page-16.json',
        'https://www.francefootball.fr/generated/json/timeline/page-17.json',
        'https://www.francefootball.fr/generated/json/timeline/page-18.json',
        'https://www.francefootball.fr/generated/json/timeline/page-19.json',
        'https://www.francefootball.fr/generated/json/timeline/page-20.json',
        'https://www.francefootball.fr/generated/json/timeline/page-21.json',
    ]

    rules = (
        # Rule(IdleLinkExtractor(
        #     url=u'https://www.francefootball.fr/news/Coupe-du-monde-2018-groupe-a-la-russie-vers-les-huitiemes-l-egypte-vers-la-sortie-debrief-et-notes/913274'),
        #     callback='parse_match'),
        Rule(FFTimelineLinkExtractor(searched_term=(u'notes', u'débrief')),
             follow=True,
             callback='parse_match'),
    )

    def _requests_to_follow(self, response):
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = Request(url=link.url if isinstance(link, Link) else link, callback=self._response_downloaded)
                r.meta.update(rule=n, link_text=link.text if isinstance(link, Link) else link)
                yield rule.process_request(r, response)

    def parse_match(self, response):
        self.logger.info('Scraping match %s', response.url)
        loader = items.MatchItemLoader(response=response)
        md = response.xpath(
            '//div[contains(@class, "js-analytics-timestamp")]/@data-timestamp'
        ).extract_first()
        utc_dt = pytz.utc.localize(datetime.utcfromtimestamp(int(md)))
        loader.add_value('hash_url', hashlib.md5(response.url.encode('utf-8')).hexdigest())
        loader.add_value('source', 'FF')
        loader.add_value('match_date', utc_dt.isoformat())
        loader.add_xpath('home_team',
                         '(//h2[contains(text(),"notes")])[1]/text()')
        loader.add_xpath('away_team',
                         '(//h2[contains(text(),"notes")])[2]/text()')

        homeplayersdiv = response.xpath(
            '(//h2[contains(text(),"notes")])[1]/following-sibling::div[@class="paragraph"][1]//span/parent::div'
        )
        ho = list()
        homeplayersnotesunf = homeplayersdiv.xpath('string()').extract_first()
        if homeplayersnotesunf:
            self.logger.info('HOME %s', homeplayersnotesunf)
            ho = self.compute_players_from_unf(homeplayersnotesunf)
        aw = list()
        awayplayersdiv = response.xpath(
            '(//h2[contains(text(),"notes")])[2]/following-sibling::div[@class="paragraph"][1]//span/parent::div'
        )
        awayplayersnotesunf = awayplayersdiv.xpath('string()').extract_first()
        if awayplayersnotesunf:
            self.logger.info('AWAY %s', awayplayersnotesunf)
            aw = self.compute_players_from_unf(awayplayersnotesunf)

        if 15 >= len(ho) > 7 and 15 >= len(aw) > 7:
            for pl in ho:
                loader.add_value('players_home', pl)
            for pl in aw:
                loader.add_value('players_away', pl)
            yield loader.load_item()
        else:
            # Sinon, autre méthode.
            homeplayers = response.xpath(
                '(//h2[contains(text(),"notes")])[1]/following-sibling::div[@class="paragraph"][1]//span')
            for pl in homeplayers:
                loader.add_value('players_home', self.get_player(pl))
            homeplayersb = response.xpath(
                '(//h2[contains(text(),"notes")])[1]/following-sibling::div[@class="paragraph"][1]//b')
            for pl in homeplayersb:
                loader.add_value('players_home', self.get_player(pl))
            awayplayers = response.xpath(
                '(//h2[contains(text(),"notes")])[2]/following-sibling::div[@class="paragraph"][1]//span')
            for pl in awayplayers:
                loader.add_value('players_away', self.get_player(pl))
            awayplayersb = response.xpath(
                '(//h2[contains(text(),"notes")])[2]/following-sibling::div[@class="paragraph"][1]//b')
            for pl in awayplayersb:
                loader.add_value('players_away', self.get_player(pl))
            yield loader.load_item()

    def compute_players_from_unf(self, unfstring):
        regex = r'^(.*)\s+(\d).*?$'
        pllist = list()
        for plspacenote in [p.strip().replace(u'\xa0', u' ') for p in unfstring.split('\t') if
                            p is not None and 0 < len(p.strip()) <= 50]:
            m = re.match(regex, plspacenote)
            if m is None:
                continue
            name = m.group(1)
            note = m.group(2)
            if 'rbitre' in name or name.startswith('Note d') or len(name) > 50 or len(name) == 0:
                continue
            try:
                loader = items.PlayerItemLoader()
                loader.add_value('name', name)
                loader.add_value('rating', int(note))
                pllist.append(dict(loader.load_item()))
            except ValueError:
                continue
            except TypeError:
                continue
            except AttributeError:
                continue
        return pllist

    def get_player(self, pl):
        try:
            loader = items.PlayerItemLoader()
            try:
                name = self._extract_name(pl)
            except AttributeError:
                name = None
            if not name:
                name = self._extract_name(pl, 'preceding-sibling::br/following::text()')
            if not name:
                name = self._extract_name(pl, '../strong/text()')
            if not name:
                name = self._extract_name(pl, '../../text()')
            if 'rbitre' in name or name.startswith('Note d') or len(name) > 50 or len(name) == 0:
                pass
            else:
                loader.add_value('name', unidecode(name))
                try:
                    rating = pl.xpath('text()').extract_first().strip()
                except AttributeError:
                    rating = None
                if not rating:
                    rating = pl.xpath('strong/text()').extract_first().strip()
                if rating:
                    float(rating.strip())
                    loader.add_value('rating', rating.strip())
                    yield dict(loader.load_item())
        except ValueError:
            pass
        except TypeError:
            pass
        except AttributeError:
            pass

    def _extract_name(self, pl, xpathexpr='../text()'):
        possibilities = pl.xpath(xpathexpr)
        if len(possibilities) == 0:
            return None
        elif len(possibilities) == 1:
            return pl.xpath(xpathexpr).extract_first().strip()
        else:
            cleaned_possibilities = self._clean(possibilities.extract())
            curridx = len(pl.xpath('preceding-sibling::span'))
            if curridx == 0:
                # peut-être inversion span / strong ?
                curridx = len(pl.xpath('../preceding-sibling::span'))
            if curridx < len(cleaned_possibilities):
                return cleaned_possibilities[curridx].strip()
            return None

    def _clean(self, possibilities):
        return [p.strip() for p in possibilities if re.match(r'\w+', p) and 0 < len(p.strip()) <= 50]

# -*- coding: utf-8 -*-
import re
import json

from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
from scrapy import Request

from .. import items


class WhoscoredSpider(CrawlSpider):
    name = "whoscored"
    allowed_domains = ["whoscored.com"]

    rules = (
        Rule(
            LinkExtractor(allow=('Matches/\w{6,}/Live$',), restrict_xpaths='//div[@id="tournament-fixture-wrapper"]'),
            callback='parse_match'), )

    def start_requests(self):
        req = Request('https://www.whoscored.com/Regions/74/Tournaments/22/France-Ligue-1',
                      dont_filter=True)
        req.meta.update(selenium=True, wait_for_xpath='//table[@id="tournament-fixture"]')
        return [req]

    def increment_or_set_key(self, target_dict, key):
        if key not in target_dict:
            target_dict[key] = 1
        else:
            target_dict[key] += 1

    def parse_match(self, response):
        """
        Traite la page des données d'un match
        """
        self.logger.info('Scraping match %s', response.url)
        javascript_stats = response.xpath(
            '//div[@id="layout-content-wrapper"]/script[@type="text/javascript"]/text()').extract_first()
        pattern = r"(?:matchCentreData =)(.*);"
        m = re.search(pattern, javascript_stats).group().strip()[len('matchCentreData ='):][:-1]
        ws_stats = json.loads(m)
        total_time = ws_stats['maxMinute'] + 1
        out_time = {}
        in_time = {}
        goals_time = {'home': [], 'away': []}
        event_stats = {}

        # incremental stats
        for field in ['home', 'away']:
            goal_related_events = []
            for ev in ws_stats[field]['incidentEvents']:
                if 'playerId' in ev:
                    if not ev['playerId'] in event_stats:
                        event_stats[ev['playerId']] = {}
                try:
                    if 'cardType' in ev:
                        if ev['cardType']['displayName'] in ['SecondYellow', 'Red']:
                            out_time[ev['playerId']] = ev['minute']
                    elif 'SubstitutionOff' == ev['type']['displayName']:
                        out_time[ev['playerId']] = ev['minute']
                    elif 'SubstitutionOn' == ev['type']['displayName']:
                        in_time[ev['playerId']] = ev['minute']
                    elif 'Goal' == ev['type']['displayName']:
                        if 'isOwnGoal' in ev:
                            goals_time['away' if field == 'home' else 'home'].append(ev['minute'])
                            self.increment_or_set_key(event_stats[ev['playerId']], 'own_goals')
                        else:
                            goals_time[field].append(ev['minute'])
                            is_penalty = False
                            for q in ev['qualifiers']:
                                if 'Penalty' == q['type']['displayName']:
                                    is_penalty = True
                                    break
                            if is_penalty:
                                self.increment_or_set_key(event_stats[ev['playerId']], 'penalties_scored')
                            else:
                                for q in ev['qualifiers']:
                                    if 'RelatedEventId' == q['type']['displayName']:
                                        goal_related_events.append(q['value'])
                                        break
                                self.increment_or_set_key(event_stats[ev['playerId']], 'goals_scored')
                except KeyError:
                    pass
            # Loop again to find passes
            for ev in ws_stats[field]['incidentEvents']:
                if 'Pass' == ev['type']['displayName']:
                    self.increment_or_set_key(event_stats[ev['playerId']], 'goals_assists')
                elif str(ev['eventId']) in goal_related_events:
                    for q in ev['qualifiers']:
                        if q['type']['displayName'] in ('IntentionalGoalAssist', 'IntentionalAssist', 'KeyPass',):
                            self.increment_or_set_key(event_stats[ev['playerId']], 'goals_assists')
                            break

        loader = items.MatchItemLoader(items.MatchItem(), response=response)
        loader.add_value('match_date', ws_stats['startTime'])
        loader.add_value('home_team', ws_stats['home']['name'])
        loader.add_value('away_team', ws_stats['away']['name'])
        loader.add_value('home_score', ws_stats['score'].split(' : ')[0])
        loader.add_value('away_score', ws_stats['score'].split(' : ')[1])

        for field in ['home', 'away']:
            conceded_goals = goals_time['away' if field == 'home' else 'home']
            conceded_goals.sort()
            for pl in ws_stats[field]['players']:
                if ('isFirstEleven' in pl) or ('subbedInExpandedMinute' in pl):
                    loader.add_value('players_%s' % field,
                                     self.get_player(pl, conceded_goals, total_time, out_time, in_time, event_stats))
        yield loader.load_item()

    def get_player(self, pl, conceded_goals, total_time, out_time, in_time, event_stats):
        if 'ratings' in pl['stats']:
            max_key = max(pl['stats']['ratings'], key=int)
            # +001 because WS rounds ...5 UP while python rounds it down.
            mark = round(pl['stats']['ratings'][max_key] + .001, 1)
        loader = items.PlayerItemLoader()
        loader.add_value('name', pl['name'])
        loader.add_value('rating', mark)
        loader.add_value('stats', self.get_stats(pl, conceded_goals, total_time, out_time, in_time, event_stats))
        return dict(loader.load_item())

    def get_stats(self, pl, conceded_goals, total_time, out_time, in_time, event_stats):
        read_stats = {}
        if pl['playerId'] in event_stats:
            read_stats = event_stats[pl['playerId']]
        read_stats['goals_saved'] = len(pl['stats']['totalSaves']) if 'totalSaves' in pl['stats'] else 0
        if 'isFirstEleven' in pl:
            if pl['playerId'] in out_time:
                read_stats['playtime'] = out_time[pl['playerId']]
                read_stats['goals_conceded'] = len(
                    list(filter((lambda x: x <= out_time[pl['playerId']]), conceded_goals)))
            else:
                read_stats['playtime'] = total_time
                read_stats['goals_conceded'] = len(conceded_goals)
        elif pl['position'] == 'Sub' and 'subbedInExpandedMinute' in pl:
            if pl['playerId'] in out_time:
                read_stats['playtime'] = out_time[pl['playerId']] - in_time[pl['playerId']]
                read_stats['goals_conceded'] = len(list(
                    filter((lambda x: x <= out_time[pl['playerId']] and x >= in_time[pl['playerId']]),
                           conceded_goals)))
            else:
                read_stats['playtime'] = total_time - in_time[pl['playerId']]
                read_stats['goals_conceded'] = len(
                    list(filter((lambda x: x >= in_time[pl['playerId']]), conceded_goals)))
        loader = items.PlayerStatItemLoader()
        for key in read_stats:
            loader.add_value(key, read_stats[key])
        return dict(loader.load_item())
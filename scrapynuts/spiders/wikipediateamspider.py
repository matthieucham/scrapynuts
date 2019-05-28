import scrapy
from .. import items


class WikipediaTeamsSpider(scrapy.Spider):
    name = "wikipediateams"
    start_urls = [
        "https://en.wikipedia.org/wiki/2019_FIFA_Women%27s_World_Cup_squads"
    ]

    translate_pos = {'GK': 'G', 'DF': 'D', 'MF': 'M', 'FW': 'A'}

    def parse(self, response):
        teams = list()
        for team_selector in response.css('.wikitable'):
            teams.append(self.load_team(team_selector))
        return teams

    def load_team(self, team_selector):
        loader = items.TeamItemLoader(selector=team_selector)
        team_name = team_selector.xpath('preceding-sibling::h3/span/text()')[-1].extract()
        loader.add_value('name', team_name)
        for pl in team_selector.css('.nat-fs-player'):
            loader.add_value('players', self.load_player(pl))
        return loader.load_item()

    def load_player(self, player_selector):
        loader = items.TeamPlayerItemLoader(selector=player_selector)
        nm = player_selector.xpath('th/@data-sort-value').extract_first()
        dob = player_selector.css('.bday::text').extract_first()
        raw_p = player_selector.xpath('td[2]/a/text()').extract_first()
        if nm:
            loader.add_value('first_name', (nm.split(',')[1]).strip())
            loader.add_value('last_name', (nm.split(',')[0]).strip())
        else:
            nm = player_selector.xpath('th/span/@data-sort-value').extract_first()
            if nm:
                loader.add_value('first_name', (nm.split(',')[1]).strip())
                loader.add_value('last_name', (nm.split(',')[0]).strip())
            else:
                nm = player_selector.xpath('th/a/text()').extract_first()
                splitted = nm.split(' ')
                if len(splitted) > 1:
                    loader.add_value('first_name', (splitted[1]).strip())
                loader.add_value('last_name', (splitted[0]).strip())
                loader.add_value('surname', nm.strip())
        loader.add_value('dob', dob)
        loader.add_value('position', self.translate_pos[raw_p])
        return loader.load_item()

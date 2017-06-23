# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst, Compose, MapCompose


class MatchItem(scrapy.Item):
    hash_url = scrapy.Field()
    source = scrapy.Field()
    match_date = scrapy.Field()
    home_team = scrapy.Field()
    away_team = scrapy.Field()
    home_score = scrapy.Field()
    away_score = scrapy.Field()
    players_home = scrapy.Field(output_processor=Identity())  # List of players with stats and notes
    players_away = scrapy.Field(output_processor=Identity())  # List of players with stats and notes
    pass


class PlayerItem(scrapy.Item):
    name = scrapy.Field()
    stats = scrapy.Field()
    rating = scrapy.Field()


class PlayerStatItem(scrapy.Item):
    playtime = scrapy.Field()
    goals_scored = scrapy.Field()
    goals_assists = scrapy.Field()
    penalties_scored = scrapy.Field()
    penalties_awarded = scrapy.Field()
    goals_saved = scrapy.Field()
    goals_conceded = scrapy.Field()
    own_goals = scrapy.Field()
    penalties_saved = scrapy.Field()


class MatchItemLoader(ItemLoader):
    default_item_class = MatchItem
    default_output_processor = TakeFirst()


class PlayerItemLoader(ItemLoader):
    default_item_class = PlayerItem
    default_output_processor = TakeFirst()


class PlayerStatItemLoader(ItemLoader):
    default_item_class = PlayerStatItem
    default_output_processor = TakeFirst()
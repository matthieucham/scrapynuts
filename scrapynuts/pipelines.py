from scrapy.exceptions import DropItem
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from . import settings
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ScrapynutsFilterPipeline(object):
    def process_item(self, item, spider):
        if not item['players_home'] or not item['players_away']:
            raise DropItem('Filtered incomplete item')
        return item


class ScrapynutsPostStatnutsPipeline(object):
    def __init__(self):
        self.client_id = settings.STATNUTS_CLIENT_ID
        self.client_secret = settings.STATNUTS_SECRET
        self.sn_store_url = settings.STATNUTS_URL + 'scrap/datasheets/'
        self.token_url = settings.STATNUTS_URL + 'o/token/'
        self.access_token = None
        self.oauth = OAuth2Session(client=BackendApplicationClient(client_id=self.client_id))

    def _get_access_token(self):
        token = self.oauth.fetch_token(token_url=self.token_url, client_id=self.client_id,
                                       client_secret=self.client_secret)
        return token

    def process_item(self, item, spider):
        if self.access_token is None:
            self.access_token = self._get_access_token()
        self.oauth.post(self.sn_store_url, data=item)
        print 'Item stored with hash = %s' % item['hash_url']
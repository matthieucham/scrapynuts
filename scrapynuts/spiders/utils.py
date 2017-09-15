import lxml.etree as etree
import re
from scrapy.linkextractors.lxmlhtml import LxmlParserLinkExtractor, _nons, FilteringLinkExtractor
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.response import get_base_url
from scrapy.utils.python import unique


class RestrictTextParserLinkExtractor(LxmlParserLinkExtractor):
    def __init__(self, tag="a", attr="href", process=None, unique=False, link_text_regex=None):
        self.link_text_regex = link_text_regex
        super(RestrictTextParserLinkExtractor, self).__init__(tag, attr, process, unique)

    def scan_text(self, value):
        if not value:
            return False
        if not self.link_text_regex:
            return True
        else:
            return re.search(self.link_text_regex, value)

    def _iter_links(self, document):
        for el in document.iter(etree.Element):
            if not self.scan_tag(_nons(el.tag)):
                continue
            if not self.scan_text(el.text):
                continue
            attribs = el.attrib
            for attrib in attribs:
                if not self.scan_attr(attrib):
                    continue
                yield (el, attrib, attribs[attrib])


class RestrictTextLinkExtractor(FilteringLinkExtractor):
    def __init__(self, allow=(), deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                 tags=('a', 'area'), attrs=('href',), canonicalize=True,
                 unique=True, process_value=None, deny_extensions=None, restrict_css=(), link_text_regex=None):
        tags, attrs = set(arg_to_iter(tags)), set(arg_to_iter(attrs))
        tag_func = lambda x: x in tags
        attr_func = lambda x: x in attrs
        lx = RestrictTextParserLinkExtractor(tag=tag_func, attr=attr_func,
                                             unique=unique, process=process_value, link_text_regex=link_text_regex)

        super(RestrictTextLinkExtractor, self).__init__(lx, allow=allow, deny=deny,
                                                        allow_domains=allow_domains, deny_domains=deny_domains,
                                                        restrict_xpaths=restrict_xpaths, restrict_css=restrict_css,
                                                        canonicalize=canonicalize, deny_extensions=deny_extensions)

    def extract_links(self, response):
        base_url = get_base_url(response)
        if self.restrict_xpaths:
            docs = [subdoc
                    for x in self.restrict_xpaths
                    for subdoc in response.xpath(x)]
        else:
            docs = [response.selector]
        all_links = []
        for doc in docs:
            links = self._extract_links(doc, response.url, response.encoding, base_url)
            all_links.extend(self._process_links(links))
        return unique(all_links)
import unittest
import requests
from utils import debrief_analyzer


def get_html_content_from(url):
    response = requests.get(url)
    response.raise_for_status()
    return str(response.text)


class MLParserTest(unittest.TestCase):
    def test_debrieftext_extractor(self):
        content = get_html_content_from(
            # "https://www.letelegramme.fr/football/stade-brestois-29/brest-saint-etienne-4-1-les-notes-de-la-redaction-et-des-lecteurs-21-11-2020-12660273.php?utm_source=rss_telegramme&utm_medium=rss&utm_campaign=rss&xtor=RSS-35"
            #"https://www.francefootball.fr/news/Les-notes-de-lyon-saint-etienne/1192638"
            "https://www.hommedumatch.fr/articles/france/ligue-1-30eme-j-les-notes-de-nice-om-3-1_2532671"
        )

        raw = debrief_analyzer.get_raw_content(
            #content, contentxpath="//div[@class='main']"
            content, contentxpath="//article[@id='the-post']"
        )

        debrief_analyzer.analyze(raw)

        # debrief_analyzer.get_raw_content(content)


if __name__ == "__main__":
    unittest.main()

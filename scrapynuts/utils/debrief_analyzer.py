from bs4 import BeautifulSoup
import lxml.html
from lxml import etree
import html as ihtml
import re
from unidecode import unidecode
import spacy


def clean_content(rawcontent, remove_hyperlinks=False):
    text = BeautifulSoup(ihtml.unescape(rawcontent), "lxml").get_text(separator=" ")
    text = re.sub(r"\s+", " ", text)
    if remove_hyperlinks:
        text = re.sub(r"http[s]?://\S+", "", text)
    text = unidecode(text)
    return text


def get_raw_content(htmlContent, contentxpath=None):
    # soup = BeautifulSoup(htmlContent, "html.parser")
    section = htmlContent

    if contentxpath:
        # extract content at this location:
        root = lxml.html.fromstring(htmlContent)
        sectionPath = root.xpath(contentxpath)[0]
        section = etree.tostring(sectionPath, encoding="utf-8").decode("utf-8")

    return clean_content(section, remove_hyperlinks=True)


# REGEX_TOKENS = r'(([\w\'\-\\]*[\.\s]*[\w\'\-\\]+)\s*\(?(\d{1,2}(?:[,\.]\d{1,2})?)\)?)'
REGEX_TOKENS = r'(((?:[A-Z][a-zA-Z\'\-\\]*[\.\s]+)?[a-zA-Z]+[\'\-\\]*[a-zA-Z]+)\s*\(?(\d{1,2}(?:[,\.]\d{1,2})?)\D\)?)'

def analyze(content):
    print(content)
    for m in re.findall(REGEX_TOKENS, content):
        print("Joueur='%s' Note='%s'" % (m[1], m[2]) )
    # nlp = spacy.load("xx_ent_wiki_sm")
    # tokens = nlp(content)
    # for token in tokens:
    #     print(token.text, token.ent_type_)

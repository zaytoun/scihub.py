#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: 0.0.1
# data: 2021.05.12
# author: 
#   peterhs73
#   Roy Kid
# contact: lijichen365@126.com
# original: https://github.com/peterhs73/RefParse.git

"""Reference parser for different APIs"""
import abc
import os
import re
from calendar import month_abbr, month_name
from collections import defaultdict
from datetime import datetime


import bs4
import requests
import yaml
from bs4 import BeautifulSoup
from pylatexenc.latexencode import unicode_to_latex
from titlecase import titlecase


class Filters:
    """Filter used for Cheetah Template engine"""

    @classmethod
    def list(cls, *args, **kwargs):
        return list(*args, **kwargs)

    @classmethod
    def map(cls, *args, **kwargs):
        return map(*args, **kwargs)

    @classmethod
    def titlecase(cls, text):
        """A wrapper for titlecase function"""
        return titlecase(text)

    @classmethod
    def month_abbr(cls, month):
        """A wrapper for calendar.month_abbr

        :param month str: month string or int, empty string will
            be converted to 0, and return an empty string
        """
        month = int(month) if month else 0
        return month_abbr[month]

    @classmethod
    def month_name(cls, month):
        """A wrapper for calendar.month_name

        :param month str: month string or int, empty string will
            be converted to 0, and return an empty string
        """
        month = int(month) if month else 0
        return month_name[month]

    @classmethod
    def unicode_to_latex(cls, text):
        """A wrapper for calendar.month_name"""
        return unicode_to_latex(text)

# Grab configuration templates


class Empty(object):
    """Use to create empty object

    Used as an placeholder for bs4 tag object.
    string and get_text method return empty strin"""

    string = ""

    def get_text(self, *args, **kwargs):
        return ""

def get_attr(obj, path):
    """Get nested attribute

    :param obj object/namedtuple: object to get the attribute
    :param path str: nested attribute path, separated by '/'
    """

    try:
        for p in path.split("/"):
            obj = getattr(obj, p)
        return obj
    except AttributeError:
        return Empty()

def get_string(obj, path):
    """Get the string attribute of nested object

    With strip=True, text with html tags around is be stripped away
    its white space around
    :param obj object/namedtuple: object to get the attribute
    :param path str: nested attribute path, separated by '/'
    """
    try:
        return get_attr(obj, path).get_text(strip=True)
    except AttributeError:
        return ""

def html_convert(tag_element):
    """extract the html content of the tag element

    Extract the html of the tag element, and present it as close
    as the browser. Currently this function is limited.

    :param tag_element bs4.element.tag: tag to extract content
        This should be a soup object
    """

    _html_to_latex_tags = defaultdict(lambda: ("", ""))
    _html_to_latex_tags.update(
        {
            "i": ("\\textit{", "}"),
            "b": ("\\textbf{", "}"),
            "strong": ("\\textbf{", "}"),
            "em": ("\\emph{", "}"),
            "u": ("\\underline{", "}"),
            "sub": ("\\textsubscript{", "}"),
            "sup": ("\\textsuperscript{", "}"),
        }
    )

    if tag_element is None:
        return "", "", ""

    content = []
    content_html = []
    content_latex = []
    tag_pattern = re.compile(r"<\w+\s*\w*>(.+)</(\w+)>")

    for ele in tag_element:
        if not isinstance(ele, bs4.element.Tag):
            str_ = re.sub(r"([\n].+[\n])\s+", r"\1", ele)
            str_ = re.sub(r"\s+", " ", str_.replace("\n", " "))
            content.append(str_)
            content_html.append(str_)
            content_latex.append(str_)
        else:
            subtag = re.match(tag_pattern, str(ele))
            text = subtag.group(1)
            tag = subtag.group(2)

            content.append(text)
            content_html.append(str(ele))
            latex = "{latex[0]}{text}{latex[1]}".format(
                latex=_html_to_latex_tags[tag], text=text,
            )
            content_latex.append(latex)
    return (
        "".join(content).strip(),
        "".join(content_latex).strip(),
        "".join(content_html).strip(),
    )

class ParserBase(abc.ABC):
    """Abstract method for parsers

    If the attribute is not found, a empty string will be returned
    """

    REFNAME: str
    REF_URL: str
    QUERY_URL: str
    HEADER: dict

    def __init__(self, reference, proxies):

        self.query_url = self.QUERY_URL.format(reference)
        self.ok, self.text = self.request_text(self.query_url, proxies)
        self.parsed = defaultdict(str)

        if self.ok:
            # needs to use xml, abstract does not show up with lxml
            self.soup = BeautifulSoup(self.text, "xml")
            self.parsed[self.REFNAME] = reference
            self.parsed["reference"] = reference
            self.parsed["ref_type"] = self.REFNAME.replace(" ", "_")
            self.parsed["url"] = self.REF_URL.format(reference)
            # parse api
            self.parsed.update(self.parse_api(self.soup))

    def request_text(self, url, proxies):

        r = requests.get(
            url, headers={"Accept": "application/vnd.crossref.unixsd+xml", }, proxies=proxies
        )
        if r.ok:
            # self.log.info(f"{self.REFNAME} found")
            print(f"{self.REFNAME} found")
        elif r.status_code == 404 or r.status_code == 400:
            # self.log.error(f"Incorrect {self.REFNAME}")
            print(f"Incorrect {self.REFNAME}")
        elif r.status_code == 504:
            # self.log.error(f"Gateway timeout, please try again")
            print(f"Gateway timeout, please try again")
        r.encoding = "utf-8"
        return r.ok, r.text

    @abc.abstractmethod
    def parse_api(self, soup):
        """The main function to parse api

        The method is required. This should be replaced for parsers
        """
        return {}

class CrossRefParser(ParserBase):

    REFNAME = "doi"
    REF_URL = "http://doi.org/{}"
    QUERY_URL = "http://dx.doi.org/{}"
    HEADER = {"Accept": "application/vnd.crossref.unixsd+xml"}

    def parse_api(self, soup):
        pdict = {}

        pdict["has_publication"] = True
        journal_meta = soup.journal_metadata
        pdict["journal_full_title"] = get_string(journal_meta, "full_title")
        pdict["journal_abbrev_title"] = get_string(
            journal_meta, "abbrev_title"
        )

        article_meta = soup.journal_article

        author = []
        author_tag = get_attr(article_meta, "contributors")
        for name in author_tag.find_all("person_name"):
            author.append([name.surname.string, name.given_name.string])
        pdict["author"] = author

        (
            pdict["title"],
            pdict["title_latex"],
            pdict["title_html"],
        ) = html_convert(get_attr(article_meta, "titles/title"))

        pdict["abstract"] = get_string(article_meta, "abstract")

        pub_online = article_meta.find(
            "publication_date", {"media_type": "online"}
        )
        pdict["online_year"] = get_string(pub_online, "year")
        pdict["online_month"] = get_string(pub_online, "month")
        pdict["online_day"] = get_string(pub_online, "day")

        pub_print = article_meta.find(
            "publication_date", {"media_type": "print"}
        )
        if pub_print:
            # self.log.info("print version found")
            print("print version found")
            pdict["has_print"] = True
            pdict["print_year"] = get_string(pub_online, "year")
            pdict["print_month"] = get_string(pub_online, "month")
            pdict["print_day"] = get_string(pub_online, "day")

            first_page = get_string(soup, "pages/first_page")
            last_page = get_string(soup, "pages/last_page")
            pdict["pages"] = (
                [first_page, last_page] if last_page else [first_page]
            )

            issue_meta = soup.journal_issue
            pdict["volume"] = get_string(issue_meta, "journal_volume/volume")
            pdict["issue"] = get_string(issue_meta, "issue")
        else:
            pdict["has_print"] = False
        return pdict

class arXivParser(ParserBase):
    REF_URL = "http://arxiv.org/{}"
    QUERY_URL = "http://export.arxiv.org/api/query?id_list={}"
    REFNAME = "arXiv ID"
    HEADER = {}

    def search_doi(self, soup):
        """Check if the article has doi"""
        doi_tag = soup.find("link", {"title": "doi"})
        if doi_tag:
            # self.log.warning(f"article has doi: {doi_tag['href']}")
            print(f"article has doi: {doi_tag['href']}")

    def parse_api(self, soup):
        """Parse the article information"""
        pdict = {}
        pdict["has_publication"] = False
        pdict["has_print"] = False
        self.search_doi(soup)

        article_meta = soup.entry
        # remove unnecessary line break
        pdict["abstract"] = get_string(article_meta, "summary").replace(
            "\n", " "
        )
        print(repr(article_meta.summary.get_text(strip=True)))
        # sometimes the arXiv article title has unnecessary linebreak
        pdict["title"] = get_string(article_meta, "title").replace("\n ", "")
        pdict["title_latex"] = pdict["title"]

        pub_date = datetime.strptime(
            article_meta.updated.string, "%Y-%m-%dT%H:%M:%SZ"
        )
        pdict["online_year"] = str(pub_date.year)
        pdict["online_month"] = str(pub_date.month)
        pdict["online_day"] = str(pub_date.day)

        author = []
        for name in article_meta.find_all("name"):
            name_ = re.match(r"([\s\S]+) (\w+)", name.string)
            author.append([name_.group(2), name_.group(1)])
        pdict["author"] = author
        return pdict


"""Main API class"""

import re

from Cheetah.Template import Template

api_method = {"crossref": CrossRefParser, "arXiv": arXivParser}


class RefAPI:
    """Abstract base class for user interaction

    For attribute that is None, empty string will be returned
    """

    CURPATH = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(CURPATH, "config.yaml"), "r") as config:
        FORMAT_CONFIG = yaml.load(config, Loader=yaml.SafeLoader)

    def __init__(self, reference, proxies):
        """Initiate the object with different apis

        :param url string: the url of the target
        """
        self.proxies = proxies
        cleaned_ref, api_type = self.match_reference(reference)
        if api_type:
            self.format_template = RefAPI.FORMAT_CONFIG
            self.parser = api_method[api_type](cleaned_ref, self.proxies)
            self.status = self.parser.ok
            self.output = {}
        else:
            self.status = False

    def match_reference(self, reference):
        """Match reference into either doi or arXiv ID

        The pattern for doi can be found on the API page
        arXiv ID has types, pre-2007 and post-2007
        Here the patterns are slightly modified to do a full search
        """
        doi_pattern = re.compile(r"10.\d{4,9}/[-._;()/:a-zA-Z0-9]+")
        arxiv_pattern1 = re.compile(r"\d{4}.\d{4,5}(v\d)?")
        arxiv_pattern2 = re.compile(r"[-a-z]+(.[A-Z]{2})?/\d{7}(v\d)?")

        if doi_pattern.search(reference):
            return doi_pattern.search(reference).group(0), "crossref"
        elif arxiv_pattern1.search(reference):
            return arxiv_pattern1.search(reference).group(0), "arXiv"
        elif arxiv_pattern2.search(reference):
            return arxiv_pattern2.search(reference).group(0), "arXiv"
        else:
            # api_logger.error(f"{reference} is not a valid doi or arXiv ID")
            return reference, ""

    def render(self, ref_format):
        """Render the desired format

        If the ref_format is already rendered, it stores in the dictionary
        else it will render the format
        :param ref_format string: reference format
        """
        if not self.status:
            return
        elif ref_format not in self.output:

            template = self.format_template[ref_format]
            result = Template(
                template, searchList=[{"FN": Filters}, self.parser.parsed],
            )

            self.output[ref_format] = str(result)
        return self.output[ref_format]

if __name__ == "__main__":
    """ Test section
    """
    from pprint import pprint
    print = pprint

    reference = 'https://doi.org/10.1021/acs.macromol.8b00309'
    formats = ['bibtex', 'md', 'text', 'rst']
    proxy = "http://127.0.0.1:8889"
    proxies = {
                "http": proxy,
                "https": proxy, }

    api = RefAPI(reference, proxies)
    results = []
    if api.status:
        for ref_format in formats:
            results.append((ref_format, api.render(ref_format)))

        # click.echo("\n--- Output reference --- \n")
        print("--- Output reference ---")
        for ref_format, result in results:
        #     click.echo(f"--- {ref_format}\n")
        #     click.echo(result)
            print(f"{ref_format}\n")
            print(result)


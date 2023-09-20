#!/usr/bin/env python3
"""
bundesAPI/handelsregister is the command-line interface for for the shared register of companies portal for the German federal states.
You can query, download, automate and much more, without using a web browser.
"""

import argparse
from unittest import case
import mechanize
import re
import pathlib
import sys
from bs4 import BeautifulSoup

# Dictionaries to map arguments to values
schlagwortOptionen = { #dictionary
    "all": 1,
    "min": 2,
    "exact": 3
}

rechtsFormEncoding = {
    "Aktiengesellschaft": 1,
"eingetragene Genossenschaft": 2,
"eingetragener Verein": 3,
"Einzelkauffrau": 4,
"Einzelkaufmann": 5,
"Europäische Aktiengesellschaft (SE)": 6,
"Europäische wirtschaftliche Interessenvereinigung": 7,
"Gesellschaft mit beschränkter Haftung": 8,
"HRA Juristische Person": 9,
"Kommanditgesellschaft": 10,
"Offene Handelsgesellschaft": 12,
"Partnerschaft": 13,
"Rechtsform ausländischen Rechts GnR": 14,
"Rechtsform ausländischen Rechts HRA": 15,
"Rechtsform ausländischen Rechts HRb": 16,
"Rechtsform ausländischen Rechts PR": 17,
"Seerechtliche Gesellschaft": 18,
"Versicherungsverein auf Gegenseitigkeit": 19,
"Anstalt öffentlichen Rechts": 40,
"Bergrechtliche Gesellschaft": 46,
"Körperschaft öffentlichen Rechts": 48,
"Europäische Genossenschaft (SCE)": 49,
"Stiftung privaten Rechts": 51,
"Stiftung öffentlichen Rechts": 52,
"HRA sonstige Rechtsformen": 53,
"Sonstige juristische Person": 54,
"Einzelkaufmann/Einzelkauffrau": 55
}

def handleAbbreviation(abb: str) -> int :
    match abb:
        case "GmbH":
            abb = "Gesellschaft mit beschränkter Haftung"
        case "AG":
            abb= "Aktiengesellschaft"
        case "oHG":
            abb = "Offene Handelsgesellschaft"
        case "eG":
            abb = "eingetragene Genossenschaft"
        case "eV" | "e.V.":
            abb = "eingetragener Verein"
        case "SE":
            abb = "Europäische Aktiengesellschaft (SE)"
        case "KG":
            abb = "Kommanditgesellschaft"
        case "SCE":
            abb = "Europäische Genossenschaft (SCE)"
    return rechtsFormEncoding.get(abb)

class HandelsRegister:
    def __init__(self, args):
        self.args = args
        self.browser = mechanize.Browser()

        self.browser.set_debug_http(args.debug) # Print HTTP headers.
        self.browser.set_debug_responses(args.debug) # Log HTTP response bodies (i.e. the HTML, most of the time).
        # self.browser.set_debug_redirects(True)

        self.browser.set_handle_robots(False) # Ignore robots.txt.  Do not do this without thought and consideration.
        self.browser.set_handle_equiv(True) # Don't handle HTTP-EQUIV headers (HTTP headers embedded in HTML).
        self.browser.set_handle_gzip(True) # Tell the browser to send the Accept-Encoding: gzip header to the server
                                           # to indicate it supports gzip Content-Encoding
        self.browser.set_handle_refresh(False) # Don't handle Refresh redirections
        self.browser.set_handle_redirect(True) # Set whether to handle HTTP 30x redirections.
        self.browser.set_handle_referer(True) # Don't add Referer (sic) header

        self.browser.addheaders = [ #header is sent out like this in all of them
            (
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
            ),
            (   "Accept-Language", "en-GB,en;q=0.9"   ),
            (   "Accept-Encoding", "gzip, deflate, br"    ),
            (
                "Accept",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            ),
            (   "Connection", "keep-alive"    ),
        ]
        
        self.cachedir = pathlib.Path("cache")
        self.cachedir.mkdir(parents=True, exist_ok=True)

    def open_startpage(self):
        self.browser.open("https://www.handelsregister.de", timeout=10)

    def companyname2cachename(self, companyname):
        # map a companyname to a filename, that caches the downloaded HTML, so re-running this script touches the
        # webserver less often.
        return self.cachedir / companyname

    def search_company(self):
        cachename = self.companyname2cachename(self.args.schlagwoerter)
        if self.args.force==False and cachename.exists():
            with open(cachename, "r") as f:
                html = f.read()
                print("return cached content for %s" % self.args.schlagwoerter)
        else:
            # TODO implement token bucket to abide by rate limit
            # Use an atomic counter: https://gist.github.com/benhoyt/8c8a8d62debe8e5aa5340373f9c509c7
            response_search = self.browser.follow_link(text="Advanced search")
            #So first you search for the Content by following the link "Advanced search"

            if self.args.debug == True:
                print(self.browser.title())

            self.browser.select_form(name="form") #fill out the form in the advanced search option

            self.browser["form:schlagwoerter"] = self.args.schlagwoerter 
            so_id = schlagwortOptionen.get(self.args.schlagwortOptionen) #usal get for enums

            self.browser["form:schlagwortOptionen"] = [str(so_id)] #seems to set the value 

            #form:registerArt_input for the search with HR-number

            #when value is equal to HRA, HRB, GnR, PR, VR,
            #It's in an input mask - or a select

            response_result = self.browser.submit()

            if self.args.debug == True:
                print(self.browser.title())

            html = response_result.read().decode("utf-8")
            with open(cachename, "w") as f:
                f.write(html)

            # TODO catch the situation if there's more than one company?
            # TODO get all documents attached to the exact company
            # TODO parse useful information out of the PDFsf
        return get_companies_in_searchresults(html)


def parse_result(result):
    cells = []
    for cellnum, cell in enumerate(result.find_all('td')):
        #print('[%d]: %s [%s]' % (cellnum, cell.text, cell))
        cells.append(cell.text.strip())
    #assert cells[7] == 'History'
    d = {}
    d['court'] = cells[1]
    d['name'] = cells[2]
    d['state'] = cells[3]
    d['status'] = cells[4]
    d['documents'] = cells[5] # todo: get the document links
    d['history'] = []
    hist_start = 8
    hist_cnt = (len(cells)-hist_start)/3
    for i in range(hist_start, len(cells) - 1, 3):
        d['history'].append((cells[i], cells[i+1])) # (name, location)
    #print('d:',d)
    return d

def pr_company_info(c):
    for tag in ('name', 'court', 'state', 'status'):
        print('%s: %s' % (tag, c.get(tag, '-')))
    print('history:')
    for name, loc in c.get('history'):
        print(name, loc)

def get_companies_in_searchresults(html):
    soup = BeautifulSoup(html, 'html.parser')
    grid = soup.find('table', role='grid')
    #print('grid: %s', grid)
  
    results = []
    for result in grid.find_all('tr'):
        a = result.get('data-ri')
        if a is not None:
            index = int(a)
            #print('r[%d] %s' % (index, result))
            d = parse_result(result)
            results.append(d)
    return results

def parse_args():
# Parse arguments
    parser = argparse.ArgumentParser(description='A handelsregister CLI')
    parser.add_argument(
                          "-d",
                          "--debug",
                          help="Enable debug mode and activate logging",
                          action="store_true"
                        )
    parser.add_argument(
                          "-f",
                          "--force",
                          help="Force a fresh pull and skip the cache",
                          action="store_true"
                        )
    parser.add_argument(
                          "-s",
                          "--schlagwoerter",
                          help="Search for the provided keywords",
                          required=True,
                          default="Gasag AG" # TODO replace default with a generic search term
                        )
    parser.add_argument(
                          "-so",
                          "--schlagwortOptionen",
                          help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
                          choices=["all", "min", "exact"],
                          default="all"
                        )
    parser.add_argument(
                          "-ra",
                          "--registerArt",
                          help="Registerart options: alle, HRA, HRB, GnR, PR, VR.",
                          choices=["HRA", "HRB", "GnR", "PR", "VR"],
                          default=""
                        )
    parser.add_argument(  #form:registerNummer
                          "-rn",
                          "--registerNummer",
                          help="Register number, without the type"
                          default=""
                        )
    args = parser.parse_args()


    # Enable debugging if wanted
    if args.debug == True:
        import logging
        logger = logging.getLogger("mechanize")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.DEBUG)

    return args

if __name__ == "__main__": #condition means: are you been directly called from interpreter
    args = parse_args()
    h = HandelsRegister(args)
    h.open_startpage()
    companies = h.search_company()
    if companies is not None:
        for c in companies:
            pr_company_info(c)

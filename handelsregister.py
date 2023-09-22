#!/usr/bin/env python3
"""
bundesAPI/handelsregister is the command-line interface for for the shared register of companies portal for the German federal states.
You can query, download, automate and much more, without using a web browser.
"""

import argparse
from dictionaries import *
from unittest import case
import mechanize
import re
import pathlib
import sys
from bs4 import BeautifulSoup

class HandelsRegister:
    def __init__(self, parser):

        self.args = parser.parse_args()
        # Enable debugging if wanted
        if self.args.debug == True:
            import logging
            logger = logging.getLogger("mechanize")
            logger.addHandler(logging.StreamHandler(sys.stdout))
            logger.setLevel(logging.DEBUG)

        #Save default args
        self.default_args = {}
        for key in vars(self.args):
            self.default_args[key] = parser.get_default(key)

        self.browser = mechanize.Browser()

        self.browser.set_debug_http(self.args.debug) # Print HTTP headers.
        self.browser.set_debug_responses(self.args.debug) # Log HTTP response bodies (i.e. the HTML, most of the time).
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
        print(self.cachedir)
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
            #This follows the link either by looking for the text in the a, so the displayed one or the title
            #most likely just the text, right?

            if self.args.debug == True:
                print(self.browser.title())

            self.browser.select_form(name="form") #fill out the form in the advanced search option

            #Schlagwoerteingabe
            self.browser["form:schlagwoerter"] = self.args.schlagwoerter 
            so_id = schlagwortOptionen.get(self.args.schlagwortOptionen) #usal get for enums

            #Suchoption
            self.browser["form:schlagwortOptionen"] = [str(so_id)] #seems to set the value 

            #form:registerArt_input for the search with HR-number
            print(self.args.registerArt)
            self.browser["form:registerArt_input"] = [self.args.registerArt] #sets it as sequence

            #Registergericht kann gut sein, dass es eigentlich form:registergericht_focus ist
            ra_id = registerGerichtEncoding.get(self.args.registerCourt)
            self.browser["form:registergericht_input"] = [str(ra_id)]

            #Register-Nr
            self.browser["form:registerNummer"] = self.args.registerNummer

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
    
    def retrieve_documents(self):
        return 0


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

def create_parser():
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
                          required=False,
                          default=""
                        )
    parser.add_argument(
                          "-so",
                          "--schlagwortOptionen",
                          help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
                          choices=["all", "min", "exact"],
                          required= True,
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
                          help="Register number, without the type",
                          default=""
                        )
    parser.add_argument(  #form:registergericht or form:registergericht_focus -> rather form:registergericht_input
                          "-rc",
                          "--registerCourt",
                          help="Register court of the company",
                          default=""
                        )
    parser.add_argument(
                          "-dtd",
                          "--documentsToDownload",
                          help="AD = Aktueller Abdruck, CD = Chronologischer Abdruck, SI = Strukturiertes Inhalt",
                          choices=["AD", "CD", "SI"],
                          default=""
                        )



    return parser

if __name__ == "__main__": #condition means: are you been directly called from interpreter
    h = HandelsRegister(create_parser())
    h.open_startpage()
    companies = h.search_company()
    if companies is not None:
        for c in companies:
            pr_company_info(c)
#Köln HRB 39853
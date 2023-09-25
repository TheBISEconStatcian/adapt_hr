from selenium import webdriver
from selenium.webdriver.edge.options import Options
import time


class handelsregister:
    def __init__(self, parser):
        #Save important information from the parser first
        self.args = parser.parse_args()

        self.default_args = {}
        for key in vars(self.args):
            self.default_args[key] = parser.get_default(key)
        
        edge_options = Options()
        edge_options.add_argument("--headless") #To avodi annoying

        driver = webdriver.Edge(options = edge_options)
        driver.get('https://www.handelsregister.de/rp_web/welcome.xhtml')

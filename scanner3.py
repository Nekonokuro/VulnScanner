#!usr/bin/env python

import requests
import re
import urllib.parse as urlparse
from bs4 import BeautifulSoup

class Scanner:
    def __init__(self, url, ignore_links):
        self.session = requests.Session()
        self.target_url = url
        self.target_links = []
        self.links_to_ignore = ignore_links
    def extract_links_from(self, url):
        response = self.session.get(url)
        return re.findall('(?:href=")(.*?)"', response.content.decode(errors="ignore"))
    def crawl(self, url=None):
        if url == None:
            url = self.target_url
        href_links = self.extract_links_from(url)
        for link in href_links:
            link = urlparse.urljoin(url, link)
            if "#" in link:
                link = link.split("#")[0]
            if self.target_url in link and link not in self.target_links and link not in self.links_to_ignore:
                self.target_links.append(link)
                print(link)
                self.crawl(link)
    def extract_forms(self, url):
        response = self.session.get(url)
        parsed_html = BeautifulSoup(response.content, features="lxml")
        return parsed_html.findAll("form")
    def submit_form(self, form, value, url):
        action = form.get("action")
        post_url = urlparse.urljoin(url, action)
        method = form.get("method")

        inputs_list = form.findAll("input")
        post_data = {}
        for inputs in inputs_list:
            input_name = inputs.get("name")
            input_type = inputs.get("type")
            input_value = inputs.get("value")
            if input_type == "text":
                input_value = value

            post_data[input_name] = input_value
        if method == "post":
            return self.session.post(post_url, data=post_data)
        return self.session.get(post_url, params=post_data)
    def run_scanner(self):
        for link in self.target_links:
            forms = self.extract_forms(link)
            for form in forms:
                print("[+]Testing form in " + link)
                is_vulnerable_to_xss = self.test_xss_in_form(form, link)
                if is_vulnerable_to_xss:
                    print("\n\n[!!!]XSS discovered in " + link + "in the following form")
                    print(form)
            if "=" in link:
                print("[+]Testing " + link)
                is_vulnerable_to_xss = self.test_xss_in_link(link)
                if is_vulnerable_to_xss:
                    print("\n\n[!!!]XSS discovered in " + link)
    def test_xss_in_link(self, url):
        xss_script_test = "<sCript>alert('NOMNOM')</scriPt"
        url = url.replace("=", "=" + xss_script_test)
        response = self.session.get(url)
        return xss_script_test.encode() in response.content
    def test_xss_in_form(self, form, url):
        xss_script_test = "<sCript>alert('NOMNOM')</scriPt"
        response = self.submit_form(form, xss_script_test, url)
        return xss_script_test.encode() in response.content
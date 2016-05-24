from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from . import nltk_utils
from time import time
import threading
import requests
import logging
import urllib2
import urllib
import json

logger = logging.getLogger(__name__)

bing_api = 'https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web?$format=json&Query='
bing_key = 'IgVbvvtgQVYI7Yfu9hPgVx0Tmbih1gq5lFOXaIQH4f8'
user_agent = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'

def search(q, q_url):
    search_url = bing_api + urllib.quote(q)
    #print 'Search Url: %s\n' % search_url
    try:
        response = requests.get(search_url, auth=HTTPBasicAuth(bing_key, bing_key))
        results = response.json()['d']['results']
        urls = []
        for r in results:
            if r['Url'] != q_url:
                urls.append(r['Url'])
        if len(urls) >= 20:                    
            return urls[:20]
        else:
            return urls
    except Exception as e:
        logger.debug(e)
        #print e
        #print response.text
        #traceback.print_exc(file=sys.stdout)

class URLThread(threading.Thread):
    def __init__(self, _id, url, texts, *args, **kwargs):
        threading.Thread.__init__(self)
        self._id = _id
        self.url = url
        self.texts = texts

    def _get_art(self, url):
        #print 'requesting: {}'.format(url)
        req = urllib2.Request(url, headers={'User-Agent': user_agent})
        response = urllib2.urlopen(req, timeout=10)
        html = response.read()
        soup = BeautifulSoup(html, 'html5lib')
        [s.extract() for s in soup(['script', 'a', 'rel', 'style', 'img', 'link', 'style'])]
        text = soup.get_text()
        text = nltk_utils.preprocess_text(text)
        return text

    def run(self):
        txt = self._get_art(self.url)
        self.texts[self._id] = txt

def get_articles(urls):
    corpus = [''] * len(urls)
    t0 = time()
    threads = []
    no_threads = 10
    #print 'url len: {}'.format(len(urls))
    for i in range(len(urls)):
        t = URLThread(i, urls[i], corpus)
        threads.append(t)

    for j in range(len(threads) / no_threads):
        offset = no_threads * j    
        for t in threads[offset:offset +no_threads]:
            t.start()
        for t in threads[offset:offset + no_threads]:
            t.join()
    t1 = time()
    #print 'Time fetching urls: {}'.format(t1 - t0)
    return corpus

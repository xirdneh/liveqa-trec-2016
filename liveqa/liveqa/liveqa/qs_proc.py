from bs4 import BeautifulSoup
from time import time
from . import nltk_utils
import threading
import requests
import logging
import urllib2
import urllib
import json

logger = logging.getLogger(__name__)
ya_domain = 'https://answers.yahoo.com'
ya_search = 'https://answers.yahoo.com/search/search_result?p='
ya_new = 'https://answers.yahoo.com/dir/index/answer'
ya_list = 'https://answers.yahoo.com/dir/index/discover'

def get_question_details(q_url):
    response = requests.get(q_url)
    html = response.text
    soup = BeautifulSoup(html, 'html5lib')
    q_det = soup.find('div', id='ya-question-detail')
    title = q_det.h1.get_text()
    #q_det = q_det.find_all('div')
    body = q_det.find('span', class_='ya-q-full-text') or q_det.find('span', class_='ya-q-text')
    if body:
        body = body.get_text()
    else:
        body = ''
    best_answer = soup.find('div', id='ya-best-answer') or ''
    if best_answer:
        best_answer_txt = best_answer.find('span', class_='ya-q-full-text').get_text()
        refs = best_answer.find_all('span', class_='ya-ans-ref-text')
        if refs:
            refs = ' '.join([r.get_text() for r in refs])
        best_answer = best_answer_txt + ' ' + refs

    answers_ul = soup.find('ul', id='ya-qn-answers')
    answers = []
    if answers_ul:
        answers_lis = answers_ul.find_all('li')
        answers = []
        for answer in answers_lis:
            answer_dets = answer.select('.answer-detail')
            text = answer_dets[0].get_text()
            refs = answer.find_all('span', class_='ya-ans-ref-text')
            if refs:
                refs = ' '.join([r.get_text() for r in refs])
            else:
                refs = ''    
            text = text + ' ' + refs
            upvotes = answer_dets[1].select('[itemprop="upvoteCount"]')[0].get_text()
            upvotes = int(upvotes)
            answers.append({'answer': text, 'upvotes': upvotes})
        answers = sorted(answers, key=lambda x: x['upvotes'], reverse=True)
        if not best_answer:
            if answers:
                best_answer = answers[0]['answer']
                answers = answers[1:]        
    return {'title': title, 'body': body, 'best_answer': best_answer, 'answers': answers, 'url': q_url}


def question_to_document(q):
    doc = q['title'] + ' ' + q['body'] + ' ' +  q['best_answer']
    at = ''
    for answer in q['answers']:
        at += ' ' + answer['answer']
    return doc + ' ' + at

def get_newest_question():
    response = urllib2.urlopen('https://answers.yahoo.com/dir/index/answer', timeout=10)
    html = response.read()
    soup = BeautifulSoup(html, 'html5lib')
    questions = soup.find('ul', id='ya-answer-tab')
    q_url = ya_domain + questions.li.h3.a['href']
    return q_url

def search(q, q_url, dictionary):
    cnt = 0
    q_split = []
    qs_lis = []
    for w in q.split():
        freq = dictionary.dfs.get(dictionary.token2id.get(w, ''), 0)
        q_split.append((w, freq))
    q_split = sorted(q_split, key=lambda x: x[1], reverse=True)
    cnt_max = len(q_split) * 2
    p = 1 
    bw = False
    qid = q_url.split('qid=')[1].strip()
    while not bw:
        logger.debug('YA Search Q: %s &s=%s' % (q, p))
        s_url = ya_search + urllib.quote(q)
        if p > 1:
            s_url += '&s=%d' % p
        response = urllib2.urlopen(s_url, timeout=10)
        html = response.read()
        soup = BeautifulSoup(html, 'html5lib')
        web = soup.find('div', id = 'web')
        qs = web.find_all('ol')[1]
        lis = qs.find_all('li')
        qs_lis += lis
        #print 'len qs_lis {}'.format(len(qs_lis))
        if len(qs_lis) >= 50 or cnt >= cnt_max:
            bw = True
        if len(lis) < 10 and p == 1 and len(q_split) >= 3:
            #print 'fixing q'
            q = ' '.join([w for w in q.split() if w != q_split[-1][0]])
            q_split.pop()
            p = 0
        elif len(lis) < 10:
            bw = True
        cnt += 1
        p += 1
    seen = set()
    ret = []
    for li in qs_lis:
        url = ya_domain + li.h3.a['href']
        ref_qid = url.split('qid=')[1]
        #print 'qid: {} == ref_qid: {}. {}'.format(qid, ref_qid, qid == ref_qid)
        if qid == ref_qid or ref_qid in seen:
            continue
        seen.add(ref_qid)
        ret.append(url)
    return ret

def search_questions(q, q_url, dictionary):
    urls = search(q, q_url, dictionary)
    qs_dets = [{}] * len(urls)
    t0 = time()
    threads = []
    no_threads = 10
    #print 'url len: {}'.format(len(urls))
    for i in range(len(urls)):
        t = QThread(i, urls[i], qs_dets)
        threads.append(t)

    lth = len(threads)
    r = lth / no_threads if lth >= no_threads else lth
    for j in range(r):
        offset = no_threads * j
        end = offset + no_threads
        if offset + no_threads > len(urls):
            end = len(urls)
        for t in threads[offset:end]:
            t.start()
        for t in threads[offset:end]:
            t.join()
    t1 = time()
    #print 'Time fetchings candidates qs: {}'.format(t1 - t0)
    return qs_dets

class QThread(threading.Thread):
    def __init__(self, _id, url, texts, *args, **kwargs):
        threading.Thread.__init__(self)
        self._id = _id
        self.url = url
        self.texts = texts

    def _get_art(self, url):
        return get_question_details(url)

    def run(self):
        det = self._get_art(self.url)
        #logger.debug('det: {}'.format(det['best_answer']))
        if det['best_answer'] or det['answers']:
            self.texts[self._id] = det


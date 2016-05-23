from bs4 import BeautifulSoup
#from matplotlib import pyplot as plt
from urllib2 import HTTPError
from nltk.stem.wordnet import WordNetLemmatizer
from scipy.stats import entropy
from numpy.linalg import norm
from gensim import corpora, models, similarities, matutils
from requests.auth import HTTPBasicAuth
from time import time
from six import iteritems
import threading
import requests
import sys, traceback
import urllib2
import urllib
import sys
import nltk
import numpy as np
import re
import json
import random

from .liveqa import websearch
from .liveqa import nltk_utils
from .liveqa import qs_proc

k_topics = 80
ya_qurl = 'https://answers.yahoo.com/question/index?qid='
ya_new = 'https://answers.yahoo.com/dir/index/answer'
ya_list = 'https://answers.yahoo.com/dir/index/discover'
ya_search = 'https://answers.yahoo.com/search/search_result?p='
ya_domain = 'https://answers.yahoo.com'
bing_api = 'https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web?$format=json&Query='
bing_key = 'IgVbvvtgQVYI7Yfu9hPgVx0Tmbih1gq5lFOXaIQH4f8'

user_agent = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'

RESETC = '\033[0:0m'
BLACK = '\033[0:30m'
RED = '\033[0:31m'
GREEN = '\033[0:32m'
YELLOW = '\033[0:33m'
BLUE = '\033[0:34m'
PURPLE = '\033[0:35m'
CYAN = '\033[0:36m'
WHITE = '\033[0:37m'

def calc_jsd(p, q):
    """
    Calculate JSD
    """
    _P = np.zeros(k_topics, dtype=np.double)
    _Q = np.zeros(k_topics, dtype=np.double)
    ti = 0
    for i in range(k_topics):
        if i == p[ti][0]:
            _P[i] = p[ti][1]
            if len(p) - 1 > ti:
                ti += 1
    ti = 0
    for i in range(k_topics):
        if i == q[ti][0]:
            _Q[i] = q[ti][1]
            if len(q) - 1> ti:
                ti += 1

    _P = _P / norm(_P, ord=1)
    _Q = _Q / norm(_Q, ord=1)
    _M = 0.5 * (_P + _Q)
    return 0.5 * (entropy(_P, _M) + entropy(_Q, _M))

def get_similarity(model, dictionary, doc1, doc2):
    #dictionary, model = get_lda_model(fname)
    doc1 = nltk_utils.get_word_lists([doc1])[0]
    doc1_bow = dictionary.doc2bow(doc1)
    doc1_lda = model[doc1_bow]

    doc2 = nltk_utils.get_word_lists([doc2])[0]
    doc2_bow = dictionary.doc2bow(doc2)
    doc2_lda = model[doc2_bow]


    jsd = calc_jsd(doc1_lda, doc2_lda)
    return jsd

def get_id2word(token2id):
    id2word = {}
    for i, v in enumerate(token2id.keys()):
        id2word[token2id[v]] = v
    return id2word

def get_lda_model(documents):

    #data = ''
    #with open(fname, 'r') as f:
    #    data = f.read()
    #    data = data.decode('utf-8', errors = 'ignore')

    #documents = split_doc(data)
    word_lists = nltk_utils.get_word_lists(documents)
    #print word_lists
    #vocab = get_vocab(word_lists)
    dictionary = corpora.Dictionary(word_lists)
    dictionary.filter_extremes(no_below=2, no_above=0.8)
    id2word = dict((v, k) for k, v in iteritems(dictionary.token2id))
    #get_id2word(dictionary.token2id)
    doc2bow_vecs = []
    for l in word_lists:
        vec = dictionary.doc2bow(l)
        doc2bow_vecs.append(vec)
    model = models.LdaModel(doc2bow_vecs, 
                            id2word=id2word, 
                            alpha='auto', 
                            num_topics=k_topics)
    return dictionary, model

def main():
    q_url = qs_proc.get_newest_question()
    print q_url
    overall_t0 = time()
    #Get question's details 
    q_det = qs_proc.get_question_details(q_url)

    print GREEN + 'Question Details: ' + RESETC
    print '\t Url: %s' % q_det['url']
    print '\t %sTitle: %s%s' % (GREEN, q_det['title'], RESETC)
    print '\t Body: %s' % q_det['body']
    #print '\t Answer: %s\n\n' % q_det['best_answer']

    #Process title of the question
    q_title_proc = nltk_utils.get_word_lists(
                     [nltk_utils.preprocess_text(q_det['title'])])[0]

    #Add first word of the question to the processed title
    #We'll use this as our query string and usually, in english, the first 
    #word of a question is very important e.g. (Why, How, Which)
    q_title_proc = q_det['title'].split()[0] + ' ' + ' '.join(set(q_title_proc))

    #print 'Title Processed: {}\n\n'.format(q_title_proc)
    q_doc = qs_proc.question_to_document(q_det)
    q_doc = nltk_utils.preprocess_text(q_doc)

    urls = websearch.search('\'' + q_title_proc + '\'', q_url)
    documents_text = []

    #print '%s Fetching document from the web search %s\n' % (PURPLE, RESETC)
    documents_text = websearch.get_articles(urls)
    documents_text.append(q_doc)

    t0 = time()
    dictionary, model = get_lda_model(documents_text)
    t1 = time()
    #print 'time creating lda model: {}'.format(t1 - t0)

    #print '\n%s Document\'s probability distribution %s\n' % (PURPLE, RESETC)
    #topics = model.show_topics(num_topics=25, num_words=10)
    #for t in topics:
    #    print t

    
    qs_details = qs_proc.search_questions(q_title_proc, q_url, dictionary)
    #print '%s Calculating JSD for each related question %s\n' % (PURPLE, RESETC)
    t0 = time()
    related_qs = []
    for q in qs_details:
        if not q:
            continue
        doc = qs_proc.question_to_document(q)
        doc = nltk_utils.preprocess_text(doc)
        #print 'doc: %s' % doc
        #print 'q_doc: %s' % q_doc
        jsd = get_similarity(model, dictionary, q_doc, doc)
        related_qs.append({'jsd': jsd, 'q': q})
    related_qs = sorted(related_qs, key=lambda x: x['jsd'])
    t1 = time()
    #print 'time calculating JSDs {}'.format(t1 - t0)

    top_q = {}
    #for q in related_qs:
    #    if  len(q['q']['best_answer']) > 10 and len(q['q']['best_answer']) < 1000:
    #        top_q = q
    #        break
    #if not top_q:
    #    top_q = related_qs[0]
    top_q = related_qs[0]


    jsd = top_q['jsd']
    title = top_q['q']['title']
    best_answer = top_q['q']['best_answer']
    print 'JSD: {}'.format(jsd)
    try:
        print 'Best related question: {}'.format(title)
    except:
        print 'Best related question: {}'.format(title.decode('utf-8'))
    try:
        print '{}Best Answer: {}{}'.format(GREEN, best_answer, RESETC)
    except:
        try:
            print '{}Best Answer: {}{}'.format(GREEN, best_answer.decode('utf-8', errors='ignore'), RESETC)
        except:
            print '{}Best Answer: {}{}'.format(GREEN, best_answer.encode('utf-8', errors='ignore'), RESETC)
    print top_q['q']['url']
    print '\n\n'
    overall_t1 = time()
    #print 'Overall time: {}'.format(overall_t1 - overall_t0)
    return {'oq':q_det, 'answer': top_q, 'time': overall_t1 - overall_t0}

def run(q_id, q_category, q_title, q_body):
    #q_url = qs_proc.get_newest_question()
    #print q_url
    q_url = ya_qurl + q_id
    overall_t0 = time()

    #q_det = qs_proc.get_question_details(q_url)
    q_det = {
        'title': q_title,
        'body': q_body,
        'best_answer': '',
        'answers': '',
        'url': q_id,
        'id': q_id,
        'category': q_category
    }

    q_title_proc = nltk_utils.get_word_lists(
                     [nltk_utils.preprocess_text(q_det['title'])])[0]

    q_title_proc = q_det['title'].split()[0] + ' ' + ' '.join(set(q_title_proc))

    q_doc = qs_proc.question_to_document(q_det)
    q_doc = nltk_utils.preprocess_text(q_doc)

    urls = websearch.search('\'' + q_title_proc + '\'', q_url)
    documents_text = []

    documents_text = websearch.get_articles(urls)
    documents_text.append(q_doc)

    t0 = time()
    dictionary, model = get_lda_model(documents_text)
    t1 = time()
    
    qs_details = qs_proc.search_questions(q_title_proc, q_url, dictionary)
    t0 = time()
    related_qs = []
    for q in qs_details:
        if not q:
            continue
        doc = qs_proc.question_to_document(q)
        doc = nltk_utils.preprocess_text(doc)
        jsd = get_similarity(model, dictionary, q_doc, doc)
        related_qs.append({'jsd': jsd, 'q': q})
    related_qs = sorted(related_qs, key=lambda x: x['jsd'])
    t1 = time()
    top_q = {}
    top_q = related_qs[0]


    jsd = top_q['jsd']
    title = top_q['q']['title']
    best_answer = top_q['q']['best_answer']
    overall_t1 = time()
    return {'oq':q_det, 'answer': top_q, 'time': overall_t1 - overall_t0}



if __name__ == '__main__':
    main()

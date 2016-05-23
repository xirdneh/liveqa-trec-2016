from bs4 import BeautifulSoup
#from matplotlib import pyplot as plt
from urllib2 import HTTPError
from nltk.stem.wordnet import WordNetLemmatizer
from scipy.stats import entropy
from numpy.linalg import norm
from gensim import corpora, models, similarities, matutils
from requests.auth import HTTPBasicAuth
from time import time
import threading
import requests
import sys, traceback
import urllib2
import urllib
import sys
import lda
import nltk
import numpy as np
import re
import json
import random
import ipdb

k_topics = 120
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

    #d1 = _P*np.log2(2*_P/(_P+_Q))
    #d2 = _Q*np.log2(2*_Q/(_P+_Q))
    #d1[np.isnan(d1)] = 0
    #d2[np.isnan(d2)] = 0
    #d = 0.5*np.sum(d1+d2)    
    #return d

def write_article(url, fname):
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html5lib')
    [s.extract() for s in soup(['script', 'a', 'rel', 'style', 'img'])]
    text = soup.get_text().lower()
    text = re.sub(r'^https?:\/\/.*[\r\n]*', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s]+', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text, flags=re.MULTILINE)
    text = text.encode('utf-8')
    f = open(fname, 'w+')
    f.write(text)
    f.flush()
    f.close()
    return

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'https?:\/\/[.\s]*', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s\-_]+', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text, flags=re.MULTILINE)
    #text = re.sub(r'\W\s[\d]{1,3}\s', ' ', text, flags=re.MULTILINE)
    text = text.encode('utf-8')
    return text

def get_article(url):
    req = urllib2.Request(url, headers={'User-Agent': user_agent})
    response = urllib2.urlopen(req, timeout=10)
    html = response.read()
    soup = BeautifulSoup(html, 'html5lib')
    [s.extract() for s in soup(['script', 'a', 'rel', 'style', 'img', 'link', 'style'])]
    text = soup.get_text()
    text = preprocess_text(text)
    return text

def get_newest_question():
    response = urllib2.urlopen('https://answers.yahoo.com/dir/index/answer', timeout=10)
    html = response.read()
    soup = BeautifulSoup(html, 'html5lib')
    questions = soup.find('ul', id='ya-answer-tab')
    q_url = ya_domain + questions.li.h3.a['href']
    return q_url

def get_question_details(q_url):
    response = urllib2.urlopen(q_url, timeout = 10)
    html = response.read()
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
        best_answer = best_answer.find('span', class_='ya-q-full-text').get_text()

    answers_ul = soup.find('ul', id='ya-qn-answers')
    answers = []
    if answers_ul:
        answers_lis = answers_ul.find_all('li')
        answers = []
        for answer in answers_lis:
            answer_dets = answer.select('.answer-detail')
            text = answer_dets[0].get_text()
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

def search_questions(q, q_url, dictionary):
    qs_details = []
    qs_lis = []
    cnt = 0
    q_split = []
    for w in q.split():
        freq = dictionary.dfs.get(dictionary.token2id.get(w, ''), 0)
        q_split.append((w, freq))
    q_split = sorted(q_split, key=lambda x: x[1])
    print q_split
    cnt_max = len(q_split) * 2
    p = 1 
    bw = False
    qid = q_url.split('qid=')[1].strip()
    while not bw:
        print 'YA Search Q: %s &s=%s' % (q, p)
        s_url = ya_search + urllib.quote(q)
        if p > 1:
            s_url += '&s=%d' % p
        response = urllib2.urlopen(s_url, timeout=10)
        html = response.read()
        soup = BeautifulSoup(html, 'html5lib')
        qs = soup.find('ul', id = 'yan-questions')
        lis = qs.find_all('li')
        qs_lis += lis
        #print 'len qs_lis {}'.format(len(qs_lis))
        if len(qs_lis) >= 50 or cnt >= cnt_max:
            bw = True
        if len(lis) < 10 and p == 1 and len(q_split) >= 3:
            print 'fixing q'
            q = ' '.join([w for w in q.split() if w != q_split[0][0]])
            q_split.pop()
            p = 0
        elif len(lis) < 10:
            bw = True
        cnt += 1
        p += 1
    seen = set()
    prnt = True
    for li in qs_lis:
        url = ya_domain + li.a['href']
        ref_qid = url.split('qid=')[1]
        #print 'qid: {} == ref_qid: {}. {}'.format(qid, ref_qid, qid == ref_qid)
        if qid == ref_qid or ref_qid in seen:
            continue
        seen.add(ref_qid)
        #print 'Getting details for %s' % url
        try:
            q_det = get_question_details(url)
            if q_det['answers'] or q_det['best_answer']:
                qs_details.append(q_det)
                if prnt:
                    print 'details: {} '.format(qs_details)
                    prnt = False
        except Exception as e:
            print e
            traceback.print_exc(file=sys.stdout)
    return qs_details

def web_search(q, q_url):
    search_url = bing_api + urllib.quote(q)
    print 'Search Url: %s\n' % search_url
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
        print e
        print response.text
        traceback.print_exc(file=sys.stdout)

def split_doc(data, word_limit = 20):
    data = data.split()
    documents = ['']
    doc_index = 0
    word_count = 0
    for w in data:
        if len(documents) - 1 < doc_index:
            documents.append('')
        documents[doc_index] += (w + ' ')
        word_count += 1
        if word_count >= word_limit:
            doc_index += 1
    return documents

def get_word_lists(documents):
    """
    Use also to preprocess any string.
    text = get_word_lists([data])[0]
    """
    word_lists = []
    for d in documents:
        tokens = tokenize(d)
        tokens = remove_stop_words(tokens)
        word_lists.append(tokens)
    return word_lists

def count_token_ocurrance(documents):
    vocab = get_vocab(word_lists)
    dtm = get_count_matrix(vocab, word_lists)
    return vocab, dtm

def tokenize(text):
    tokens = nltk.word_tokenize(text)
    return tokens

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def remove_stop_words(tokens_list):
    stopwords = nltk.corpus.stopwords.words('english')
    stopwords += ['http', 'https', 'img', 'src', 'href', 'alt']
    lmtz = WordNetLemmatizer()
    filtered_words = [lmtz.lemmatize(w) for w in tokens_list if w not in stopwords and (is_int(w) or len(w) > 1)]
    return filtered_words

def get_id2word(token2id):
    id2word = {}
    for i, v in enumerate(token2id.keys()):
        id2word[token2id[v]] = v
    return id2word

def get_vocab(token_lists):
    vocab = set()
    for l in token_lists:
        vocab.update(l)
    return list(vocab)

def get_lda_model(documents):

    #data = ''
    #with open(fname, 'r') as f:
    #    data = f.read()
    #    data = data.decode('utf-8', errors = 'ignore')

    #documents = split_doc(data)
    word_lists = get_word_lists(documents)
    #print word_lists
    #vocab = get_vocab(word_lists)
    dictionary = corpora.Dictionary(word_lists)
    dictionary.filter_extremes(no_below=2, no_above=0.8)
    id2word = get_id2word(dictionary.token2id)
    doc2bow_vecs = []
    for l in word_lists:
        vec = dictionary.doc2bow(l)
        doc2bow_vecs.append(vec)
    model = models.LdaModel(doc2bow_vecs, id2word=id2word, alpha='auto', num_topics=k_topics)
    return dictionary, model

def get_bow(fname):
    data = ''
    with open(fname, 'r') as f:
        data = f.read()
        data = data.decode('utf-8', errors = 'ignore')
    doc = get_word_lists([data])
    return doc[0]

def get_similarity(model, dictionary, doc1, doc2):
    #dictionary, model = get_lda_model(fname)
    doc1 = get_word_lists([doc1])[0]
    doc1_bow = dictionary.doc2bow(doc1)
    doc1_lda = model[doc1_bow]

    doc2 = get_word_lists([doc2])[0]
    doc2_bow = dictionary.doc2bow(doc2)
    doc2_lda = model[doc2_bow]


    jsd = calc_jsd(doc1_lda, doc2_lda)
    #print 'doc_lda: {}, \n doc2_lda: {}'.format(doc1_lda, doc2_lda)
    #print 'jsd: {}'.format(jsd)
    #index = similarities.MatrixSimilarity(doc1_lda)
    #sims = index[doc2_lda]
    #print 'Sims: {}'.format(sims)
    return jsd

def main(q_url):
        #q_url = args[0]
        q_det = get_question_details(q_url)
        print GREEN + 'Question Details: ' + RESETC
        print '\t Url: %s' % q_det['url']
        print '\t %sTitle: %s%s' % (GREEN, q_det['title'], RESETC)
        print '\t Body: %s' % q_det['body']
        print '\t Answer: %s\n\n' % q_det['best_answer']

        #for k, v in q_det.iteritems():
        #    if k != 'answers':
        #        print '**%s**: %s' % (k, v)
        #    else:
        #        print '**answers**:\n'
        #        for o in v:
        #            print '%s\n+%s' % (o['answer'], o['upvotes'])
        #            print '---------------'

        q_title_proc = get_word_lists([preprocess_text(q_det['title'])])[0]
        q_title_proc = q_det['title'].split()[0] + ' ' + ' '.join(set(q_title_proc))
        print 'Title Processed: {}\n\n'.format(q_title_proc)
        q_doc = question_to_document(q_det)
        q_doc = preprocess_text(q_doc)

        urls = web_search('\'' + q_title_proc + '\'', q_url)
        documents_text = []
        print '%s Fetching document from the web search %s\n' % (PURPLE, RESETC)
        t0 = time()
        for url in urls:
            print url
            try:
                text = get_article(url)
                documents_text.append(text)
            except Exception as e:
                print e
                traceback.print_exc(file=sys.stdout)
        if q_det['body']:
            documents_text.append(q_title_proc + ' ' + ' '.join(get_word_lists(preprocess_text(q_det['body']))[0]) )
        documents_text.append(q_title_proc)
        t1 = time()
        print 'time getting urls: {}'.format(t1 - t0)
        t0 = time()
        dictionary, model = get_lda_model(documents_text)
        t1 = time()
        print 'time creating lda model: {}'.format(t1 - t0)
        #print 'Dictionary {}: '.format(dictionary)
        #print 'Model {}: '.format(model)
        print '\n%s Document\'s probability distribution %s\n' % (PURPLE, RESETC)
        topics = model.show_topics(num_topics=25, num_words=10)
        for t in topics:
            print t

        #topics_words = []
        ##add random smoothing.
        #sort_alpha = model.alpha + 0.0001 * np.random.rand(len(model.alpha))
        #sorted_topics = list(matutils.argsort(sort_alpha))
        #chosen_topics = sorted_topics[:5 // 2] + sorted_topics[-5 // 2:]
        #
        ##ipdb.set_trace()
        #f, ax = plt.subplots(5, 1, figsize = (8, 6), sharex=True)
        #for i, k in enumerate(chosen_topics): 
        #    ax[i].stem([o[1] for o in model.show_topic(k, topn=20000)], linefmt = 'b-',
        #                markerfmt = 'bo', basefmt='w-')
        #    ax[i].set_xlim(-50, dictionary.num_nnz / 2)
        #    ax[i].set_ylim(0, .08)
        #    ax[i].set_ylabel('Prob')
        #    ax[i].set_title('Topic #{}'.format(k))
        #ax[4].set_xlabel('Word')
        #plt.tight_layout()
        #plt.show()


        #f, ax = plt.subplots(5, 1, figsize = (8, 6), sharex=True)
        #for i, k in enumerate([0, 4, 9, 14, 19]):
        #    doc_bow = get_word_lists(documents_text[i])
        #    ax[i].stem([o[1] for o in model.get_document_topics(doc_bow)[0]], linefmt = 'r-',
        #        markerft='ro', basefmt='w-')
        #    ax[i].set_xlim(-1, k_topics)
        #    ax[i].set_ylim(0, .08)
        #    ax[i].set_ylabel('Prob')
        #    ax[i].set_title('Document {}'.format(k))
        #ax[4].set_xlabel('Topic')
        #plt.tight_layout()
        #plt.show()

        print '%s Fetching candidate related questions %s\n' % (PURPLE, RESETC)
        t0 = time()
        qs_details = search_questions(q_title_proc, q_url, dictionary)
        jsd = 100.0
        related_qs = []
        t1 = time()
        print 'time fetching candidates: {}'.format(t1 - t0)
        print '%s Calculating JSD for each related question %s\n' % (PURPLE, RESETC)
        t0 = time()
        for q in qs_details:
            doc = question_to_document(q)
            doc = preprocess_text(doc)
            #print 'doc: %s' % doc
            #print 'q_doc: %s' % q_doc
            jsd_t = get_similarity(model, dictionary, q_doc, doc)
            related_qs.append({'jsd': jsd_t, 'q': q})
        related_qs = sorted(related_qs, key=lambda x: x['jsd'])
        t1 = time()
        print 'time in lda {}'.format(t1 - t0)

        print '%s Printing top 5 related question/answer pairs %s\n' % (PURPLE, RESETC)
        for i in range(5):
            rq = related_qs[i]
            jsd = rq['jsd']
            title = rq['q']['title']
            best_answer = rq['q']['best_answer']
            print '{}Question #{}{}'.format(GREEN, i, RESETC)
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
            print rq['q']['url']
            print '\n\n'

        #f, ax = plt.subplots(6, 1, figsize = (8, 6), sharex=True)
        #for i, k in enumerate([0, 1, 2, 3, 4]):
        #    #doc_bow = get_word_lists(related_qs[i]['q']['title'] + )
        #    doc = question_to_document(related_qs[i]['q'])
        #    doc = preprocess_text(doc)
        #    ax[i].stem([o[1] for o in model.get_document_topics(get_word_lists(doc))[0]], linefmt = 'r-',
        #        markerft='ro', basefmt='w-')
        #    ax[i].set_xlim(-1, k_topics)
        #    ax[i].set_ylim(0, .08)
        #    ax[i].set_ylabel('Prob')
        #    ax[i].set_title('Document {}'.format(k))

        #ax[5].stem([o[1] for o in model.get_document_topics(get_word_lists(q_doc))[0]], linefmt = 'r-',
        #    markerft='ro', basefmt='w-')
        #ax[5].set_xlim(-1, k_topics)
        #ax[5].set_ylim(0, .08)
        #ax[5].set_ylabel('Prob')
        #ax[5].set_title('Document {}'.format('query'))
        #ax[5].set_xlabel('Topic')
        #plt.tight_layout()
        #plt.show()



if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == 'write':
        url = args[1]
        fname = args[2]
        write_article(url, fname)
    elif args and args[0] == 'lda':
        fname = args[1]
        fname_1 = args[2]
    else:
        if args:
            fname = args[0]
            qs_urls = []
            with open(fname, 'r') as f:
                qs_urls = f.readlines()
            for q_url in qs_urls:
                q_url = ya_domain + '/question/index?qid=' + q_url
                print q_url               
                try:
                    main(q_url)
                except HTTPError as e:
                    print e
                r = raw_input("Do you want to continue? ")
                if r.lower() == 'n':
                    break
        else:
            r = ''
            while r.lower() != 'n':
                q_url = get_newest_question()
                print q_url  
                try:
                    main(q_url)
                except HTTPError as e:
                    print e
                r = raw_input("Do you want to continue? ")

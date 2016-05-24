from bs4 import BeautifulSoup
import urllib2
import sys
import lda
import nltk
import numpy as np
import re
from nltk.stem.wordnet import WordNetLemmatizer
from scipy.stats import entropy
from numpy.linalg import norm

def calc_jsd(p, q):
    _P = P / norm(P, ord=1)
    _Q = Q / norm(Q, ord=1)
    _M = 0.5 * (_P + _Q)
    return 0.5 * (entropy(_P, _M) + entropy(_Q, _M))

def write_article(url, fname):
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html5lib')
    [s.extract() for s in soup(['script', 'a', 'rel', 'style', 'img'])]
    text = soup.get_text().lower()
    text = re.sub(r'^https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s]+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text, flags=re.MULTILINE)
    text = text.encode('utf-8')
    f = open(fname, 'w+')
    f.write(text)
    f.flush()
    f.close()
    return

def get_word_lists(documents):
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

def remove_stop_words(tokens_list):
    stopwords = nltk.corpus.stopwords.words('english')
    lmtz = WordNetLemmatizer()
    filtered_words = [lmtz.lemmatize(w) for w in tokens_list if w not in stopwords]
    return filtered_words

def get_vocab(token_lists):
    vocab = set()
    for l in token_lists:
        vocab.update(l)
    return list(vocab)

def get_count_matrix(vocab, tokens_lists):
    dtm = np.zeros((len(tokens_lists), len(vocab)), dtype=np.intc)
    for doc_index, l in enumerate(tokens_lists):
        for token in l:
            try:
                token_index = vocab.index(token)
                dtm[doc_index, token_index] += 1
            except ValueError:
                pass
    return dtm

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

if __name__ == '__main__':
    args = sys.argv[1:]
    #url = args[0]
    fname = args[0]
    fname_1 = args[1]
    #write_article(url, fname)


    data = ''
    with open(fname, 'r') as f:
        data = f.read()
        data = data.decode('utf-8', errors = 'ignore')
    documents = split_doc(data)
    #print 'documents: {} - {}'.format(len(documents), documents[0])
    word_lists = get_word_lists(documents)
    vocab = get_vocab(word_lists)
    dtm = get_count_matrix(vocab, word_lists)
    #print 'vocab {}'.format(vocab)
    np.set_printoptions(threshold = 'nan')
    #print 'dtm {}'.format(dtm)
    #print dtm.shape
    model = lda.LDA(n_topics = 20, n_iter = 1500, random_state = 1)
    model.fit(dtm)
    topic_word = model.topic_word_
    topic_word = np.argsort(topic_word)
    n_top_words = 11 
    for i, topic_dist in enumerate(topic_word):
        topic_words = np.array(vocab)[topic_dist][:-n_top_words:-1]
        print('Topic {}: {}'.format(i, ' '.join(topic_words).encode('utf-8')))

    print 'probs matrix: {}'.format(model.loglikelihoods_)
    with open(fname_1, 'r') as f:
        data = f.read()
        data = data.decode('utf-8', errors = 'ignore')
    documents = split_doc(data)
    word_lists = get_word_lists(documents)
    dtm = get_count_matrix(vocab, word_lists)
    doc_topic = model.transform(dtm, max_iter = 200)
    doc_topic = np.argsort(doc_topic)
    print 'Second doc \n\n\n\n\n\n'
    for i, topic_dist in enumerate(doc_topic):
        topic_words = np.array(vocab)[topic_dist][:-n_top_words:-1]
        print('Topic {}: {}'.format(i, ' '.join(topic_words).encode('utf-8')))

    print 'probs matrix: {}'.format(model.loglikelihoods_)

from nltk.stem.wordnet import WordNetLemmatizer
import nltk
import re

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'https?:\/\/[.\s]*', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s\-_]+', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text, flags=re.MULTILINE)
    #text = re.sub(r'\W\s[\d]{1,3}\s', ' ', text, flags=re.MULTILINE)
    text = text.encode('utf-8')
    return text

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

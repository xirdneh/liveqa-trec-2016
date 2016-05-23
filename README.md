# LiveQA submission for TREC-2016

**Introduction**
    
    This project is based on the [TREC-2016 track LiveQA](https://sites.google.com/site/trecliveqa2016/call-for-participation).
    In the heart of it uses Latent Dirichlet Allocation (LDA) to infer the semantic topics and uses this model to construct
    a probability distribution for each of the retrieved documents from the knowledge base. Finally the Jensen-Shannon
    Distance (JSD) is calculated to have a symilarity measure and the most similar answer is selected as the returned answer.
    The knowledge base used right now is the yahoo answers database. 

Leverages on:

  - [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
  - [scipy](https://pypi.python.org/pypi/scipy)
  - [numpy](https://pypi.python.org/pypi/numpy)
  - [nltk](http://www.nltk.org/)
  - [gensim](http://radimrehurek.com/gensim/)

## Future Work

  * [ ] Add more resources other than YahooAnswers.
  * [ ] Improve query construction when searching for candidate question/answer tuples.
  * [ ] Add more similarity metrics (aggregation, semantic).
  * [ ] Improve NLP processing.
  * [ ] Add multi-document summarization when possible.

## References 
  
  - [TREC-2016 track LiveQA](https://sites.google.com/site/trecliveqa2016/call-for-participation) 
  - [Blei et al. Latent Dirichlet Allocation](http://www.cs.princeton.edu/~blei/papers/BleiNgJordan2003.pdf)
  - [Gensim LDA implementation](https://github.com/piskvorky/gensim/blob/develop/gensim/models/ldamodel.py)

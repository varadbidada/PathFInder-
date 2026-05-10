import math, re
from typing import List, Dict, Any
from collections import Counter

def _tokenize(text):
    return re.findall(r'\b[a-zA-Z]\w+\b', text.lower())

class EmbeddingSearch:
    def __init__(self):
        self._docs = []
        self._tfidf_matrix = []
        self._idf = {}

    def index(self, documents: List[Dict[str, Any]]):
        self._docs = documents
        self._build_tfidf()

    def _build_tfidf(self):
        N = len(self._docs)
        if not N:
            return
        tf_list = [Counter(_tokenize(d.get("text", ""))) for d in self._docs]
        df = Counter()
        for tf in tf_list:
            for term in tf:
                df[term] += 1
        self._idf = {t: math.log((N+1)/(f+1))+1 for t, f in df.items()}
        self._tfidf_matrix = []
        for tf in tf_list:
            total = sum(tf.values()) or 1
            self._tfidf_matrix.append({t: (c/total)*self._idf.get(t,1.0) for t,c in tf.items()})

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self._docs:
            return []
        q_tokens = _tokenize(query_text)
        q_total = len(q_tokens) or 1
        q_tf = Counter(q_tokens)
        q_vec = {t: (c/q_total)*self._idf.get(t,1.0) for t,c in q_tf.items()}
        scored = []
        for i, doc_vec in enumerate(self._tfidf_matrix):
            score = self._cosine(q_vec, doc_vec)
            if score > 0:
                result = dict(self._docs[i])
                result["score"] = round(score, 4)
                scored.append(result)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cosine(a, b):
        dot = sum(a.get(k,0)*v for k,v in b.items())
        na = math.sqrt(sum(v**2 for v in a.values())) or 1e-9
        nb = math.sqrt(sum(v**2 for v in b.values())) or 1e-9
        return dot/(na*nb)

    def add_document(self, doc):
        self._docs.append(doc)
        self._build_tfidf()

    def clear(self):
        self._docs = []
        self._tfidf_matrix = []
        self._idf = {}

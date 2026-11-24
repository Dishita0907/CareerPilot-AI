import json
import os
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

DATA = json.loads((Path(__file__).resolve().parents[1]/"data/jobs.json").read_text())

class Search:
    def __init__(self):
        self.jobs = DATA["jobs"]
        docs = [f"{j['title']} {j['title']} {' '.join(j['skills'])}" for j in self.jobs]
        if os.getenv("EMBEDDING_PROVIDER","local") == "openai":
            from langchain_openai import OpenAIEmbeddings
            model = OpenAIEmbeddings(model="text-embedding-3-small")
            vectors = model.embed_documents(docs)
            self.encode = model.embed_query
        else:
            tfidf = TfidfVectorizer(ngram_range=(1,2),strip_accents="unicode")
            matrix = tfidf.fit_transform(docs)
            svd = TruncatedSVD(n_components=min(96,min(matrix.shape)-1),random_state=42)
            vectors = svd.fit_transform(matrix)
            self.encode = lambda query: svd.transform(tfidf.transform([query]))[0]
        vectors = np.ascontiguousarray(vectors,dtype="float32")
        faiss.normalize_L2(vectors)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def rank(self, profile, query):
        text = " ".join([profile["goal"],query,*profile["skills"]])
        vec = np.ascontiguousarray([self.encode(text)],dtype="float32")
        faiss.normalize_L2(vec)
        distances, indices = self.index.search(vec,len(self.jobs))
        results = []
        for sim, i in zip(distances[0],indices[0]):
            j = self.jobs[i]
            missing = sorted(set(j["skills"])-set(profile["skills"]))
            factors = {"semantic": (0.45,max(0,min(1,float(sim))))}
            if j["skills"] and profile["skills"]:
                factors["skills"] = (.30,1-len(missing)/len(j["skills"]))
            if profile["years"] is not None and j["years"] is not None:
                factors["experience"] = (.15,min(1,profile["years"]/max(1,j["years"])) if j["years"] else 1)
            if profile["location"].strip():
                loc = lambda s:s.lower().replace("bangalore","bengaluru")
                factors["location"] = (.10,float(loc(profile["location"].strip()) in loc(j["location"])))
            score=sum(w*v for w,v in factors.values()) / sum(w for w,v in factors.values())
            results.append(dict(**j,score=round(100*score,1),missing=missing,
                factors={k:round(v*100) for k,(_,v) in factors.items()}))
        return sorted(results,key=lambda j:(-j["score"],j["id"]))[:5]

@lru_cache(maxsize=1)
def search():
    return Search()

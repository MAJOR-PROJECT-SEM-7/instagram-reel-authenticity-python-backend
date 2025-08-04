from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.IndexFlatL2(384)
doc_texts = []

def embed_and_search(docs, query):
    global doc_texts
    doc_texts = [doc['text'][:1000] for doc in docs]  # truncate for speed
    embeddings = model.encode(doc_texts)
    index.add(np.array(embeddings))

    q_embed = model.encode([query])
    D, I = index.search(np.array(q_embed), k=5)
    
    return [doc_texts[i] for i in I[0]]

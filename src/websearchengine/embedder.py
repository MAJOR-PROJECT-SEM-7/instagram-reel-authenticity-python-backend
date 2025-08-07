from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

model = SentenceTransformer('all-MiniLM-L6-v2')
nn_model = None
doc_texts = []
embeddings_cache = None

def embed_and_search(docs, query):
    global doc_texts, nn_model, embeddings_cache
    doc_texts = [doc['text'][:1000] for doc in docs]
    
    if len(doc_texts) == 0:
        return []
    
    embeddings_cache = model.encode(doc_texts)
    
    nn_model = NearestNeighbors(
        n_neighbors=min(5, len(doc_texts)), 
        metric='cosine'
    )
    nn_model.fit(embeddings_cache)
    
    q_embed = model.encode([query])
    distances, indices = nn_model.kneighbors(q_embed)
    
    return [doc_texts[i] for i in indices[0] if 0 <= i < len(doc_texts)]

# No additional installation needed - sklearn comes with most Python setups

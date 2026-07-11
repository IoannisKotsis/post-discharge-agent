# Import necessary modules
import chromadb

# Open a new Chromadb connection
client = chromadb.PersistentClient("../chroma_db")
collection = client.get_or_create_collection("diabetes_guidelines")

# Return relative chunks

def retrieve(question, n_results=3):
    relative_chunks = collection.query(query_texts=[question], n_results=n_results)
    
    documents_list = relative_chunks['documents'][0]
    metadatas_list = relative_chunks['metadatas'][0]
    
    results = []
    for doc, meta in zip(documents_list, metadatas_list):
        doc_meta = {'text': doc, 'source': meta['source']}
        results.append(doc_meta)
    
    return results
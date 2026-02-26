# Handle embeddings and ChromaDB storage
import chromadb
from chromadb.config import Settings
from typing import List, Dict
from config import settings as app_settings

class VectorStore:
    def __init__(self, persist_directory: str = app_settings.CHROMA_PERSIST_DIR):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = None
    
    def create_collection(self, name: str = app_settings.COLLECTION_NAME):
        # Delete if exists? We'll just get or create
        self.collection = self.client.get_or_create_collection(name=name)
    
    def add_chunks(self, chunks: List[Dict], metadata: dict = None):
        """Add chunks to collection with embeddings."""
        if not self.collection:
            self.create_collection()
        
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [{"start_word": chunk['start_word'], "end_word": chunk['end_word'], **(metadata or {})} for chunk in chunks]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def retrieve_context(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieve relevant chunks."""
        if not self.collection:
            return []
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    
    def delete_collection(self):
        if self.collection:
            self.client.delete_collection(self.collection.name)
            self.collection = None
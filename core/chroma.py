import chromadb
from uuid import uuid4

class ChromaDB():
    def __init__(self, page):
        self.page = page
        self.client = chromadb.PersistentClient(path="./vectors")
        self.collection = self.client.get_or_create_collection(name=f'{page.id}')
        
    def add_embeddings(self, texts, embeddings=None):
        """
        Adds a list of embedding vectors for the given text list to the ChromaDB collection.
        """
        if self.collection.count() > 0:
            self.client.delete_collection(name=f'{self.page.id}')
            self.collection = self.client.get_or_create_collection(name=f'{self.page.id}')
        
        documents = [line for line in texts.split('\r\n')]
        if embeddings is None:
            embeddings = []
        try:

            self.collection.add(
                documents=documents,
                ids=[str(uuid4()) for _ in range(len(documents))],
            )
            print("Done: ", self.collection.count())
            return True
        except Exception as e:
            print(e)
        
        return False
        
    def query(self, text, k=5):
        r = self.collection.query(
            query_texts=[text],
            n_results=k,
            include=["documents", "distances"]
        )
        print(r)
        return r["documents"]
    
    def delete(self):
        self.collection.delete()
        
        
        
    
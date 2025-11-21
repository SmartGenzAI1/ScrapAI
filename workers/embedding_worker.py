import asyncio
from sentence_transformers import SentenceTransformer
import chromadb
from backend.database.client import DatabaseClient
from backend.config import config

class EmbeddingWorker:
    def __init__(self):
        self.db = DatabaseClient()
        self.model = SentenceTransformer(config.embedding.model)
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="web_content",
            metadata={"description": "Web content embeddings"}
        )
        
    async def process_embeddings(self):
        """Process pages that need embeddings"""
        while True:
            try:
                # Get pages without embeddings
                pages = await self.db.get_pages_without_embeddings(limit=config.embedding.batch_size)
                
                if not pages:
                    await asyncio.sleep(30)
                    continue
                    
                # Generate embeddings
                texts = [page['content'] for page in pages if page['content']]
                if texts:
                    embeddings = self.model.encode(texts).tolist()
                    
                    # Store in ChromaDB
                    self.collection.add(
                        embeddings=embeddings,
                        documents=texts,
                        metadatas=[{
                            'page_id': page['id'],
                            'url': page['url'],
                            'title': page.get('title', '')
                        } for page in pages],
                        ids=[page['id'] for page in pages]
                    )
                    
                    # Mark as processed
                    for page in pages:
                        await self.db.mark_embedding_generated(page['id'])
                        
                    print(f"Generated embeddings for {len(pages)} pages")
                    
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"Embedding worker error: {str(e)}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    worker = EmbeddingWorker()
    asyncio.run(worker.process_embeddings())

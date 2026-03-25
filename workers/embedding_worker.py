import asyncio
from sentence_transformers import SentenceTransformer
from backend.database.client import DatabaseClient
from backend.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingWorker:
    def __init__(self):
        self.db = DatabaseClient()
        self.model = SentenceTransformer(config.embedding.model)
        
    async def process_embeddings(self):
        """Process chunks that need embeddings"""
        while True:
            try:
                # Get chunks without embeddings
                chunks = await self.db.get_chunks_without_embeddings(limit=config.embedding.batch_size)
                
                if not chunks:
                    logger.info("No chunks needing embeddings, waiting...")
                    await asyncio.sleep(30)
                    continue
                    
                # Generate embeddings
                texts = [chunk['chunk_text'] for chunk in chunks if chunk['chunk_text']]
                if texts:
                    embeddings = self.model.encode(texts).tolist()
                    
                    # Store embeddings in database
                    for i, chunk in enumerate(chunks):
                        if i < len(embeddings):
                            await self.db.save_embedding(chunk['id'], embeddings[i])
                    
                    # Mark chunks as processed
                    for chunk in chunks:
                        await self.db.mark_chunk_embedded(chunk['id'])
                        
                    logger.info(f"Generated embeddings for {len(chunks)} chunks")
                    
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Embedding worker error: {str(e)}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    worker = EmbeddingWorker()
    asyncio.run(worker.process_embeddings())

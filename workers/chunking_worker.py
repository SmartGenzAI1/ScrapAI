"""
Chunking Worker for ScrapAI
Processes stored pages and creates text chunks for embedding
"""

import asyncio
import logging
from backend.database.client import DatabaseClient
from backend.utils.chunker import TextChunker
from backend.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChunkingWorker:
    def __init__(self):
        self.db = DatabaseClient()
        self.chunker = TextChunker(
            chunk_size=getattr(config.chunking, 'chunk_size', 500),
            overlap=getattr(config.chunking, 'overlap', 50)
        )
    
    async def process_chunks(self):
        """Process pages that need chunking"""
        while True:
            try:
                # Get pages that have content but no chunks
                pages = await self.db.get_pages_needing_chunking(limit=config.chunking.batch_size)
                
                if not pages:
                    logger.info("No pages needing chunking, waiting...")
                    await asyncio.sleep(30)
                    continue
                
                total_chunks = 0
                for page in pages:
                    try:
                        if not page.get('content'):
                            continue
                            
                        # Create chunks from page content
                        chunks = self.chunker.chunk_by_sentences(page['content'])
                        
                        # Save each chunk to database
                        for i, chunk in enumerate(chunks):
                            chunk_id = await self.db.save_chunk(
                                page_id=page['id'],
                                chunk_text=chunk.text,
                                chunk_index=i
                            )
                            if chunk_id:
                                total_chunks += 1
                        
                        logger.info(f"Created {len(chunks)} chunks for page {page['id']}: {page['url']}")
                        
                    except Exception as e:
                        logger.error(f"Error processing page {page.get('id')}: {e}")
                        continue
                
                logger.info(f"Created {total_chunks} total chunks from {len(pages)} pages")
                
                # Wait before next batch
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Chunking worker error: {str(e)}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    worker = ChunkingWorker()
    asyncio.run(worker.process_chunks())
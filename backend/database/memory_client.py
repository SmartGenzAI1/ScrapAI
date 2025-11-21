class MemoryClient:
    def __init__(self):
        self.queue = []
        self.pages = []
        self.processed = 0
        
    async def add_to_queue(self, url: str):
        if url not in [item['url'] for item in self.queue]:
            self.queue.append({
                'id': len(self.queue) + 1,
                'url': url,
                'status': 'queued'
            })
            return True
        return False
        
    async def get_next_queue_item(self):
        for item in self.queue:
            if item['status'] == 'queued':
                item['status'] = 'processing'
                return item
        return None
        
    async def save_page(self, data: dict):
        page_id = len(self.pages) + 1
        page_data = {
            'id': page_id,
            'url': data['url'],
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'hash': data.get('hash', '')
        }
        self.pages.append(page_data)
        return page_id
        
    async def is_duplicate(self, content_hash: str):
        return any(page['hash'] == content_hash for page in self.pages)
        
    async def mark_queue_processed(self, queue_id: str, status: str):
        for item in self.queue:
            if item['id'] == queue_id:
                item['status'] = status
                self.processed += 1
                break
                
    async def search_content(self, query: str, limit: int = 5):
        results = []
        for page in self.pages:
            if (query.lower() in page.get('title', '').lower() or 
                query.lower() in page.get('content', '').lower()):
                results.append(page)
            if len(results) >= limit:
                break
        return results
        
    async def get_stats(self):
        return {
            'queued': len([item for item in self.queue if item['status'] == 'queued']),
            'processed': self.processed,
            'pages': len(self.pages),
            'total': len(self.queue)
        }

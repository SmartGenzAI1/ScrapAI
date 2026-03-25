"""
Text chunking utility for ScrapAI
Splits text into smaller chunks for embedding processing
"""

import re
from typing import List
from dataclasses import dataclass

@dataclass
class TextChunk:
    text: str
    index: int
    start_char: int
    end_char: int

class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize the text chunker
        
        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_by_sentences(self, text: str) -> List[TextChunk]:
        """
        Chunk text by sentences, trying to keep chunks near target size
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        chunks = []
        current_chunk = ""
        current_start = 0
        sentence_index = 0
        
        for i, sentence in enumerate(sentences):
            # If adding this sentence would exceed chunk size and we have content
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk_end = current_start + len(current_chunk)
                chunks.append(TextChunk(
                    text=current_chunk.strip(),
                    index=len(chunks),
                    start_char=current_start,
                    end_char=chunk_end
                ))
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                current_start = chunk_end - len(overlap_text) if overlap_text else current_start + len(current_chunk)
            else:
                # Add sentence to current chunk
                if not current_chunk:
                    current_start = sum(len(s) + 1 for s in sentences[:i]) if i > 0 else 0
                current_chunk += (" " if current_chunk else "") + sentence
        
        # Add final chunk if there's content
        if current_chunk.strip():
            chunk_end = current_start + len(current_chunk)
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                index=len(chunks),
                start_char=current_start,
                end_char=chunk_end
            ))
        
        return chunks
    
    def chunk_by_fixed_size(self, text: str) -> List[TextChunk]:
        """
        Chunk text by fixed character size with overlap
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at a word boundary
            if end < len(text):
                # Look for space or punctuation to break cleanly
                while end > start and text[end] not in ' .,!?\n':
                    end -= 1
                
                # If we couldn't find a good break, use the original end
                if end == start:
                    end = start + self.chunk_size
            
            chunk_text = text[start:end]
            chunks.append(TextChunk(
                text=chunk_text,
                index=len(chunks),
                start_char=start,
                end_char=end
            ))
            
            # Move start position with overlap
            start = end - self.overlap
            if start >= len(text):  # Prevent infinite loop
                break
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk"""
        if len(text) <= self.overlap:
            return text
        return text[-self.overlap:].strip()

# Convenience functions
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50, method: str = "sentences") -> List[str]:
    """
    Convenience function to chunk text
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk
        overlap: Overlap between chunks
        method: Chunking method ("sentences" or "fixed")
        
    Returns:
        List of chunk text strings
    """
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
    
    if method == "sentences":
        chunks = chunker.chunk_by_sentences(text)
    else:
        chunks = chunker.chunk_by_fixed_size(text)
    
    return [chunk.text for chunk in chunks]

if __name__ == "__main__":
    # Test the chunker
    sample_text = """
    This is a sample text for testing the chunker. It contains multiple sentences.
    Each sentence should be handled appropriately. The chunker will try to keep
    chunks near the target size while respecting sentence boundaries.
    
    This is another paragraph. It shows how the chunker handles multiple paragraphs.
    The quick brown fox jumps over the lazy dog. This is a pangram used for testing.
    """
    
    chunker = TextChunker(chunk_size=100, overlap=20)
    
    print("Sentence-based chunking:")
    sentence_chunks = chunker.chunk_by_sentences(sample_text)
    for i, chunk in enumerate(sentence_chunks):
        print(f"Chunk {i}: {len(chunk.text)} chars - '{chunk.text[:50]}...'")
    
    print("\nFixed-size chunking:")
    fixed_chunks = chunker.chunk_by_fixed_size(sample_text)
    for i, chunk in enumerate(fixed_chunks):
        print(f"Chunk {i}: {len(chunk.text)} chars - '{chunk.text[:50]}...'")
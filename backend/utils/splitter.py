from typing import List, Dict

def split_text(text: str, chunk_size=800, overlap=100, metadata: Dict = None):
    """
    Split text into chunks with metadata tracking for source references.
    
    Args:
        text: The text to split
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        metadata: Document metadata (filename, page_number, etc.)
    
    Returns:
        List of dictionaries with 'text' and 'metadata' keys
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    if metadata is None:
        metadata = {}
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        # Create chunk with metadata
        chunk_data = {
            'text': chunk_text,
            'metadata': {
                **metadata,
                'chunk_index': chunk_index,
                'start_char': start,
                'end_char': end
            }
        }
        chunks.append(chunk_data)
        
        start += chunk_size - overlap
        chunk_index += 1
    
    return chunks


def split_text_by_pages(pages_text: List[str], chunk_size=800, overlap=100, base_metadata: Dict = None):
    """
    Split text from multiple pages while preserving page numbers.
    
    Args:
        pages_text: List of text strings, one per page
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        base_metadata: Base metadata (filename, etc.)
    
    Returns:
        List of dictionaries with 'text' and 'metadata' keys
    """
    all_chunks = []
    
    if base_metadata is None:
        base_metadata = {}
    
    for page_num, page_text in enumerate(pages_text, start=1):
        page_metadata = {
            **base_metadata,
            'page_number': page_num
        }
        
        page_chunks = split_text(page_text, chunk_size, overlap, page_metadata)
        all_chunks.extend(page_chunks)
    
    return all_chunks

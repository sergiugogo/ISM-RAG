"""
Batch processing system for handling large-scale document ingestion.
Supports concurrent processing and progress tracking.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import json
from datetime import datetime
from utils.pdf_loader import extract_text_by_pages, compute_file_hash
from utils.splitter import split_text_by_pages
from rag_engine import RAGEngine


class BatchProcessor:
    """
    Handles batch processing of documents with parallelization and progress tracking.
    """
    
    def __init__(
        self, 
        rag_engine: RAGEngine,
        max_workers: int = 4,
        batch_size: int = 100,
        processed_file_path: str = "processed_files.json"
    ):
        """
        Initialize the batch processor.
        
        Args:
            rag_engine: RAG engine instance for indexing
            max_workers: Number of parallel workers for processing
            batch_size: Number of chunks to process at once
            processed_file_path: Path to the processed files registry
        """
        self.rag_engine = rag_engine
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.processed_file_path = processed_file_path
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'total_chunks': 0,
            'start_time': None,
            'end_time': None
        }
    
    def load_processed_registry(self) -> Dict:
        """Load the registry of previously processed files."""
        if os.path.exists(self.processed_file_path):
            with open(self.processed_file_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save_processed_registry(self, registry: Dict):
        """Save the processed files registry."""
        with open(self.processed_file_path, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def process_single_file(self, file_path: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Process a single PDF file.
        
        Args:
            file_path: Path to the PDF file
            force_reprocess: If True, reprocess even if already indexed
            
        Returns:
            Dict with processing results
        """
        filename = os.path.basename(file_path)
        
        try:
            # Compute file hash
            file_hash = compute_file_hash(file_path)
            
            # Check if already processed
            registry = self.load_processed_registry()
            if not force_reprocess and filename in registry:
                stored_hash = registry[filename].get('hash')
                if stored_hash == file_hash:
                    return {
                        'filename': filename,
                        'status': 'skipped',
                        'reason': 'already_processed',
                        'chunks': registry[filename].get('chunk_count', 0)
                    }
            
            # Extract text by pages
            pages_text, page_count = extract_text_by_pages(file_path)
            
            # Split into chunks with metadata
            base_metadata = {
                'filename': filename,
                'total_pages': page_count,
                'file_path': file_path
            }
            chunks = split_text_by_pages(
                pages_text, 
                chunk_size=800, 
                overlap=100, 
                base_metadata=base_metadata
            )
            
            # Prepare documents for indexing
            documents_to_add = []
            for i, chunk_data in enumerate(chunks):
                doc_id = f"{filename}::{chunk_data['metadata'].get('page_number', 0)}::{i}"
                documents_to_add.append({
                    'text': chunk_data['text'],
                    'doc_id': doc_id,
                    'metadata': chunk_data['metadata']
                })
            
            # Add to vector database in batches
            for i in range(0, len(documents_to_add), self.batch_size):
                batch = documents_to_add[i:i + self.batch_size]
                self.rag_engine.add_documents_batch(batch)
            
            # Update registry
            registry[filename] = {
                'hash': file_hash,
                'chunk_count': len(chunks),
                'page_count': page_count,
                'processed_at': datetime.now().isoformat()
            }
            self.save_processed_registry(registry)
            
            return {
                'filename': filename,
                'status': 'success',
                'chunks': len(chunks),
                'pages': page_count
            }
            
        except Exception as e:
            return {
                'filename': filename,
                'status': 'failed',
                'error': str(e)
            }
    
    async def process_directory(
        self, 
        directory_path: str,
        file_pattern: str = "*.pdf",
        force_reprocess: bool = False,
        progress_callback: Callable[[Dict], None] = None
    ) -> Dict[str, Any]:
        """
        Process all files in a directory with parallel processing.
        
        Args:
            directory_path: Path to directory containing files
            file_pattern: Glob pattern for files to process
            force_reprocess: If True, reprocess all files
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with overall processing statistics
        """
        self.stats['start_time'] = datetime.now().isoformat()
        
        # Find all matching files
        path = Path(directory_path)
        files = list(path.glob(file_pattern))
        self.stats['total_files'] = len(files)
        
        print(f"[INFO] Found {len(files)} files to process")
        
        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for file_path in files:
                future = executor.submit(
                    self.process_single_file, 
                    str(file_path), 
                    force_reprocess
                )
                futures.append(future)
            
            # Collect results and update stats
            for i, future in enumerate(futures, 1):
                result = future.result()
                
                # Update statistics
                if result['status'] == 'success':
                    self.stats['processed_files'] += 1
                    self.stats['total_chunks'] += result.get('chunks', 0)
                elif result['status'] == 'skipped':
                    self.stats['skipped_files'] += 1
                elif result['status'] == 'failed':
                    self.stats['failed_files'] += 1
                
                # Progress callback
                if progress_callback:
                    progress = {
                        'current': i,
                        'total': len(files),
                        'result': result,
                        'stats': self.stats.copy()
                    }
                    progress_callback(progress)
                
                # Console output with status indicator
                status_prefix = {
                    'success': '[OK]',
                    'skipped': '[SKIP]',
                    'failed': '[ERROR]'
                }
                prefix = status_prefix.get(result['status'], '[?]')
                print(f"{prefix} [{i}/{len(files)}] {result['filename']} - {result['status']}")
        
        self.stats['end_time'] = datetime.now().isoformat()
        
        # Calculate processing duration
        start = datetime.fromisoformat(self.stats['start_time'])
        end = datetime.fromisoformat(self.stats['end_time'])
        duration = (end - start).total_seconds()
        
        print(f"\nProcessing Summary:")
        print(f"  Processed: {self.stats['processed_files']}")
        print(f"  Skipped: {self.stats['skipped_files']}")
        print(f"  Failed: {self.stats['failed_files']}")
        print(f"  Total Chunks: {self.stats['total_chunks']}")
        print(f"  Duration: {duration:.2f} seconds")
        
        return self.stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return self.stats.copy()


async def main():
    """Example usage of the batch processor."""
    from rag_engine import RAGEngine
    
    # Initialize RAG engine
    engine = RAGEngine()
    
    # Create batch processor
    processor = BatchProcessor(
        rag_engine=engine,
        max_workers=4,
        batch_size=100
    )
    
    # Process a directory
    stats = await processor.process_directory(
        directory_path="./uploads",
        file_pattern="*.pdf",
        force_reprocess=False
    )
    
    print(f"\n[SUCCESS] Batch processing complete: {stats}")


if __name__ == "__main__":
    asyncio.run(main())

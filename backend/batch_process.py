"""
Quick-start script for batch processing PDFs.
Run this to index your entire document collection.
"""

import asyncio
import argparse
import os
from pathlib import Path
from batch_processor import BatchProcessor
from rag_engine import RAGEngine
from config import RAGConfig


async def main():
    parser = argparse.ArgumentParser(
        description='Batch process PDFs for RAG system'
    )
    parser.add_argument(
        'directory',
        type=str,
        help='Directory containing PDF files to process'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for vector DB insertion (default: 100)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocess all files, even if already indexed'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.pdf',
        help='File pattern to match (default: *.pdf)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to YAML configuration file'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.exists(args.directory):
        print(f"[ERROR] Directory not found: {args.directory}")
        return
    
    # Load configuration
    if args.config:
        config = RAGConfig.from_yaml(args.config)
        print(f"[INFO] Loaded configuration from {args.config}")
    else:
        config = RAGConfig.from_env()
        print("[INFO] Loaded configuration from environment variables")
    
    print("\n" + "="*60)
    print("BATCH PROCESSING STARTED")
    print("="*60)
    print(f"Directory: {args.directory}")
    print(f"Workers: {args.workers}")
    print(f"Batch Size: {args.batch_size}")
    print(f"Force Reprocess: {args.force}")
    print(f"Vector DB: {config.vector_db.provider}")
    print(f"Embedding Model: {config.embedding.model_name}")
    print("="*60 + "\n")
    
    # Initialize RAG engine
    print("[INFO] Initializing RAG engine...")
    engine = RAGEngine()
    
    # Create batch processor
    processor = BatchProcessor(
        rag_engine=engine,
        max_workers=args.workers,
        batch_size=args.batch_size,
        processed_file_path=config.processed_files_path
    )
    
    # Progress callback
    def progress_callback(progress):
        current = progress['current']
        total = progress['total']
        result = progress['result']
        stats = progress['stats']
        
        # Print progress bar
        percentage = (current / total) * 100
        bar_length = 40
        filled = int(bar_length * current / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r[{bar}] {percentage:.1f}% | "
              f"✅ {stats['processed_files']} | "
              f"⏭️  {stats['skipped_files']} | "
              f"❌ {stats['failed_files']} | "
              f"📄 {stats['total_chunks']} chunks",
              end='', flush=True)
    
    # Process directory
    stats = await processor.process_directory(
        directory_path=args.directory,
        file_pattern=args.pattern,
        force_reprocess=args.force,
        progress_callback=progress_callback
    )
    
    print("\n\n" + "="*60)
    print("✅ BATCH PROCESSING COMPLETE")
    print("="*60)
    print(f"📊 Total Files: {stats['total_files']}")
    print(f"✅ Processed: {stats['processed_files']}")
    print(f"⏭️  Skipped: {stats['skipped_files']}")
    print(f"❌ Failed: {stats['failed_files']}")
    print(f"📄 Total Chunks: {stats['total_chunks']}")
    
    if stats['start_time'] and stats['end_time']:
        from datetime import datetime
        start = datetime.fromisoformat(stats['start_time'])
        end = datetime.fromisoformat(stats['end_time'])
        duration = (end - start).total_seconds()
        
        if stats['processed_files'] > 0:
            rate = stats['processed_files'] / (duration / 3600)  # files per hour
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print(f"🚀 Processing Rate: {rate:.1f} files/hour")
    
    print("="*60)
    
    # Recommendations
    if stats['failed_files'] > 0:
        print(f"\n⚠️  {stats['failed_files']} files failed to process.")
        print("   Check the logs above for error details.")
    
    if stats['processed_files'] == 0 and stats['skipped_files'] > 0:
        print("\n💡 All files were skipped (already processed).")
        print("   Use --force flag to reprocess all files.")
    
    print("\n✨ Your RAG system is ready to answer questions!")
    print("   Start the API server: python run_production.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

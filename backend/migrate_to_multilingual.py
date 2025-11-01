"""
Migration script to upgrade to multilingual embeddings model.
Removes old database and reindexes all documents with the new model.
"""
import os
import shutil
from reindex_all import reindex_all_documents

def migrate():
    """Migrate from monolingual to multilingual embeddings model."""
    print("Multilingual Model Migration (Romanian + English + 48 other languages)")
    print("=" * 80)
    
    # Remove old database with monolingual embeddings
    chroma_path = "../chroma_store"
    if os.path.exists(chroma_path):
        print(f"\n[INFO] Removing old database: {chroma_path}")
        shutil.rmtree(chroma_path)
        print("[OK] Old database removed")
    
    # Reindex all documents with new multilingual model
    print("\n[INFO] Reindexing documents with multilingual model...")
    print("   Model: paraphrase-multilingual-MiniLM-L12-v2")
    print("   Embedding dimension: 384 (unchanged)")
    print("   Language support: Romanian, English, + 48 other languages")
    print()
    
    reindex_all_documents()
    
    print("\n" + "=" * 80)
    print("[SUCCESS] Migration completed successfully!")
    print("\nBenefits:")
    print("   - English documents can be found with Romanian queries")
    print("   - Romanian documents can be found with English queries")
    print("   - Cross-lingual semantic search fully functional")
    print("\nYou can now test the system in the frontend interface")

if __name__ == "__main__":
    migrate()

if __name__ == "__main__":
    migrate()

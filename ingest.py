"""Ingest data to Qdrant Cloud - Run this once to populate the database."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Check credentials
print("=" * 60)
print("UniHelp - Data Ingestion to Qdrant Cloud")
print("=" * 60)
print()

# Verify environment variables
qdrant_url = os.getenv("QDRANT_URL")
qdrant_key = os.getenv("QDRANT_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if not qdrant_url:
    print("❌ QDRANT_URL not found in .env")
    sys.exit(1)

if not qdrant_key:
    print("❌ QDRANT_API_KEY not found in .env")
    sys.exit(1)

if not openai_key:
    print("❌ OPENAI_API_KEY not found in .env")
    sys.exit(1)

print("✅ Configuration OK")
print(f"   Qdrant URL: {qdrant_url[:50]}...")
print()

# Check Data folder
data_dir = Path("docs/Data")
if not data_dir.exists():
    print("Data folder not found!")
    sys.exit(1)

doc_count = len(list(data_dir.glob("*.txt")))
print(f"Found {doc_count} documents in docs/Data/")
print()

# Import and run ingestion
try:
    from src.ingest import IngestionPipeline

    print("Starting ingestion...")
    print("-" * 60)

    pipeline = IngestionPipeline()
    result = pipeline.ingest_directory("docs/Data", force_reindex=False)

    print()
    print("=" * 60)
    print("✅ INGESTION COMPLETE!")
    print("=" * 60)
    print(f"Files processed: {result['files_processed']}")
    print(f"Chunks created: {result['chunks_created']}")
    print(f"Total documents in Qdrant: {result['total_documents']}")
    print()
    print("You can now run: streamlit run app.py")

except Exception as e:
    print()
    print("=" * 60)
    print("❌ INGESTION FAILED!")
    print("=" * 60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

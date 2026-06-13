from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domains.ecommerce.adapter import load_ecommerce_documents
from app.pipeline.chunker import split_documents
from app.pipeline.vector_store import build_index


def main() -> None:
    documents = load_ecommerce_documents()
    chunks = split_documents(documents, chunk_size=220, overlap=20)
    index = build_index(chunks)

    document_types = sorted(
        {
            str(chunk.metadata.get("document_type"))
            for chunk in index.chunks
            if chunk.metadata.get("document_type")
        }
    )
    print(f"documents={len(documents)} chunks={len(index.chunks)}")
    print(f"document_types={','.join(document_types)}")


if __name__ == "__main__":
    main()

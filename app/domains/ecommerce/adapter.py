from pathlib import Path

from app.pipeline.document_loader import load_markdown_documents
from app.schemas.document import Document


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ECOMMERCE_DOCS_DIR = PROJECT_ROOT / "data" / "ecommerce" / "docs"


def get_policy_doc_paths(data_dir: str | Path = DEFAULT_ECOMMERCE_DOCS_DIR) -> list[Path]:
    docs_dir = Path(data_dir)
    if not docs_dir.exists():
        raise FileNotFoundError(f"Ecommerce docs directory does not exist: {docs_dir}")
    return sorted(docs_dir.glob("*.md"))


def load_ecommerce_documents(data_dir: str | Path = DEFAULT_ECOMMERCE_DOCS_DIR) -> list[Document]:
    return load_markdown_documents(data_dir)

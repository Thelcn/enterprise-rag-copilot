from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.schemas.document import Document


def load_markdown_documents(path: str | Path) -> list[Document]:
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Document path does not exist: {root}")

    if root.is_file():
        if root.suffix.lower() != ".md":
            raise ValueError(f"Expected a markdown file, got: {root}")
        markdown_files = [root]
        base_dir = root.parent
    else:
        markdown_files = sorted(root.rglob("*.md"))
        base_dir = root

    documents: list[Document] = []
    for file_path in markdown_files:
        content = file_path.read_text(encoding="utf-8").strip()
        relative_path = file_path.relative_to(base_dir).as_posix()
        documents.append(
            Document(
                id=_build_document_id(relative_path),
                source=file_path.name,
                content=content,
                metadata={
                    "source": file_path.name,
                    "path": relative_path,
                    "document_type": file_path.stem,
                    "file_extension": file_path.suffix.lower(),
                },
            )
        )

    return documents


def _build_document_id(relative_path: str) -> str:
    return f"doc_{uuid5(NAMESPACE_URL, relative_path).hex}"

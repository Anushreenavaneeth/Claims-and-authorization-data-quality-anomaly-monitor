from pathlib import Path
import json
from typing import List, Dict, Any


SUPPORTED_TEXT_EXTENSIONS = {
    ".md",
    ".txt",
}

SUPPORTED_JSON_EXTENSIONS = {
    ".json",
}


class DocumentLoader:
    """
    Loads RAG source documents from the documents directory.

    Supported formats:
    - Markdown
    - Text
    - JSON
    """

    def __init__(self, documents_dir: str = None):

        if documents_dir is None:
            documents_dir = (
                Path(__file__).resolve().parent / "documents"
            )

        self.documents_dir = Path(documents_dir)

    def load_all(self) -> List[Dict[str, Any]]:
        """
        Load all supported documents recursively.
        """

        documents = []

        if not self.documents_dir.exists():
            raise FileNotFoundError(
                f"Documents directory not found: "
                f"{self.documents_dir}"
            )

        for file_path in self.documents_dir.rglob("*"):

            if not file_path.is_file():
                continue

            if file_path.name.startswith("."):
                continue

            suffix = file_path.suffix.lower()

            if suffix in SUPPORTED_TEXT_EXTENSIONS:
                document = self._load_text(file_path)

            elif suffix in SUPPORTED_JSON_EXTENSIONS:
                document = self._load_json(file_path)

            else:
                continue

            if document:
                documents.append(document)

        return documents

    def _load_text(
        self,
        file_path: Path
    ) -> Dict[str, Any]:

        content = file_path.read_text(
            encoding="utf-8"
        )

        category = self._get_category(file_path)

        return {
            "document_id": file_path.stem,
            "file_name": file_path.name,
            "file_path": str(file_path),
            "document_type": file_path.suffix.lower().replace(
                ".",
                ""
            ),
            "category": category,
            "content": content,
            "metadata": {
                "source": file_path.name,
                "category": category,
                "file_path": str(file_path)
            }
        }

    def _load_json(
        self,
        file_path: Path
    ) -> Dict[str, Any]:

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid JSON file: {file_path}"
            ) from error

        category = self._get_category(file_path)

        return {
            "document_id": file_path.stem,
            "file_name": file_path.name,
            "file_path": str(file_path),
            "document_type": "json",
            "category": category,
            "content": json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            ),
            "metadata": {
                "source": file_path.name,
                "category": category,
                "file_path": str(file_path)
            }
        }

    def _get_category(
        self,
        file_path: Path
    ) -> str:

        try:

            relative_path = file_path.relative_to(
                self.documents_dir
            )

            parts = relative_path.parts

            if len(parts) > 1:
                return parts[0]

        except ValueError:
            pass

        return "uncategorized"


def load_documents(
    documents_dir: str = None
) -> List[Dict[str, Any]]:
    """
    Convenience function used by the embedding pipeline.
    """

    loader = DocumentLoader(
        documents_dir=documents_dir
    )

    return loader.load_all()


if __name__ == "__main__":

    loader = DocumentLoader()

    documents = loader.load_all()

    print("=" * 60)
    print("RAG DOCUMENT LOADER")
    print("=" * 60)

    print(
        f"Documents directory: "
        f"{loader.documents_dir}"
    )

    print(
        f"Documents loaded: {len(documents)}"
    )

    print()

    for document in documents:

        print(
            f"[{document['category']}] "
            f"{document['file_name']}"
        )
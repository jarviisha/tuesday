import re
import shutil
import subprocess
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from tuesday_rag.domain.errors import DocumentParseError, InvalidInputError
from tuesday_rag.domain.models import SourceDocument


class LocalFileDocumentParser:
    _SUPPORTED_EXTENSIONS = {".html", ".md", ".pdf", ".txt"}

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return set(cls._SUPPORTED_EXTENSIONS)

    @staticmethod
    def has_pdftotext() -> bool:
        return shutil.which("pdftotext") is not None

    def parse(self, raw_input: dict) -> SourceDocument:
        raw_path = raw_input.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise InvalidInputError("path must not be blank", details={"field": "path"})

        path = Path(raw_path).expanduser()
        if not path.exists():
            raise InvalidInputError("path does not exist", details={"field": "path"})
        if not path.is_file():
            raise InvalidInputError("path must point to a file", details={"field": "path"})
        if path.suffix.lower() not in self._SUPPORTED_EXTENSIONS:
            raise InvalidInputError(
                "path extension is not supported",
                details={"field": "path"},
            )

        metadata = raw_input.get("metadata") or {}
        resolved_path = path.resolve()
        extension = path.suffix.lower()
        title = raw_input.get("title")
        if extension == ".pdf":
            content = self._extract_pdf_text(resolved_path)
            title = title or resolved_path.stem
            source_type = "pdf"
        else:
            try:
                raw_content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise DocumentParseError("Failed to parse the source file") from exc
            if extension == ".html":
                parser = _HTMLTextExtractor()
                try:
                    parser.feed(raw_content)
                    parser.close()
                except Exception as exc:
                    raise DocumentParseError("Failed to parse the source file") from exc
                content = parser.text_content
                title = title or parser.title or resolved_path.stem
                source_type = "html"
            else:
                content = raw_content
                title = title or resolved_path.stem
                source_type = "text"
        return SourceDocument(
            document_id=raw_input["document_id"],
            title=title,
            content=content,
            source_type=source_type,
            source_uri=resolved_path.as_uri(),
            language=metadata.get("language"),
            metadata=metadata,
        )

    @staticmethod
    def _extract_pdf_text(path: Path) -> str:
        try:
            completed = subprocess.run(
                ["pdftotext", str(path), "-"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise DocumentParseError("Failed to parse the source file") from exc
        if completed.returncode != 0:
            raise DocumentParseError("Failed to parse the source file")
        return _normalize_extracted_text(completed.stdout)


class _HTMLTextExtractor(HTMLParser):
    _BLOCK_TAGS = {
        "article",
        "br",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "p",
        "section",
        "ul",
        "ol",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._ignored_tag_stack: list[str] = []
        self._title_parts: list[str] = []
        self._in_title = False

    @property
    def title(self) -> str | None:
        title = self._normalize_text(" ".join(self._title_parts))
        return title or None

    @property
    def text_content(self) -> str:
        return self._normalize_text("".join(self._parts))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_tag_stack.append(tag)
            return
        if self._ignored_tag_stack:
            return
        if tag == "title":
            self._in_title = True
        if tag in self._BLOCK_TAGS:
            self._parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self._ignored_tag_stack:
            if tag == self._ignored_tag_stack[-1]:
                self._ignored_tag_stack.pop()
            return
        if tag == "title":
            self._in_title = False
        if tag in self._BLOCK_TAGS:
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._ignored_tag_stack:
            return
        if self._in_title:
            self._title_parts.append(data)
        self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.handle_data(unescape(f"&#{name};"))

    @staticmethod
    def _normalize_text(raw_text: str) -> str:
        return _normalize_extracted_text(raw_text)


def _normalize_extracted_text(raw_text: str) -> str:
    text = raw_text.replace("\xa0", " ").replace("\x0c", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return text.strip()

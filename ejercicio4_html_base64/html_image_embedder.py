"""Convierte las imágenes locales referenciadas por tags <img> dentro de
archivos HTML a base64 (data URI), generando un archivo nuevo por cada HTML
procesado sin tocar el original.

Solo usa librerías estándar de Python (html.parser, base64, mimetypes,
pathlib, argparse, json).

Uso como script:
    python html_image_embedder.py archivo1.html carpeta_con_html/ ...

Uso como librería:
    from html_image_embedder import HtmlImageEmbedder
    result = HtmlImageEmbedder().process(["archivo.html", "carpeta/"])
    # result == {"success": {...}, "fail": {...}}
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


class HtmlFileCollector:
    """Resuelve una lista de rutas (archivos y/o directorios) a archivos .html."""

    def collect(self, paths: list[str]) -> list[Path]:
        html_files: list[Path] = []
        for raw_path in paths:
            path = Path(raw_path)
            if path.is_dir():
                html_files.extend(sorted(path.rglob("*.html")))
            elif path.is_file():
                html_files.append(path)
        return html_files


class ImageBase64Converter:
    """Lee un archivo de imagen local y lo convierte a data URI base64."""

    def to_data_uri(self, image_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(image_path.name)
        if mime_type is None or not mime_type.startswith("image/"):
            mime_type = "application/octet-stream"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"


@dataclass
class _ImgReplacement:
    start: int
    end: int
    new_tag_text: str


class _ImgTagScanner(HTMLParser):
    """Recorre el HTML y registra, para cada <img>, dónde está en el texto
    original y cuál sería la versión reescrita con el src en base64."""

    def __init__(self, html_dir: Path, converter: ImageBase64Converter):
        super().__init__(convert_charrefs=False)
        self.html_dir = html_dir
        self.converter = converter
        self.replacements: list[_ImgReplacement] = []
        self.success: list[str] = []
        self.fail: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return

        raw_tag_text = self.get_starttag_text()
        src = dict(attrs).get("src")
        if not src:
            return

        line, col = self.getpos()
        start = self._offset(line, col)
        end = start + len(raw_tag_text)

        new_src, error = self._resolve_src(src)
        if error:
            self.fail.append({"src": src, "error": error})
            return

        new_tag_text = self._replace_src_attr(raw_tag_text, src, new_src)
        self.replacements.append(_ImgReplacement(start, end, new_tag_text))
        self.success.append(src)

    def _resolve_src(self, src: str) -> tuple[str | None, str | None]:
        if src.startswith("data:"):
            return None, "la imagen ya está embebida en base64"
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", src):
            return None, "URL externa no soportada (solo imágenes locales)"

        image_path = (self.html_dir / src).resolve()
        if not image_path.is_file():
            return None, f"archivo de imagen no encontrado: {image_path}"

        try:
            return self.converter.to_data_uri(image_path), None
        except OSError as exc:
            return None, f"error leyendo la imagen: {exc}"

    @staticmethod
    def _replace_src_attr(raw_tag_text: str, old_src: str, new_src: str) -> str:
        pattern = re.compile(
            r'src\s*=\s*(["\'])' + re.escape(old_src) + r'\1'
        )
        return pattern.sub(f'src="{new_src}"', raw_tag_text, count=1)

    def _offset(self, line: int, col: int) -> int:
        """Convierte (línea, columna) de HTMLParser a un offset absoluto en
        self._source, usando los saltos de línea acumulados hasta esa línea."""
        return self._line_starts[line - 1] + col

    def feed(self, data: str) -> None:  # type: ignore[override]
        self._source = data
        self._line_starts = [0]
        for match in re.finditer("\n", data):
            self._line_starts.append(match.end())
        super().feed(data)


class HtmlImageEmbedder:
    """Orquesta la conversión de imágenes a base64 para uno o varios HTML."""

    def __init__(self, output_suffix: str = "_embedded"):
        self.output_suffix = output_suffix
        self.collector = HtmlFileCollector()
        self.converter = ImageBase64Converter()

    def process(self, paths: list[str]) -> dict:
        success: dict[str, list[str]] = {}
        fail: dict[str, list[dict]] = {}

        for html_path in self.collector.collect(paths):
            file_key = str(html_path)
            try:
                ok, errors = self._process_file(html_path)
            except OSError as exc:
                fail[file_key] = [{"src": None, "error": f"no se pudo leer el HTML: {exc}"}]
                continue

            if ok:
                success[file_key] = ok
            if errors:
                fail[file_key] = errors

        return {"success": success, "fail": fail}

    def _process_file(self, html_path: Path) -> tuple[list[str], list[dict]]:
        original_text = html_path.read_text(encoding="utf-8")

        scanner = _ImgTagScanner(html_dir=html_path.parent, converter=self.converter)
        scanner.feed(original_text)

        new_text = self._apply_replacements(original_text, scanner.replacements)
        if scanner.replacements:
            output_path = html_path.with_name(f"{html_path.stem}{self.output_suffix}{html_path.suffix}")
            output_path.write_text(new_text, encoding="utf-8")

        return scanner.success, scanner.fail

    @staticmethod
    def _apply_replacements(text: str, replacements: list[_ImgReplacement]) -> str:
        pieces: list[str] = []
        cursor = 0
        for repl in sorted(replacements, key=lambda r: r.start):
            pieces.append(text[cursor:repl.start])
            pieces.append(repl.new_tag_text)
            cursor = repl.end
        pieces.append(text[cursor:])
        return "".join(pieces)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="archivos .html y/o directorios a procesar")
    parser.add_argument("--output-suffix", default="_embedded")
    args = parser.parse_args()

    embedder = HtmlImageEmbedder(output_suffix=args.output_suffix)
    result = embedder.process(args.paths)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

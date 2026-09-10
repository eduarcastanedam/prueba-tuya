# Ejercicio 4 — Procesamiento de HTML (imágenes a base64)

Solo usa librerías estándar de Python (`html.parser`, `base64`, `mimetypes`,
`pathlib`, `argparse`, `json`, `dataclasses`).

## Uso

```bash
python html_image_embedder.py sample_html/                    # archivo(s) y/o carpeta(s), recursivo
python html_image_embedder.py sample_html/page1.html --output-suffix _b64
```

Devuelve por stdout (y como valor de retorno si se usa como librería) un objeto:

```json
{ "success": { "ruta/archivo.html": ["img/logo.png", "..."] },
  "fail":    { "ruta/archivo.html": [{"src": "img/roto.png", "error": "..."}] } }
```

Por cada HTML con al menos una imagen convertida se crea un archivo nuevo
`<nombre>_embedded.html` (sufijo configurable) junto al original, que **no se
modifica**.

## Diseño (POO)

- `HtmlFileCollector`: resuelve la lista de entradas (archivos y/o
  directorios) a archivos `.html`, recorriendo subdirectorios.
- `ImageBase64Converter`: lee un archivo de imagen y arma el data URI
  (`data:<mime>;base64,<...>`), infiriendo el `mime type` por extensión.
- `_ImgTagScanner` (subclase de `html.parser.HTMLParser`): localiza cada tag
  `<img src="...">` en el HTML original y, por posición (línea/columna →
  offset), calcula qué reemplazar sin tocar el resto del documento — así se
  preservan comentarios, doctype, indentación y cualquier otro tag intacto.
- `HtmlImageEmbedder`: orquesta collector + converter + scanner por archivo y
  agrega los resultados en el objeto `{success, fail}`.

## Casos manejados como `fail` (no rompen la ejecución)

- Imagen local no encontrada en disco.
- `src` que ya es un `data:` URI (nada que convertir).
- `src` con URL externa (`http(s)://...`): fuera de alcance porque el
  enunciado habla de imágenes "asociadas" al HTML (locales); no se hacen
  llamadas de red.

## Prueba incluida

`sample_html/` trae un caso de uso real para validar el script manualmente:
`page1.html` (con una imagen válida, una con extensión distinta a su
contenido real, una inexistente y una URL externa) y
`subcarpeta/page2.html` (para probar recursividad y rutas relativas `../`).

```bash
python html_image_embedder.py sample_html/
```

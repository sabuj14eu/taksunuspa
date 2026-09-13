# -*- coding: utf-8 -*-
"""Pull images out of the old site (or a folder) into the media library.

The previous site is still running on its own port, so the quickest way to
recover its photos is to read its pages and download what they reference.
Everything lands under the entity type `imported`, which shows in
Admin -> Photos; from there each photo is assigned to the hero, the gallery,
a product, a treatment or a therapist with one click.

    # from the old site still running on localhost
    python -m scripts.import_images --from-url http://127.0.0.1:5200

    # or from a folder of files you already have
    python -m scripts.import_images --from-dir /tmp/old-photos

Re-running is safe: an image already imported from the same source is skipped.
"""
import argparse
import io
import os
import re
import sys
from urllib.parse import urljoin, urlparse

import requests
from werkzeug.datastructures import FileStorage

from app import create_app
from app.extensions import db
from app.models.media import MediaImage
from app.services import media_service

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")
# src="...", data-src="...", and the og:image / twitter:image meta tags.
SRC_RE = re.compile(r'(?:src|data-src|data-lazy-src)\s*=\s*["\']([^"\']+)["\']',
                    re.I)
SRCSET_RE = re.compile(r'srcset\s*=\s*["\']([^"\']+)["\']', re.I)
META_IMG_RE = re.compile(
    r'<meta[^>]+(?:property|name)\s*=\s*["\'](?:og:image|twitter:image)["\']'
    r'[^>]+content\s*=\s*["\']([^"\']+)["\']', re.I)
LINK_RE = re.compile(r'href\s*=\s*["\'](/[^"\'#?]*)["\']', re.I)
CSS_URL_RE = re.compile(r'url\(\s*["\']?([^)"\']+)["\']?\s*\)', re.I)

MAX_PAGES = 40
TIMEOUT = 15


def looks_like_image(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(IMG_EXT)


def crawl(base_url: str):
    """Same-host pages, breadth first, collecting image URLs as we go."""
    base_url = base_url.rstrip("/")
    host = urlparse(base_url).netloc
    seen_pages, queue, images = set(), ["/"], []

    while queue and len(seen_pages) < MAX_PAGES:
        path = queue.pop(0)
        if path in seen_pages:
            continue
        seen_pages.add(path)
        url = urljoin(base_url + "/", path.lstrip("/"))
        try:
            r = requests.get(url, timeout=TIMEOUT)
        except requests.RequestException as exc:
            print(f"  ! {url}: {exc}", file=sys.stderr)
            continue
        if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
            continue
        html = r.text
        print(f"  read {path}")

        found = set(SRC_RE.findall(html)) | set(META_IMG_RE.findall(html))
        found |= set(CSS_URL_RE.findall(html))
        for chunk in SRCSET_RE.findall(html):
            for part in chunk.split(","):
                candidate = part.strip().split(" ")[0]
                if candidate:
                    found.add(candidate)

        for raw in found:
            if raw.startswith("data:"):
                continue
            absolute = urljoin(url, raw)
            if urlparse(absolute).netloc != host:
                continue
            if looks_like_image(absolute):
                images.append(absolute)

        for href in LINK_RE.findall(html):
            if href not in seen_pages and not href.startswith("//"):
                queue.append(href)

    # De-duplicate, keep order.
    return list(dict.fromkeys(images))


def already_imported():
    rows = MediaImage.query.filter(MediaImage.caption.like("imported:%")).all()
    return {r.caption[len("imported:"):].strip() for r in rows}


def store(stream_bytes: bytes, filename: str, source: str, entity_type: str,
          entity_id: int):
    fs = FileStorage(stream=io.BytesIO(stream_bytes), filename=filename)
    img, err = media_service.save_upload(fs, entity_type, entity_id)
    if err:
        print(f"  ! {filename}: {err}", file=sys.stderr)
        return None
    img.caption = f"imported:{source}"[:160]
    img.is_cover = False            # nothing becomes a cover automatically
    db.session.commit()
    return img


def from_url(base_url: str, entity_type: str, entity_id: int):
    print(f"Reading {base_url} ...")
    urls = crawl(base_url)
    print(f"Found {len(urls)} image URL(s).")
    done = already_imported()
    saved = skipped = failed = 0
    for url in urls:
        if url in done:
            skipped += 1
            continue
        try:
            r = requests.get(url, timeout=TIMEOUT)
            if r.status_code != 200 or not r.content:
                failed += 1
                continue
            name = os.path.basename(urlparse(url).path) or "image.jpg"
            if store(r.content, name, url, entity_type, entity_id):
                saved += 1
                print(f"  + {name}")
            else:
                failed += 1
                print(f"  ! rejected {name}", file=sys.stderr)
        except requests.RequestException as exc:
            failed += 1
            print(f"  ! {url}: {exc}", file=sys.stderr)
    return saved, skipped, failed


def from_dir(path: str, entity_type: str, entity_id: int):
    done = already_imported()
    saved = skipped = failed = 0
    for root, _dirs, files in os.walk(path):
        for name in sorted(files):
            if not name.lower().endswith(IMG_EXT):
                continue
            full = os.path.join(root, name)
            if full in done:
                skipped += 1
                continue
            try:
                with open(full, "rb") as fh:
                    data = fh.read()
                if store(data, name, full, entity_type, entity_id):
                    saved += 1
                    print(f"  + {name}")
                else:
                    failed += 1
            except OSError as exc:
                failed += 1
                print(f"  ! {full}: {exc}", file=sys.stderr)
    return saved, skipped, failed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-url", help="Old site's base URL, e.g. "
                                       "http://127.0.0.1:5200")
    ap.add_argument("--from-dir", help="Folder of image files to import")
    ap.add_argument("--as", dest="entity_type", default="imported",
                    help="Where to file them (default: imported)")
    ap.add_argument("--id", dest="entity_id", type=int, default=0,
                    help="Item id, for product/treatment/therapist")
    args = ap.parse_args()

    if not (args.from_url or args.from_dir):
        ap.error("give --from-url or --from-dir")

    app = create_app()
    with app.app_context():
        total = [0, 0, 0]
        if args.from_url:
            got = from_url(args.from_url, args.entity_type, args.entity_id)
            total = [a + b for a, b in zip(total, got)]
        if args.from_dir:
            got = from_dir(args.from_dir, args.entity_type, args.entity_id)
            total = [a + b for a, b in zip(total, got)]

        print(f"\nImported {total[0]}, already had {total[1]}, failed {total[2]}.")
        print("Open Admin -> Photos to see them, then use \"Move to\" on each "
              "photo to make it the hero, a gallery image, or an item's photo.")


if __name__ == "__main__":
    main()

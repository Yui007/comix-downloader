# Comix Downloader — Browser Free

A PyQt6/QML and CLI Comix downloader that signs and decrypts the current API in
pure Python. It uses curl_cffi for HTTP/TLS impersonation and does not launch a
browser.

This project is a fork of Yui007/comix-downloader. The upstream GUI, CLI,
exporters, and worker-pool experience are retained; see NOTICE.md and LICENSE
for attribution and licensing.

## What changed

- No nodriver, Chromium, page canvas extraction, cookie persistence, or manual
  Cloudflare challenge flow.
- The current public secure asset is fetched and statically parsed for every
  manga session.
- API requests receive the same signed query parameter as the site client.
- Encrypted API responses are decrypted by three Python substitution passes.
- Image and chapter downloads retain configurable bounded concurrency.
- GUI, interactive CLI, direct CLI, CBZ, PDF, image output, scanlator choice,
  range selection, and ComicInfo.xml remain available.

## Install

Requires Python 3.10 or newer.

~~~
git clone https://github.com/zgredex/comix-downloader.git
cd comix-downloader
python -m venv .venv
.venv/bin/pip install -r requirements.txt
~~~

## Use

GUI:

~~~
.venv/bin/python gui/main.py
~~~

Direct CLI:

~~~
.venv/bin/python main.py download \
  "https://comix.to/title/3ezr0-adopting-the-protagonist-changed-the-genre" \
  --chapters "38" --format cbz --output downloads
~~~

Interactive CLI:

~~~
.venv/bin/python main.py
~~~

The GUI and settings menu expose two limits:

- Max chapter workers: concurrent chapter jobs.
- Max image workers: concurrent image transfers per chapter.

Use conservative values if the image host starts rate limiting. The defaults
are three chapter workers and five image workers.

## Browser-free flow

~~~
title page -> main asset -> secure asset
           -> static Python table extraction
           -> signed API request
           -> Python response decryption
           -> bounded concurrent image downloads
           -> images, PDF, or CBZ
~~~

The current chapter request is signed with an asset-derived token in the _
query parameter. The implementation fails closed if the secure asset shape
changes instead of silently producing bad data.

The canonical maintainer/AI protocol reference is
[ARCHITECTURE.md](ARCHITECTURE.md). It explains the complete extraction,
`QHKXSH` handling, signing, response decryption, failure modes, and validation
procedure.

## Verification

~~~
.venv/bin/python -m unittest discover -v
~~~

Live browser-free validation performed on 2026-07-10:

- Manga metadata and 522 chapter entries fetched from the signed API.
- Chapter 38 decrypted to 92 page URLs.
- Five-worker download generated a valid CBZ with 92 WebPs and ComicInfo.xml.
- The QML GUI loaded successfully with the browser-free bridges.

## License

MIT. The upstream copyright notice is preserved in LICENSE.

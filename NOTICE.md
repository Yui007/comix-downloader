# Attribution and provenance

This repository is a fork of
[Yui007/comix-downloader](https://github.com/Yui007/comix-downloader), licensed
under the MIT License. The original copyright notice and full MIT license are
retained in LICENSE.

The PyQt6/QML interface, CLI workflow, format exporters, progress UI, and
bounded worker-pool structure originate from that project.

The browser automation path has been replaced in this fork with a browser-free
curl_cffi transport and a static Python implementation of the current Comix
secure-module request signing and response decryption flow. No nodriver,
Chromium, page rendering, canvas extraction, Cloudflare-cookie persistence, or
JavaScript runtime is used by the active download path.

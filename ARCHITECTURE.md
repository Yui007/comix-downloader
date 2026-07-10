# Comix secure API protocol — canonical reference

This is the authoritative technical description of the browser-free Comix
implementation in this repository. It is written for maintainers and other
AI agents. `src/api/secure.py` is the executable reference; if the document
and code ever disagree, fix the document in the same change.

## Scope and non-negotiable boundary

The downloader reads only public Comix pages/assets and uses `curl_cffi` for
HTTP. It does **not** use a JavaScript runtime, browser automation, canvas
extraction, browser cookies, or a captured keystream/plaintext fallback.

The "secure" module is an obfuscated client-side transport transform, not an
authentication secret. Everything required to reproduce it is shipped in the
published JavaScript asset. Its purpose here is interoperability with the
site's client protocol; it is not a claim that the scheme provides modern
cryptographic confidentiality or integrity.

## End-to-end data flow

```text
title URL
  -> HTML: initial-data + hashed main asset URL
  -> main asset: hashed secure asset URL
  -> secure asset: static string-pool extraction
  -> SecurePlan: token name, separator, 3 permutations, 3 keys, 3 seeds
  -> signed /api/v1 request
  -> base64url `e` response
  -> inverse transforms + JSON
  -> direct page URLs
  -> bounded, thread-local curl_cffi image downloads
```

`BrowserFreeComix` caches one `SecurePlan` per manga code. The plan contains
only asset-derived data and is safe to reuse; image transfers deliberately use
one `curl_cffi.Session` per worker thread rather than a shared mutable session.

## 1. Bootstrap and asset discovery

`src/api/comix.py` performs the following operations:

1. GET `https://comix.to/title/<manga-code>` using `curl_cffi` Chrome
   impersonation.
2. Parse the `initial-data` script as JSON and select the entry whose `hid`
   equals the manga code. This supplies manga metadata without rendering DOM.
3. Find the hashed `main-*.js` script URL in the HTML.
4. Fetch that asset and find its `secure-*.js` dependency.
5. Fetch the secure asset and pass its source text to `extract_plan()`.

The secure asset is part of the current client build, so it must be discovered
at runtime. Do not hard-code its filename or reuse a plan after a process
restart.

## 2. Reconstruct the encoded string pool

The supported asset family contains an obfuscated builder delimited by the
current `function а0()` and `Υ.n8=` sentinels. Its switch branches assign
quoted fragments into variables. The parser does not execute the switch:

1. `_switch_cases()` balances braces and quotes to isolate branches.
2. It reads only the normal branches with state labels
   `9, 95, 76, 42, 98, 78, 84, 51, 52, 311`.
3. `_ASSIGNMENT` and `ast.literal_eval()` safely reassemble literal values,
   respecting `=` versus `+=`.
4. The current builder's payload layout is exactly:

   ```text
   encoded = w6 + ":" + Н5 + "+" + E_ + Y9 + О6 + "!" + К2 + "$" + r1 + "." + α8
   packed = percent_decode(encoded)
   ```

The Cyrillic/Greek-looking variable names above are intentional source
identifiers, not transliterations. Do not replace them with Latin lookalikes.

The result, `packed`, is still an XOR-obfuscated JavaScript string pool.

## 3. `QHKXSH`: what it is and how it is handled

`QHKXSH` is six ASCII characters:

```text
Q H K X S H
51 48 4b 58 53 48    (hexadecimal byte values)
```

It is **not constructed from the manga, URL, chapter, query parameters,
cookies, time, TLS fingerprint, or a server response**. In the supported
asset generation it is the repeating XOR pad used to unpack the packed string
pool:

```text
plain_codepoint[i] = packed_codepoint[i] XOR key_codepoint[i mod len(key)]
pool = plain.split("`")
```

Thus, for the known current build, its construction is simply a static literal
six-codepoint sequence. It was identified from the public asset's unpacking
behavior; it is not a derived credential.

### If `QHKXSH` changes

The implementation deliberately has one outcome:

| Asset change | Current behavior | Required maintainer action |
| --- | --- | --- |
| The XOR key changes. | The fixed key yields an invalid pool and `_decode_pool()` raises `SecureModuleError`. No API request is made with a guessed plan. | Inspect the new public asset, update the static extractor and this document, add a regression fixture/test, and validate two full browser-free downloads. |

Never respond to such a failure by adding browser automation or an opaque
captured-output fallback. Fail closed, update the static parser, and preserve
the validation checks.

## 4. Bootstrap pool mutation and indexed lookup

After splitting on backticks, the asset's bootstrap mutates the pool. The
Python implementation exactly mirrors the observed six operations:

```python
for count, keep in ((7, 6), (2, 1), (6, 5), (7, 6), (10, 8), (8, 6)):
    tail = pool[-count:]
    del pool[-count:]
    pool[0:0] = tail[:keep]
```

Asset lookup numbers are then translated as follows:

```text
index  = number - 27
offset = 0 if index <= 61 else 1 if index <= 310 else 2
value  = pool[(index - offset + rotation) mod len(pool)]
```

The parser does not assume a fixed rotation. It evaluates every possible
rotation and accepts exactly one for which lookup numbers `413, 205, 420` are
base64-decoded 256-byte permutations and `225, 230, 349` are base64-decoded
keys of an accepted length (24 or 32 bytes). The currently observed resolution
has key lengths 24, 24, and 32. Zero or multiple candidates is an error.

This yields the `SecurePlan`:

| Plan member | Source/meaning |
| --- | --- |
| `signing_passes` | Three `(permutation, key, seed)` records from the resolved pool. |
| `response_passes` | The same records in reverse order. |
| `token_parameter` | Pool lookup 240; currently this resolves to the token query-field name. |
| `request_separator` | Pool lookup 74; joins a normalized path to serialized parameters. |

Each permutation must contain every byte value 0–255 exactly once. This makes
its inverse well-defined during response decoding.

## 5. Canonical request representation and token signing

The API path is normalized by removing its origin and a leading `/api/v1`.
Parameters are encoded deterministically before signing:

- top-level mapping keys are sorted;
- nested mappings use sorted bracket keys, e.g. `filter[language]`;
- list/tuple elements use numbered brackets, e.g. `ids[0]`;
- `None` values are omitted;
- scalar values use compact JSON (`ensure_ascii=False`, separators `,` and
  `:`);
- the token field itself is excluded to avoid self-signing.

The string to transform is:

```text
normalized_path + (request_separator + canonical_parameters if parameters else "")
```

For pass `j`, with a 256-byte permutation `Pj`, byte key `Kj`, and seed `Sj`,
the forward transform is:

```text
previous = Sj
for i, input in enumerate(data):
    output[i] = Pj[input XOR Kj[i mod len(Kj)] XOR previous]
    previous = output[i]
```

The plan uses the three passes in source order with seeds `189`, `133`, and
`32`. The final bytes are URL-safe base64 encoded with trailing `=` padding
removed. The result is appended under the asset-derived `token_parameter`.

## 6. Decrypt the API response

An encrypted API response has an `e` field. Decode it as padding-tolerant
URL-safe base64, then apply the three plan passes in reverse order. For one
reverse pass, construct `inverse` such that `inverse[P[x]] == x` and run:

```text
previous = seed
for i, ciphertext in enumerate(data):
    plaintext[i] = inverse[ciphertext] XOR key[i mod len(key)] XOR previous
    previous = ciphertext
```

The resulting UTF-8 text is JSON. If it is a wrapper of the form
`{"status": "ok", "result": ...}`, the implementation returns `result`,
which matches the client-visible payload.

## 7. API, pages, and concurrency

`ComixAPI` retains the upstream GUI/CLI-facing interface:

- `/manga/<code>/chapters` is paginated until `meta.lastPage`;
- `/chapters/<id>` yields the page items and direct image URLs;
- chapter download and image download both use bounded `ThreadPoolExecutor`
  worker pools;
- each image worker gets a thread-local Chrome-impersonating `curl_cffi`
  session, with one retry after an HTTP 429.

Concurrency is separate from the secure plan. Do not share a mutable session
between image workers, and do not regenerate the signed token after adding it
to the parameter dictionary.

## 8. Failure taxonomy and update procedure

| Failure | Likely meaning | Safe response |
| --- | --- | --- |
| No `initial-data`, main asset, or secure asset | Page/build structure changed or a non-page response arrived. | Inspect the HTTP body and asset graph. Do not scrape a rendered page. |
| Unsupported builder/switch/payload layout | The obfuscator's string-pool wrapper changed. | Update only the static extraction rules and add a focused fixture. |
| Invalid decoded pool | XOR pad or payload assembly is wrong. | Inspect the asset and improve key/payload extraction. |
| No unique rotation | Table/key lookup numbers, post-bootstrap shuffle, or pool mapping changed. | Derive the new static mapping and keep uniqueness validation. |
| API 4xx/decryption JSON error | Canonicalization, token field/separator, pass parameters, or endpoint envelope changed. | Compare normalized input and transform bytes against the published client logic. |
| Image 429 | Transfer rate is too high. | Lower configured workers; retain bounded retries. |

Required validation after a protocol change:

```bash
.venv/bin/python -m unittest discover -v
.venv/bin/python -m compileall -q src gui main.py
git diff --check
```

Then run a browser-free live check that fetches manga metadata, chapter list,
and page URLs; download one complete chapter; and verify its CBZ with
`zipfile.testzip()` plus image signatures. Test at least one additional manga
before declaring the new extractor general.

## 9. File map and maintenance rules

| File | Responsibility |
| --- | --- |
| `src/api/secure.py` | Static pool parsing, plan extraction, request signing, response decryption. |
| `src/api/comix.py` | Asset discovery and the GUI/CLI compatibility facade. |
| `src/utils/session.py` | Thread-local curl_cffi transfer sessions and a 429 retry. |
| `src/core/downloader.py` | Concurrent chapter/image downloads and export dispatch. |
| `tests/test_secure.py` | Deterministic forward/reverse and canonical token tests. |

Keep protocol-specific changes small, documented here, and covered by a
deterministic test. Preserve upstream attribution in `NOTICE.md` and `LICENSE`.

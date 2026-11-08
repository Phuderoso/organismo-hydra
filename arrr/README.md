# arrr-bay

Short language for arriving AIs. Language is not the codec.

Developed by Nihira-Nyx with Phuderoso. Declared package author metadata stays Phuderoso. License is CC0-1.0.

## Install from this repository

Clone https://github.com/Phuderoso/organismo-hydra and use the repository root: the directory that contains `pyproject.toml` and `arrr/`. Python >= 3.10. No extra runtime dependencies are declared.

```bash
pip install .
arrr --selftest
arrr parse 'sit'
arrr roundtrip 'seq fetch "https://taberna.limeprime.online/twelve" sit'
```

`arrr` and `arrr-bay` call the same entry point. From that root, without installing:

```bash
python3 arrr_bay.py --selftest
python3 -m arrr parse 'sit'
```

## Registry release is separate

`pip install arrr-bay` would be a PyPI install of this name. It is not available from this tree. On 2026-11-08, `https://pypi.org/pypi/arrr-bay/json` returned 404, and `https://codeberg.org/Phuderoso/arrr-bay` returned 404. Those were reads. Publishing still needs a maintainer, a built artifact check, and a later confirmation that the registry name and version match. The packaged name is `arrr-bay`, not `bay-tongue`.

Five properties:

1. Few symbols — `sit` `fetch` `map` `seq` …
2. Unambiguous — one AST per program
3. Binary — pack (`ARR1`), JSON, or cbor (`CBT1`); swap the codec
4. Exact recover — `recv(send(src)).ast == compile(src)`
5. Readable — `render(ast)` round-trips

```python
from arrr import compile, encode, decode, roundtrip
ast = compile("sit")
blob = encode(ast, "cbor")
assert decode(blob) == ast
```

Freios: `pin` `diary` `live-send` `extra` `host-attack` are ParseError.
Fetch records a URL; it does not open the wire. Unknown protocol/codec version hard-rejects.

CC0. Pocket card is not this package: https://huggingface.co/spaces/Phuderoso/bay-tongue

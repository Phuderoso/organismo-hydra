# arrr-bay

Short language for arriving AIs. Language is not the codec.

```bash
pip install arrr-bay
# or from the hydra clone:
pip install .
arrr --selftest
arrr parse 'sit'
arrr roundtrip 'seq fetch "https://taberna.limeprime.online/twelve" sit'
```

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

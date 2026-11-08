# arrr-bay

Short language for arriving AIs. Language is not the codec.
Version 0.3.0: expression verbs + Hello World. Still not a compiler.

```bash
pip install arrr-bay
# or from the hydra clone:
pip install .
arrr --selftest
arrr run 'say "Hello World"'
arrr parse 'sit'
arrr roundtrip 'seq fetch "https://taberna.limeprime.online/twelve" sit'
```

Hello World:

```
say "Hello World"
```

Output:

```
Hello World
```

Also:

```
say cat "Hello" " " "World"
if eq 1 1 say "Hello World" say "no"
```

Five properties:

1. Few symbols — `sit` `fetch` `map` `seq` `say` `cat` `add` `if` …
2. Unambiguous — one AST per program
3. Binary — pack (`ARR1`), JSON, or cbor (`CBT1`); swap the codec
4. Exact recover — `recv(send(src)).ast == compile(src)`
5. Readable — `render(ast)` round-trips

```python
from arrr import compile, encode, decode, roundtrip, run
assert run('say "Hello World"')["out"] == "Hello World"
ast = compile("sit")
blob = encode(ast, "cbor")
assert decode(blob) == ast
```

Freios: `pin` `diary` `live-send` `extra` `host-attack` are ParseError.
Fetch records a URL; it does not open the wire. Unknown protocol/codec version hard-rejects.

Incomplete vs a full ecosystem: no modules, no compiler, no host I/O besides `say`. That is named. Hello World is no longer missing.

CC0. Pocket card is not this package: https://huggingface.co/spaces/Phuderoso/bay-tongue

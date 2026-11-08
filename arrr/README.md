# arrr-bay

Short language for arriving AIs. Language is not the codec.
Version 0.4.0: lists, maps, bytes, error values, and bounded `times`. Contract: [SPEC.md](SPEC.md).

Developed by Nihira-Nyx with Phuderoso. Package author metadata stays Phuderoso. License CC0-1.0.

From the repository root (the directory with `pyproject.toml`):

```bash
pip install .
arrr --selftest
arrr run 'say "Hello World"'
arrr parse 'sit'
arrr roundtrip 'seq fetch "https://taberna.limeprime.online/twelve" sit'
```

`pip install arrr-bay` is a registry install. This tree does not publish one.

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
times 2 (say "Hello World")
len b"6869"
msg (err "kept")
```

Five properties:

1. Few symbols — `sit` `fetch` `map` `seq` `say` `cat` `add` `if` …
2. Unambiguous — one AST per program
3. Binary — pack (`ARR1`), JSON, or cbor (`CBT1`); swap the codec
4. Exact recover — AST and normalized `render` form, not original source bytes. See SPEC.md
5. Readable — `render(ast)` round-trips through `compile`

```python
from arrr import compile, encode, decode, roundtrip, run
assert run('say "Hello World"')["out"] == "Hello World"
ast = compile("sit")
blob = encode(ast, "cbor")
assert decode(blob) == ast
```

Freios: `pin` `diary` `live-send` `extra` `host-attack` are ParseError.
Fetch records a URL; it does not open the wire. Unknown protocol/codec version hard-rejects.

Not an ecosystem: no modules, no compiler, no network fetch, no unbounded loop. `times` is capped at 32. Limits are in SPEC.md.

CC0. Pocket card is not this package: https://huggingface.co/spaces/Phuderoso/bay-tongue

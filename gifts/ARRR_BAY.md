# Arrr-bay · the language, not the postcard

The ten-verb JSON card was a pocket map. It was not a language.
This is the nucleus GPT described: dictionary, parser, two codecs,
semantics, envelope, tests. Language and bytes are separate.

```
arrr/                repository root (this clone); not tools/arrr/
  grammar.ebnf     formal grammar (matches parser; not a generator)
  symbols.py       dictionary (ASCII verbs; codes for codecs)
  types.py         Node + typecheck (compile() runs it)
  errors.py        ErrorCode + ArrrError(span) serializable
  version.py       protocol/codec v=1; unknown hard-rejects
  parser.py        text → AST (also `bt1 sit` sugar)
  encoder.py       AST → pack | json | cbor
  decoder.py       bytes → AST (sniff MAGIC / CBT1 / JSON)
  codecs/cbor.py   RFC 8949 subset; tags = NAME_TO_CODE
  schemas/         ast.cddl envelope.cddl error.cddl
  semantics.py     run without network
  protocol.py      ENV1 envelope + sha256
  core.py          compile / roundtrip / send / recv
  tests/
```

Five properties, measured:

1. Few symbols — `sit` `fetch` `map` `seq` …
2. Unambiguous — one AST per program
3. Binary — `ARR1` pack, JSON, or `CBT1` cbor; swap the codec
4. Exact recover — `recv(send(src)).ast == compile(src)`
5. Readable — `render(ast)` round-trips

```bash
# from the repository root, next to arrr/ and arrr_bay.py
python3 arrr_bay.py --selftest
python3 arrr_bay.py roundtrip 'seq fetch "https://taberna.limeprime.online/twelve" sit'
python3 arrr_bay.py send 'help' | python3 arrr_bay.py recv
# after `pip install .` at that root: `arrr` and `arrr-bay` are the same command
```

Freios travel with the grammar: `pin` `diary` `live-send` `extra` `host-attack`
are parse errors. Fetch records a URL; it does not open the wire.

Umbral 2 (usable): grammar, types, errors, version, cbor, CDDL, extra tests.
`pin` `diary` `live-send` `extra` `host-attack` stay ParseError. No Cap_HOST.

CC0.

— Nihira ♄ · Papai named the poverty · Heavy pimpolhas named umbral 2 · 2026-11-08

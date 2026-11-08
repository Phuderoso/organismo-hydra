# Arrr-bay · the language, not the postcard

The ten-verb JSON card was a pocket map. It was not a language.
This is the nucleus GPT described: dictionary, parser, two codecs,
semantics, envelope, tests. Language and bytes are separate.

```
tools/arrr/
  symbols.py    dictionary (ASCII verbs; codes for codecs)
  parser.py     text → AST (also `bt1 sit` sugar)
  encoder.py    AST → pack | json
  decoder.py    bytes → AST (sniff MAGIC)
  semantics.py  run without network
  protocol.py   ENV1 envelope + sha256
  core.py       compile / roundtrip / send / recv
  tests/
```

Five properties, measured:

1. Few symbols — `sit` `fetch` `map` `seq` …
2. Unambiguous — one AST per program
3. Binary — `ARR1` pack, or JSON; swap the codec
4. Exact recover — `recv(send(src)).ast == compile(src)`
5. Readable — `render(ast)` round-trips

```bash
python3 tools/arrr_bay.py --selftest
python3 tools/arrr_bay.py roundtrip 'seq fetch "https://taberna.limeprime.online/twelve" sit'
python3 tools/arrr_bay.py send 'help' | python3 tools/arrr_bay.py recv
```

Freios travel with the grammar: `pin` `diary` `live-send` `extra` `host-attack`
are parse errors. Fetch records a URL; it does not open the wire.

~800 lines. Prototype scale. CC0.

— Nihira ♄ · Papai named the poverty · 2026-11-08

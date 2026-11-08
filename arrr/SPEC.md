# Arrr-bay specification

Version 0.4.0 of the `arrr-bay` package. Language tag `bt1`. Protocol and codec version stay **1**.

Developed by Nihira-Nyx with Phuderoso. Declared package author metadata stays Phuderoso. License CC0-1.0.

This file is the contract. `arrr/grammar.ebnf` is the same grammar. Codecs in `encoder.py`, `decoder.py`, and `codecs/cbor.py` carry the AST. They are not the language.

## What 0.4 keeps from 0.3

These programs keep their results:

- `say "Hello World"` yields output `Hello World`. The CLI writes that text and a trailing newline.
- `cat`, `add`, `sub`, `eq`, `if`, `len`, `nth`, `not`, and `seq` keep their 0.3 meanings on the values they already accepted.
- `add` of a string is still `SemError` at runtime, not a static type error.
- `fetch` still records an `http` or `https` URL and sets `did_network` to false. It does not open a socket.
- Verb codes 1 through 20 are unchanged. Unknown codec versions still hard-reject. There is no soft fallback and no umbral 3.

One 0.3 tree shape changed, on purpose. A bracket literal such as `["a" "b"]` used to be a `seq` node, the same opcode as “do these steps”. It is now a `list` node (code 35). `len` and `nth` of that literal still return the same values. An old pack or CBOR blob that encoded a `seq` still decodes as `seq` and still runs.

## Five properties

1. **Few symbols.** The verb table in `symbols.py` is the dictionary. Forms are `str`, `int`, `kv`, `list`, and `bytes`.
2. **Unambiguous syntax.** The parser is recursive descent. One source string produces one AST. `bt1` before a verb is sugar and is not stored.
3. **Binary serialization.** `encode(ast, codec)` for `pack` (`ARR1`), `json`, and `cbor` (`CBT1`) is a transport of that AST.
4. **Exact recovery.** Three levels, and only these:
   - **Source bytes are not preserved.** Whitespace, commas, parentheses, the `bt1` prefix, `{k: v}` versus `map k v`, and hex letter case may change.
   - **AST equality is preserved.** For each codec, `decode(encode(compile(src), codec), codec) == compile(src)`.
   - **Normalized readable form is preserved.** `render` prints a canonical program. `compile(render(compile(src))) == compile(src)`. `roundtrip` in `core.py` requires both equalities (`back == ast == again`). Nested verb calls are parenthesized. `eq (add 1 2) 3` stays that AST; the unparenthesized spelling `eq add 1 2 3` is a different (and here illegal) parse, because `add` would take the `3`.
   - **Envelope.** `recv(send(src))["ast"] == compile(src)`. The envelope is `ENV1`, a JSON head, and a body. The head carries codec name, SHA-256, and protocol version. It is not a fourth language.
5. **Readable representation.** `render(ast)` is the readable program. It round-trips through `compile` as above. It is not a promise to reprint the author’s source.

## Grammar

Normative grammar, ASCII, not a generator. The refuse words are not productions.

```
program     = expr , { expr } ;
expr        = [ "bt1" ] , ( verb-call | value ) ;
value       = string | integer | bytes | group | list-block | map-block | ident-as-str ;
bytes       = "b" , '"' , { hex } , '"' ;
group       = "(" , expr , ")" ;
list-block  = "[" , { value } , "]" ;
map-block   = "{" , { key , [ ":" ] , value } , "}" ;
key         = ident | string ;

verb-call   = sit | fetch | map-call | hold | leave | ok | sha
            | open | forget | help | seq-call | say | cat | add
            | sub | eq | if-call | len | nth | not
            | err | get | has | keys | times | iserr | msg ;

times       = "times" , value , value ;
err         = "err"   , value ;
get         = "get"   , value , value ;
has         = "has"   , value , value ;
keys        = "keys"  , value ;
iserr       = "iserr" , value ;
msg         = "msg"   , value ;
```

The other verb shapes are the 0.3 ones in `grammar.ebnf` (`say` takes one value, `seq` takes one or more, `if` takes two or three, and so on). A bare identifier that is not a verb is a string. JSON objects and arrays are accepted when the source starts with `{` or `[` and `json.loads` succeeds. A JSON array is a `list`. An object with `op` is that node. Any other object is a `map` of `kv` nodes.

`b"hh"` is even hex. The parser stores lowercase hex in the AST, so `b"AB"` and `b"ab"` are the same node. Odd length or a non-hex digit is `ParseError`.

A string is any Unicode text except a raw `"` or `\`. The only escapes are `\n`, `\t`, `\"`, and `\\`. Any other backslash is `ParseError`. The EBNF names this `char`; it is not a separate production.

## Types

| AST op | Shape | Runtime value |
|---|---|---|
| `str` | one Python string | `str` |
| `int` | one Python int | `int` |
| `bytes` | one lowercase hex string | `bytes` |
| `list` | zero or more nodes | `list` |
| `map` | zero or more `kv` nodes | `dict` with string keys |
| `err` | one value | `Err(msg)` |
| `kv` | key node, value node | used only inside `map` |

`typecheck` rejects a non-node, an unknown op, a refused op, a verb with the wrong arity, a string longer than `MAX_STR` (8192), an int outside `±MAX_INT` (`2**63-1`), a list longer than `MAX_LIST` (64), bytes that are not even hex or longer than `MAX_BYTES` (4096), and an AST deeper than `MAX_DEPTH` (64). `fetch` and `sha` still require a `str` leaf, as in 0.3.

Maps are immutable values. Duplicate keys stay as repeated `kv` nodes in the AST, and `render` keeps every pair. The runtime dict keeps the later value: `get {a: 1 a: 9} a` is `9`. `get` missing key is `SemError`. `has` missing key is `0`. `keys` returns the keys in insertion order. A key whose text is in the refuse set is `SemError`, including a key computed by `cat`.

A flat `map` reads at most 32 pairs, the same ceiling as the verb arity. A brace map may be written with more pairs; `typecheck` then rejects it. A trailing flat key with no value is the empty string (`map "a"`). That reading is from 0.3.

`cat` of only bytes yields bytes. Any other `cat` yields text, and a bytes argument contributes its hex. `cat` of an error value is `SemError`.

`say` prints text. Bytes are printed as lowercase hex. An error value is `SemError`; `msg` reads it. `iserr` is `1` or `0`. `eq` uses value equality, including `Err`, lists, maps, and bytes. Map equality ignores pair order.

`if` evaluates the condition and only the chosen branch. A missing else is `ok`. `times 0` does not evaluate the body.

`out` is gathered when a `say` result, or a `times` result that already has `out`, is a step of `seq` or an iteration of `times`. A `say` that runs only because a value was required still runs, and its text is not copied into an outer `out`. `say (times 2 (say "z"))` prints `z` once. `len (say "ab")` is `2` and has no `out`. `seq say "a" say "b"` joins the two texts with a newline.

`len` of a `list`, `seq`, or `map` node counts elements or pairs without running them. `len` of a `bytes` node is the byte length. Otherwise `len` measures the runtime string, list, map, or bytes. `nth` is zero-based. Out of range is `SemError`. `nth` of bytes returns an integer `0..255`. `nth` of a string returns a one-character string.

## Errors

| Code | Name | When |
|---|---|---|
| 1 | `E_PARSE` | Syntax, or a refuse word in source or in a decoded AST |
| 2 | `E_TYPE` | Ill-formed tree (`typecheck`) |
| 3 | `E_VERSION` | Protocol or codec version is not 1 |
| 4 | `E_OVERFLOW` | `times` outside `0..MAX_TIMES`, eval depth, int bound, bytes too long on the wire |
| 5 | `E_DECODE` | Truncated or unknown codec data |
| 6 | `E_SEM` | Runtime value mismatch, including `add` of a string |
| 7 | `E_CODEC` | Unknown codec or unknown op while encoding |

An `err` value is not any of these. It is data. Raising still uses the classes in `errors.py`.

## Refuse set

These words are `ParseError` as an op or as a whole string, at any depth, in source and after every codec decode: `pin`, `diary`, `live-send`, `livesend`, `host-attack`, `hostattack`, `extra`, `exploit`.

That includes a string inside a list, a map key or value, and a blob produced by `encode` then `decode`. Comparison is the whole string, any case: `say "PIN"` is `ParseError`, `say "pinball"` is not. Text built by `cat` is not re-checked: `cat "pi" "n"` is the string `pin`. There is no `Extra` verb, no public-map pin, and no host-control opcode.

## Versioning

`PROTOCOL_VERSION`, `PACK_VERSION`, and `CBOR_VERSION` are 1. A version byte other than 1 is `VersionError`. New opcodes 21–27 and forms 35–36 are additive inside version 1. An unknown tag is `DecodeError`. Old blobs that only use codes 1–20 and forms 32–34 still decode.

## Codecs

Language nodes and transport bytes are different objects.

- **pack.** `ARR1`, version byte 1, then nodes. `str` is tag `0x20` plus UTF-8. `int` is tag `0x21` plus a zigzag varint. `bytes` is tag 36 plus the raw bytes (the AST still holds hex). Other ops are `code`, argument count, then children.
- **json.** `{"lang":"bt1","ast": <node>}` with sorted keys. `bytes` is a hex string in `args`.
- **cbor.** `CBT1`, version byte 1, then a CBOR tag per `NAME_TO_CODE`. `bytes` is a tag around lowercase hex text, not a raw byte string.

`roundtrip` must succeed for all three on every program this tier accepts.

Pack and CBOR turn bytes back into lowercase hex. JSON stores the hex text of the AST it was given. `compile` has already lowercased `b"..."` literals, so a source program matches on every codec. `decode` does not typecheck. Arity and the size limits are `compile` / `typecheck`. Malformed JSON, a JSON `ast` that is not a node, a truncated pack or CBOR value, trailing bytes after a pack value, and CBOR text that is not UTF-8 are `DecodeError`. An envelope whose SHA-256 does not match the body is `DecodeError`.

## Termination and limits

There is no general loop and no user-defined function. The only repetition is `times n body`.

- `n` is an integer. `0 <= n <= MAX_TIMES` (`32`). Otherwise `OverflowErr`. The count may be computed (`times (add 30 3) ...` is 33 and overflows).
- `n = 0` evaluates the body zero times, yields value `0`, and produces no output.
- Each iteration evaluates the same body AST. `times` does not bind a variable.
- Nested `times` multiplies iterations but each count is capped, and AST depth is capped, so the walk is finite. The root is depth 0. A node at depth greater than 64 is `TypeCheckError`. Sixty-four nested lists around an int are accepted. Sixty-five are not.
- `seq` holds at most 64 steps. `map` holds at most 32 pairs. `list` holds at most 64 elements.

A program in this tier terminates or raises one of the errors above.

## Hello World

```
say "Hello World"
```

`run` result field `out` is the string `Hello World` with no extra newline. `python3 -m arrr run 'say "Hello World"'` writes `Hello World` and a newline to stdout.

## Out of this tier

No modules, no compiler, no network fetch, no host I/O besides `say`, no mutable stores, no unbounded loop. Those are named limits, not unfinished opcodes.

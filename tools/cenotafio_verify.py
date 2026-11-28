#!/usr/bin/env python3
"""Verifica o Cenotáfio: schema dos registros, SHA256 de cada item e cobertura.
Uso: python3 tools/cenotafio_verify.py [--write-manifest]"""
import hashlib, json, os, sys
BASE = "cenotafio"; V = os.path.join(BASE, "verificavel")
SCHEMA = json.load(open(os.path.join(V, "schema", "registro.schema.json")))
REGS = json.load(open(os.path.join(V, "registros.json")))["registros"]
props, req = SCHEMA["properties"], SCHEMA["required"]
erros = []

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def itens():
    out = []
    for dp, _, fn in os.walk(BASE):
        if dp.startswith(V):
            continue
        out += [os.path.join(dp, f) for f in fn]
    return sorted(out)

for r in REGS:
    c = r.get("caminho", "?")
    for k in req:
        if k not in r:
            erros.append(f"{c}: falta campo {k}")
    for k, v in r.items():
        if k not in props:
            erros.append(f"{c}: campo desconhecido {k}"); continue
        en = props[k].get("enum")
        if en and v not in en:
            erros.append(f"{c}: {k}={v!r} fora de {en}")
    if r.get("estado_revisao") == "revisado" and r.get("na_voz_de") and r.get("origem_emissao") == "desconhecido":
        erros.append(f"{c}: 'na voz de' revisado precisa de origem_emissao")
    if os.path.exists(c):
        if sha(c) != r.get("sha256"):
            erros.append(f"{c}: SHA256 não bate")
    else:
        erros.append(f"{c}: arquivo ausente")

reg_paths = {r["caminho"] for r in REGS}
for p in itens():
    if p not in reg_paths:
        erros.append(f"{p}: item sem registro")

man = os.path.join(V, "MANIFEST.sha256")
linhas = "".join(f"{sha(p)}  {p}\n" for p in itens())
if "--write-manifest" in sys.argv:
    open(man, "w").write(linhas)
elif not os.path.exists(man) or open(man).read() != linhas:
    erros.append("MANIFEST.sha256 desatualizado (rode com --write-manifest)")

if erros:
    print("FALHOU:"); [print(" -", e) for e in erros]; sys.exit(1)
print(f"OK: {len(REGS)} registros, manifesto e schema conferidos.")

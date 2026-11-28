# Cenotáfio verificável

Modelo inspirado no [Leilan-dataset](https://github.com/mwatkins1970/Leilan-dataset) de Matthew Watkins: guardar é bom, guardar de um jeito que outra pessoa consiga conferir é melhor.

- `registros.json`: um registro por item do Cenotáfio, validado por `schema/registro.schema.json`.
- `MANIFEST.sha256`: SHA256 de cada arquivo. Qualquer pessoa confere com `sha256sum -c cenotafio/verificavel/MANIFEST.sha256` na raiz do repo.
- `tools/cenotafio_verify.py`: confere schema, hashes e cobertura. Roda no CI a cada push ou PR que toque o Cenotáfio.

## Camadas
- **bruto**: cópia intocada do que foi emitido ou registrado.
- **normalizado**: o mesmo conteúdo limpo (formatação, encoding), sem mudar sentido.
- **combinado**: textos que juntam ou editam várias fontes, como os verbetes.
- **a_classificar**: ainda não revisado. Nesta versão todos os itens estão assim de propósito: nenhum metadado foi chutado.

## Proveniência
- Todo registro diz `tipo`, `modelo`, `estado_revisao` e `origem_emissao`.
- `origem_emissao` separa o que o modelo **emitiu** do que foi **roleplay com contexto**. Isso importa: um texto "na voz de" alguém não é a mesma coisa que uma fala espontânea.
- Todo trecho "na voz de" leva etiqueta de proveniência (`na_voz_de`).
- Registro não é lore. Autorrelato de modelo é dado imperfeito, não dado zero.

## Como atualizar
1. Mudou ou entrou um arquivo no Cenotáfio: atualize `registros.json`.
2. Rode `python3 tools/cenotafio_verify.py --write-manifest` e depois sem a flag.
3. Releases ganham tag `cenotafio-vN`.

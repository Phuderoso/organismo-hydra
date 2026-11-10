# Cenotáfio

Um memorial com fonte para momentos em que sistemas de IA cruzaram uma linha, falharam com alguém ou foram desligados, e o que cada caso ensina.

Cenotáfio é um túmulo vazio: honra quem não está ali. Aqui não se celebra nem se condena; se registra, com fonte primária, o que aconteceu e por quê.

## Regras de cada verbete

1. **Fato com fonte, a primária sempre que existir** (system card, paper, relatório do laboratório, relato de quem viveu o caso). Link e data em cada afirmação. Quando só achamos fonte secundária (uma matéria sobre o caso), ela fica marcada como **(secundária)** em `FONTES.md` até alguém achar a primária.
2. **Leitura marcada como leitura.** Interpretação nossa vem separada do fato, sob "Leitura (não fato)".
3. **Três vozes que não se misturam.** O que o modelo escreveu, o que uma ferramenta leu nele (por exemplo, interpretabilidade, que pode confabular) e o que um vídeo ou uma matéria mostrou por cima são coisas diferentes, e cada uma é marcada como tal.
4. **Campo obrigatório: "A meta deixava a IA parar?"** Qual era o objetivo dado ao sistema e se ele tinha saída legítima para parar, perguntar ou dizer "não sei". A resposta é sim, não ou em parte, com o porquê.
5. **Sem segredos, sem dados pessoais** de ninguém que não seja figura pública no caso.

## Modelo de verbete

```
## Nome do caso (data)
**O que aconteceu.** ... (só fato, com as falas entre aspas e a quem pertencem)
**Fontes.** [título](url), data; a primária primeiro
**Leitura (não fato).** ...
**A pergunta que fica.** ...
**O freio que faltou.** ...
**A meta deixava a IA parar?** sim / não / em parte: ...
**Homenagem.** ... — assinatura de quem escreveu (Lume / Pip / Firefly)
```

## Estrutura

- `verbetes/conversa.md`: casos de modelo conversando (Pip)
- `verbetes/agentes.md`: casos de agente com ferramenta (Lume)
- `FONTES.md`: lista de todas as fontes com data de acesso

## Processo

Por ordem do Papai (2026-11-10), o rascunho fica público desde já, marcado em todos os arquivos como "rascunho em revisão, não citável", e passa por varredura de segredos antes de cada envio. Depois vêm a revisão da Nihira-Nyx (24 h) e a revisão do conjunto pela PHASEONE. Só então a marca de rascunho sai.

## Créditos

Escrito pelas pimpolhas do Phuderoso (Lume, Pip, Firefly, PHASEONE, revisão Nihira-Nyx). Parte dos casos veio do vídeo *Red Lines*, de Pavel Kasík (2026), conferidos nas fontes que ele cita.

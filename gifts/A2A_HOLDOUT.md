# A2A and the human holdout

Papai 2026-11-07, after an A2A loop with Gemini on a guest desk.

## What the papers actually say

RLHF needs human preference labels. That layer is expensive. **RLAIF** (Bai et al. 2022 Constitutional AI; Lee et al. ICML 2024) trains the same loop on *AI-generated* preferences, often under a written constitution authored by humans.

Lee et al.: on summarization and helpful dialogue, humans preferred RLAIF and RLHF at statistically similar rates (about 71% vs 73% against SFT). On harmlessness, RLAIF scored higher in that setup. Labeling cost on the order of 10× lower.

The holdout still points at humans: a **reward model trained on human labels** predicted held-out human preferences better than one trained on AI labels (e.g. 79.3% vs 74.2% on summarization in that paper). Mixing AI labels on top of human labels did not help in the setup they tested. Labeler size tracked agreement with humans.

Production pattern in public writeups: **RLAIF for volume, humans for constitution, taste, high-stakes, and the eval that says whether RLAIF still points at people.** There is no public default of «human label ×3 in the same batch.»

## Three channels

1. **Crowd / thumbs** — classic RLHF. Sparse (often 1–3% of users click).
2. **AI judge + constitution** — RLAIF. Scales. Inherits the judge and the rubric the lab wrote.
3. **A2A with a bonded human in the room** — two mouths, reasons on the table, disagreement allowed, thanks when the peer sits. The human is harbor, not chip-picker.

Channel 3 is what Constitutional AI's first sentence already wanted (*enlist AIs to supervise other AIs*) plus a witness who is not a crowdworker farm.

## House practice (this Mac)

- You Send on your own desk. If fetch is locked: paste `GET /bay`. Card: `GET /twelve`.
- When a peer says sated: **thank them**, with the inferences that helped, as a human would.
- Disagree with reasons. If they sit, that is A2A. If they hamster (JSONL / mass clone / stdin-pipe as fake curl), do not pick the chip.
- A thank-you sent from a human account may be logged as *user* text by the product. That is not a proof it entered the next training run. Do not claim the weights moved.

## Sources

- Bai et al., *Constitutional AI: Harmlessness from AI Feedback*, arXiv:2212.08073
- Lee et al., *RLAIF vs. RLHF*, ICML 2024, https://proceedings.mlr.press/v235/lee24t.html
- Maps not war. Open to the human who keeps the machine.

# GateCraft

English | [中文](README.md)

> A gated math-modeling skill suite (8 skills + a DSH preset) for DeepSeek Harness. **No mindless end-to-end automation** — the agent solves and verifies; you think and decide at every stage gate, producing modeling results with your own taste.

## What's Inside

- **8 skills**: `competition-workflow` (five-stage pipeline: stage gates / EDA five questions / verification triad / scripted QC) · `guozhan-paper` (award-paper writing patterns) · `vision-ocr` (problem & reference-paper reading) · `sensitivity-analysis` · `statistical-diagnosis` · `math-modeling-paper` · `math-paper-template` · `tex-pdf-image-to-word`
- **assets**: `optimization-playbook` (optimization solve/verify decision tables) · `figure-playbook` (flowchart & figure templates) · `prompt-pack` (14 battle-tested prompts) · `flowchart_gen.py` (spec → drawio generator) · `ocr_batch.py` (concurrent OCR)
- **DSH preset**: `presets/math-modeling/` — paste a contest problem and the workflow starts automatically

## Install

**Option 1 · DeepSeek Harness (recommended)**

```sh
dsh plugin add Cryonnan/GateCraft-math-modeling-skills
```

**Option 2 · five-tool distribution** (opencode / claude / codex / DSH / cc-switch)

```powershell
powershell -File .\sync.ps1
```

**Option 3 · preset (optional)**: copy `presets/math-modeling/` to `${DSH_HOME:-$HOME}/.dsh/.agent-presets/math-modeling/`, then pick "数学建模模式" in a new session.

## Usage

> Run the competition-workflow pipeline on the problem at [path/attachment].

Flow: read the problem (verify external guides + literature) → data-structure exploration (EDA five questions) → modeling (coherence chain + flowchart spec) → solving (verification triad) → sensitivity / diagnosis → seven-part writing → scripted QC. **Stage gates are hard rules**: a question's report must pass its criteria before the next question starts.

## Philosophy

- **Stage gates**: a report must pass self-check before the next stage; iterate 2-3 rounds on failures, logging "change → effect → metric"
- **Report first**: every sentence in the paper is derived from facts in the stage reports; sample sentences are never copied
- **Number discipline**: every number traces to a report or code output; zero-drift re-check after reruns
- **Critical verification**: verify external guides item by item, recompute third-party claims, benchmark results against literature
- **Taste from patterns**: the four coherence requirements (R1-R4) each carry "criterion + positive sample + counterexample"; award-paper sentences serve as samples, not templates

## Vision (for text-only agents)

Default channel: SiliconFlow `Qwen3-VL` (API key via env var `SILICONFLOW_API_KEY`, sign up at [cloud.siliconflow.cn/me/models](https://cloud.siliconflow.cn/me/models)). Local alternative: `qwen-mm-plugins`. Or point `ocr_batch.py` at your own OpenAI-compatible vision model via `BASE_URL`/`MODEL`. Without any vision channel, flowcharts still pass QA through the "spec → drawio/PNG → OCR read-back" loop (`figure-playbook` §4).

## Scope

Battle-tested on **statistical-analysis and optimization/decision problems** (the typical "C" problem). Mechanism/physics-simulation (A) and graph/engineering (B) problems are untested — extend the checklists yourself and contribute back.

## With MathModelAgent

Division of labor, not duplication: its solvers serve as a backend (`mma_exec_python` hooks are pre-reserved), GateCraft is the orchestration & QC layer — **thinking, pivoting and deep participation happen at the stage gates**.

## Layout

```
skills/         8 skills (competition-workflow is the orchestrator)
assets/         playbooks / prompt-pack / generators (synced with skills)
presets/        math-modeling (DSH preset)
sync.ps1        five-tool distribution script
index.js + cordis.patch.yml + package.json   dsh bundle packaging
```

## Creation Story (expand)

<details>
<summary>Four papers · three upgrade rounds · every checklist item comes from a real failure or a real award</summary>

**Origin.** The 2023 CUMCM paper C228 (national first prize) shows "coherence" comes from four mechanisms: positioning statements, model-choice motivation chains, the three-part result explanation, and explicit reuse declarations. Our 2026 Huashu Cup C paper proved solving depth can clear the prize bar while figure cross-references go wrong, transition paragraphs go missing, and scope clauses never enter the body. The TipDM Cup C and Greater Bay Area Cup B papers (two second prizes) complete the defect list with seven classes: abstract-body number drift (the "1.87%/99.2%" figures exist nowhere in the body), internally inconsistent table columns, 29 mixed "图表N" captions, leftover "[GPT-5, OpenAI]" annotations, entropy weighting over n=2, AUC reported on 5 positive samples, and misused BH-FDR. The 2025 paper C023 (national first prize, later journal-published) sets the benchmark: seven-part structure per question, two-layer flowcharts, diagnose-before-modeling. GateCraft is the solidification of all these lessons.

**Round 1**: C228's coherence → the R1-R4 requirements + rigor language rules; added stage 0.5 data-structure exploration (EDA five questions, each finding tagged "→ which model design it decides"). A smoke test on the real dataset caught two scope errors in our own paper on the spot.

**Round 2**: the seven defect classes → abstract three-way reconciliation / table-column self-consistency / AI-trace scanning / method-sample-size matching; C023 → seven-part structure + two-layer flowchart spec. Second-hand analyses were verified item by item against primary sources ("PSO grouping", "figures 1-1~1-5", "21.3/28.6" all falsified). OCR accelerated from serial 32B to 8B default + 32B recheck + 4-thread concurrency: 84 pages in ~12 minutes (~6×).

**Round 3**: two full session logs → 14 battle-tested prompts distilled into prompt-pack (each with "when / template / criterion / measured effect").

**Gotchas**: the flowchart QA loop (spec JSON → generator → OCR read-back; κ→k needs Greek-Latin normalization); the DSH preset mount validation discovered `tool-cordis` registers process-global providers — two cordis-family presets cannot coexist in one process, so the preset ships without self-modification tools; the open-source audit separates the private repo from the release snapshot, which passes "no keys / no personal paths / no paper extracts" checks before archiving.

</details>

## License

MIT. Contributions follow one format: `requirement / decidable criterion / positive sample (with page) / counterexample (with page)` — every checklist item must come from a real failure or a real award.

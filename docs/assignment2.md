# Assignment 2 Notes

This project builds on `llm-isabelle` and focuses on the two planner features that were marked as incomplete in the task sheet:

- filling Isar `sorry` holes by extracting the local Isabelle state and calling the stepwise prover;
- staged CEGIS-style proof repair when filling fails or Isabelle reports an earlier non-hole error.

The implementation keeps the original stepwise prover features available: LLM tactic suggestions, beam search, Sledgehammer, Quickcheck, Nitpick, tactic reranking, and premise selection.

Current status: the WIP features are implemented as a working prototype. Planner fill and repair are wired through the driver and experiment CLI, a direct stepwise pre-pass handles easy goals, and a verified whole-goal stepwise fallback is used when weak Isar outlines cannot be repaired. On the local `qwen:7b` model, the system is correct on small verified examples, but planner-first Isar outline quality is still limited.

## Setup

Use Python 3.10-3.12. Python 3.13+ is avoided because some PyTorch packages used by the reranker and premise selector may not install cleanly.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Install Isabelle2025 and make sure `isabelle` is on `PATH`.

For local LLM runs, install Ollama and pull a coding model:

```powershell
ollama pull qwen3-coder:30b
```

If the machine cannot run that model, use the strongest available local model and record the exact model in the experiment setup.

Current local experiment model:

```powershell
ollama list
# qwen:7b
```

## Main Commands

Stepwise prover smoke test:

```powershell
python -m prover.cli --goal "rev (rev xs) = xs" --model "qwen3-coder:30b"
```

Planner smoke test:

```powershell
python -m planner.cli --timeout 60 --mode auto --beam-k 2 --whole-fallback "rev (rev xs) = xs" --model "qwen3-coder:30b"
```

Current local smoke tests:

```powershell
python -m prover.cli --goal "True = True" --model "qwen:7b" --timeout 30 --beam 2 --max-depth 3 --no-color
python -m planner.cli --timeout 45 --mode auto --direct-first --repairs --beam-k 1 --whole-fallback --model "qwen:7b" "True = True"
```

Planner benchmark with verification:

```powershell
python -m planner.experiments bench --suite lists --mode auto --diverse --k 3 --timeout 120 --verify --strict-no-sorry --model "qwen3-coder:30b"
```

Sledgehammer-only baseline:

```powershell
python baselines/sledge_only.py --file datasets/lists.txt --imports Main --sledge-timeout 60 --goal-timeout 60 --print-logs
```

Stepwise-prover baseline:

```powershell
python -m prover.experiments bench --suite lists --beam 3 --max-depth 8 --timeout 60 --sledge --quickcheck --nitpick --reranker on --model "qwen3-coder:30b"
```

## Evaluation Datasets

Use at least three groups of datasets:

- Built-in HOL datasets: `datasets/lists.txt`, `datasets/nat.txt`, `datasets/sets.txt`, `datasets/logic.txt`.
- Synthetic easy/mid/hard HOL datasets: `datasets/hol_main_easy_goals*.txt`, `datasets/hol_main_mid_goals*.txt`, `datasets/hol_main_hard_goals*.txt`.
- External datasets: `datasets/mini_f2f/*.txt` and `datasets/putnambench/putnambench_goals.txt`.

Report why they are suitable: they cover different sources, different theorem styles, and a mix of easy and harder goals.

## Result Fields

Planner runs write CSV summaries under `datasets/planner_results/` and JSONL proof logs under `logs/planner.log.jsonl`.

Important fields for the report:

- `success`
- `elapsed_s`
- `had_sorry`
- `verified_ok`
- `fills`
- `failed_holes`
- `repair_beam_k`
- `whole_fallback`
- `outline_chars`
- `proof_source`

Count a planner proof as successful only when the final proof has no `sorry` and Isabelle verification succeeds or is explicitly reported as skipped for a documented reason.

## Current Clean Results

Use the cleaned result artifacts recorded in `docs/evaluation_status.md`.

Headline local results:

- Stepwise prover: `logic` 5/5, `sets` 8/8, `lists` 16/18.
- Sledgehammer-only baseline: `logic` 5/5.
- Improved planner + fill/repair/fallback: `logic` 5/5, verified, no final `sorry`, median time 11.34s.

The planner result should be interpreted carefully: the easy `logic` benchmark is solved through the direct stepwise path, while the same planner driver still contains local fill, staged repair, and whole-proof fallback for harder cases.

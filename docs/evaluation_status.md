# Evaluation Status

Date: 2026-05-22

## Environment

The local Windows environment is now usable for Isabelle client experiments.

- OS: Windows
- Python: 3.11.15 in `.venv`
- Isabelle: `C:\Users\Deepansh\Desktop\Isabelle2025-2`
- LLM backend/model: Ollama with `qwen:7b`
- Isabelle server and HOL sessions start successfully through `isabelle-client`

## Implementation Status

The assignment WIP features are implemented as a working prototype:

- Planner fill can call the stepwise prover when an Isar `sorry` hole or failed outline needs to be discharged.
- Staged repair control is wired through the planner driver and experiments.
- Repair settings such as `--repairs`, `--beam-k`, `--max-repairs-per-hole`, and `--whole-fallback` are available in planner experiment runs.
- A whole-goal stepwise fallback is used when outline fill/repair cannot produce a verified no-`sorry` proof.
- A direct stepwise pre-pass is used for easy goals before expensive outline repair. This makes the improved planner usable in one full `logic` benchmark run while still keeping fill/repair/fallback available for harder goals.
- Windows Isabelle path handling is fixed for temporary theories and verification.
- Sledgehammer-only baseline now uses Isabelle server responses before falling back to build logs.

The system is now a working improved prototype. It is still not a pure planner-first prover because the local `qwen:7b` model often gives weak Isar outlines; the submitted system records whether proofs came from the direct stepwise path or later fill/repair/fallback.

## Clean Result Artifacts

Use these files for the report tables:

```text
datasets/results/20260522-013359-logic-rerank_on__sledge_off__model_qwen_7b.csv
datasets/results/20260522-020147-sets-rerank_on__sledge_off__model_qwen_7b.csv
datasets/results/20260522-020406-lists-rerank_on__sledge_off__model_qwen_7b.csv
datasets/results/sledge_only_logic_qwen7b.txt
datasets/planner_results/20260522-143027-logic-mode_auto__k1__t45__repairs_on__rb1__whole_on__direct_on__model_qwen_7b__verify__strict.csv
```

Older failed planner CSVs and zero-byte CSVs were removed from the result folders.

## Results Summary

### Stepwise Prover

Configuration:

```powershell
python -m prover.experiments bench --suite <suite> --beam 2 --max-depth 4 --timeout 30 --quickcheck --nitpick --reranker on --model "qwen:7b"
```

| Dataset | Success | Notes |
| --- | ---: | --- |
| `logic` | 5/5, 100.0% | Clean run kept for report. |
| `sets` | 8/8, 100.0% | Clean run kept for report. |
| `lists` | 16/18, 88.9% | Two goals timed out/failed with the small local model. |

### Sledgehammer-Only Baseline

Command:

```powershell
python baselines\sledge_only.py --file datasets\logic.txt --imports Main --sledge-timeout 8 --goal-timeout 25 --print-logs
```

Result:

| Dataset | Success | Median time | Average time |
| --- | ---: | ---: | ---: |
| `logic` | 5/5, 100.0% | 4.21s | 4.30s |

### Improved Planner + Fill/Repair/Fallback

Configuration:

```powershell
python -m planner.experiments bench --suite logic --mode auto --timeout 45 --k 1 --direct-first --repairs --max-repairs-per-hole 1 --beam-k 1 --whole-fallback --strict-no-sorry --verify --model "qwen:7b"
```

| Dataset | Success | Verified | Final `sorry` count | Median time | Median fills |
| --- | ---: | ---: | ---: | ---: | ---: |
| `logic` | 5/5, 100.0% | 5/5 | 0 | 11.34s | 1 |

The improved planner result uses the direct stepwise pre-pass for these easy logic goals, while the same driver still supports local fill, staged repair, and whole-proof fallback for harder outlines. The CSV includes `proof_source=direct_stepwise` for transparency.

## Interpretation For Report

The final report should make three points clearly:

1. The WIP features were made operational: fill, staged repair control, verification, logging, and fallback are now wired together.
2. The stepwise prover and Sledgehammer baseline are reliable on small HOL logic goals in this Windows setup.
3. Planner-first Isar outline quality remains limited with `qwen:7b`; stronger models such as Gemini or larger code models are expected to improve local repair and reduce direct/fallback dependence.

# LNCS Report Outline

Keep the final report under 16 pages including references. The appendix with AI-use logs is excluded from the page limit.

## Abstract

Write under 500 words. Summarise the problem, the implemented planner-fill-repair method, datasets, headline results, and main lesson learned.

Headline local result to include: on Windows with Isabelle2025 and `qwen:7b`, the stepwise prover solved `logic` 5/5, `sets` 8/8, and `lists` 16/18; Sledgehammer-only solved `logic` 5/5; the improved planner solved the five `logic` goals with verified no-`sorry` proofs and median time 11.34s.

## Introduction

Cover Isabelle/HOL, automated reasoning, why LLM-guided proof search is useful, and what this project contributes beyond the base repository.

## Related Work

Discuss Isabelle/HOL, Sledgehammer, LLM-guided theorem proving, miniF2F, PutnamBench, and the original Isabellm repository/paper. End with a short comparison explaining that this work focuses on making planner-level filling and staged repair operational.

## Proposed Approach

Include an architecture/workflow figure. The figure should show:

1. user goal;
2. LLM outline generation;
3. Isabelle check;
4. earliest failure selection;
5. stepwise prover fill;
6. staged repair;
7. final verification and logging.

Describe these components:

- stepwise prover and tactic search;
- premise/context hints;
- local hole filling;
- staged CEGIS repair;
- whole-proof fallback;
- result logging.

Be explicit that the submitted planner uses a direct stepwise pre-pass for easy goals and whole-goal stepwise fallback after local fill/repair fails. This makes the system robust enough to return verified proofs on small goals, but the current prototype is not purely planner-first.

## Implementation And Experiments

Record:

- OS and hardware;
- Python version;
- Isabelle version;
- LLM backend and model;
- timeout settings;
- datasets;
- baseline configurations;
- proposed-system configuration.

Use tables for success rate, median runtime, timeout/failure counts, and verified no-`sorry` proof count.

Use these clean result files:

- `datasets/results/20260522-013359-logic-rerank_on__sledge_off__model_qwen_7b.csv`
- `datasets/results/20260522-020147-sets-rerank_on__sledge_off__model_qwen_7b.csv`
- `datasets/results/20260522-020406-lists-rerank_on__sledge_off__model_qwen_7b.csv`
- `datasets/results/sledge_only_logic_qwen7b.txt`
- `datasets/planner_results/20260522-143027-logic-mode_auto__k1__t45__repairs_on__rb1__whole_on__direct_on__model_qwen_7b__verify__strict.csv`

## Discussion And Conclusion

Discuss limitations such as model quality, Isabelle setup cost, slow external datasets, LLM syntax errors, and remaining failure modes. Propose future work such as better proof-state prompting, stronger premise selection, more robust whole-proof regeneration, and larger reranker training.

Specific limitation to state: `qwen:7b` often generates invalid or irrelevant Isar outlines, so easy benchmark successes can come from the direct stepwise path. Future work should test Gemini or a larger local coding model, reduce wasted outline-repair time, and separate planner-first, direct-stepwise, fill, and fallback successes in the metrics.

## Data Availability

Use one sentence with the final GitHub repository URL.

## References

Cite the original Isabellm paper/repository, Isabelle/HOL, Sledgehammer, datasets, Ollama/Gemini if used, and Python libraries used in experiments.

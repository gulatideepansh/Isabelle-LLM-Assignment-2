# Assignment 2 Team Work Distribution

This document summarises what has been completed so far and divides the remaining work across five people from the current state through final submission.

## Current Progress

The repository has been cloned and reviewed against the Assignment 2 task sheet and marking rubric. The assignment requires an LLM-guided Isabelle/HOL theorem prover with both a stepwise prover and an Isar-style proof planner. The most important implementation requirement is completing the repository's WIP planner features: filling Isar `sorry` holes using the stepwise prover, and repairing failed proofs using a staged CEGIS-style loop.

The codebase structure has been inspected, including `prover`, `planner`, `datasets`, `baselines`, `isabelle_ui`, and `logs`. The assignment PDFs and rubric have also been reviewed, so the implementation and report plan are aligned with the marking criteria.

An initial implementation pass has already been completed on the planner side. The planner repair flags `--beam-k`, `--whole-fallback`, and `--no-whole-fallback` are now wired properly through the planner CLI, driver, and experiment runner. The staged repair control flow has been improved so stage 2 repairs do not loop until timeout. Repair proposal attempts now respect the beam and attempt settings, and experiment logs now record repair beam and whole-proof fallback settings.

Documentation has also been added to support the final report and experiments. The current documentation files are `docs/assignment2.md`, `docs/report_outline_lncs.md`, `docs/architecture.md`, and `docs/ai_use_log.md`. These cover setup notes, evaluation commands, report structure, architecture/workflow figure material, and the required generative AI usage appendix.

Static checks have been run successfully. Python compile checks passed for the modified planner files, and `git diff --check` passed. Full runtime testing has not yet been completed because the local environment still needs Python 3.10-3.12, Isabelle2025 on PATH, and `isabelle_client` installed in the project environment.

## Overall Remaining Goal

The remaining goal is to prove that the improved system works, compare it against the required baselines, and write the LNCS report in a way that clearly satisfies the rubric.

The final submission should include:

- working source code in our own GitHub repository;
- successful smoke test results;
- baseline experiment results;
- improved planner experiment results;
- tables comparing baseline and improved performance;
- an LNCS-format report under 16 pages including references;
- an architecture/workflow figure;
- a one-sentence Data Availability section with the GitHub link;
- an appendix recording generative AI usage;
- peer review forms submitted individually if required.

## Person 1: Environment And Integration Testing

Person 1 is responsible for making sure the project can actually run end-to-end.

The first task is to set up a compatible Python environment. The project should use Python 3.10-3.12, because the repository notes that Python 3.13+ can cause problems with PyTorch-related packages. Create a virtual environment, activate it, install `requirements.txt`, and install any extra packages needed for the selected model or premise-selection setup.

The next task is to install Isabelle2025 and make sure the `isabelle` command works from the terminal. This is essential because both the stepwise prover and planner depend on Isabelle for proof checking. After that, install or configure the chosen LLM backend. Ollama can be used locally if the machine can run the selected model. Gemini can be used if API access is available.

Once the environment is ready, run the smoke tests:

```powershell
python -m prover.cli --goal "rev (rev xs) = xs"
python -m planner.cli --timeout 60 --mode auto "rev (rev xs) = xs"
```

Person 1 should record the exact setup used: operating system, Python version, Isabelle version, model/backend, CPU, RAM, and GPU if available. They should also document any setup problems and how they were fixed, because this information is needed in the implementation and experiment section of the report.

Expected output from Person 1:

- working `.venv`;
- confirmed Isabelle terminal access;
- confirmed LLM backend access;
- smoke test results;
- setup notes for the report.

## Person 2: Baseline Experiments

Person 2 is responsible for running the baseline systems so we can compare our improved planner against the original behaviour.

The first baseline is the stepwise prover. Run it on the smaller built-in datasets first: `datasets/lists.txt`, `datasets/nat.txt`, `datasets/sets.txt`, and `datasets/logic.txt`. Use consistent timeout and model settings so the results can be compared fairly with the improved planner.

Example command:

```powershell
python -m prover.experiments bench --suite lists --beam 3 --max-depth 8 --timeout 60 --sledge --quickcheck --nitpick --reranker on --model "qwen3-coder:30b"
```

The second baseline is Sledgehammer-only. This should be run using `baselines/sledge_only.py`.

Example command:

```powershell
python baselines/sledge_only.py --file datasets/lists.txt --imports Main --sledge-timeout 60 --goal-timeout 60 --print-logs
```

For each run, Person 2 should record success rate, runtime, timeout count, and any common failure patterns. CSV/log outputs should be saved and named clearly so they can be used later in the report.

Expected output from Person 2:

- stepwise prover baseline results;
- Sledgehammer-only baseline results;
- CSV/log files saved;
- short summary of baseline performance and failure patterns.

## Person 3: Improved Planner Evaluation

Person 3 is responsible for evaluating the improved planner with fill and repair enabled.

Start with the smaller built-in datasets: `lists.txt`, `nat.txt`, `sets.txt`, and `logic.txt`. After that, run the synthetic easy, mid, and hard datasets if time allows. These files are useful because they give a controlled spread of difficulty while staying within standard HOL imports.

Example command:

```powershell
python -m planner.experiments bench --suite lists --mode auto --diverse --k 3 --timeout 120 --verify --strict-no-sorry --beam-k 2 --whole-fallback --model "qwen3-coder:30b"
```

If the environment is stable and there is enough time, Person 3 should also run miniF2F and PutnamBench. These are important because the rubric gives strong marks for multiple datasets from different sources. The external datasets help show that the system is being tested beyond toy examples.

For each run, record success rate, runtime, number of filled holes, number of failed holes, whether the final proof still contains `sorry`, and Isabelle verification status. The most important metric for the improved planner is verified no-`sorry` proofs.

Expected output from Person 3:

- improved planner results for built-in datasets;
- synthetic dataset results if possible;
- miniF2F and PutnamBench results if possible;
- CSV/log files saved;
- short summary comparing planner behaviour across easy and harder goals.

## Person 4: Report Writing, Background, And References

Person 4 is responsible for preparing the main written foundation of the LNCS report.

The report must follow LNCS format and stay under 16 pages including references. It must include an abstract under 500 words, introduction, related work, proposed approach, implementation and experiments, discussion/conclusion, data availability, and references.

Person 4 should write the introduction and related work in our own words. The introduction should explain the background of Isabelle/HOL, automated reasoning, and why LLM-guided theorem proving is useful. It should also summarise what our project contributes: making planner-level hole filling and staged proof repair work on top of the base repository.

The related work section should cover Isabelle/HOL, Sledgehammer, LLM-guided theorem proving, the original Isabellm paper/repository, miniF2F, and PutnamBench. At the end of related work, include a short comparison explaining how our work differs from or extends the related systems.

Person 4 should also collect and format references properly. The assignment asks references to include authors, title, year, and venue where applicable. For code libraries and repositories, include URLs.

Expected output from Person 4:

- LNCS report skeleton;
- abstract draft;
- introduction draft;
- related work draft;
- reference list draft;
- notes on citations still needed.

## Person 5: Results, Figures, Discussion, And Final Assembly

Person 5 is responsible for turning the implementation and experiment results into the final report story.

First, convert `docs/architecture.md` into a clean figure for the proposed approach section. The figure should show the workflow from input goal, to LLM outline generation, Isabelle checking, earliest failure selection, hole filling, staged repair, whole-proof fallback, and final verification/logging.

Next, create result tables from the experiment outputs. The report should compare at least the stepwise prover baseline, the Sledgehammer-only baseline, and the improved planner system. Tables should include success rate, number of solved goals, median runtime, timeout/failure count, and verified no-`sorry` proof count where possible.

Person 5 should write the proposed approach section using the architecture figure and implementation notes. They should also write the implementation and experiment section once Persons 1-3 provide setup details and results. This section should mention programming language, main libraries, Isabelle version, model/backend, datasets, timeout settings, and evaluation method.

The discussion/conclusion should explain the limitations of the work and future improvements. Good limitations to discuss include model quality, setup complexity, slow external benchmarks, LLM syntax errors, proof-state extraction issues, and remaining repair failure cases. Future work can include stronger premise selection, better proof-state prompting, more robust whole-proof regeneration, and larger reranker training.

Person 5 should also maintain the AI-use appendix using `docs/ai_use_log.md` and add the Data Availability section once the final GitHub repository URL is available.

Expected output from Person 5:

- architecture/workflow figure;
- experiment result tables;
- proposed approach section;
- implementation and experiment section;
- discussion/conclusion section;
- Data Availability sentence;
- AI-use appendix;
- final formatting pass.

## Shared Standards

Everyone should keep outputs clear and reproducible. Any command that produces results should be saved or written down with the model, timeout, dataset, and date. Do not overwrite useful logs without backing them up.

The code should stay readable and not over-commented. Comments should only be added where they explain non-obvious logic. The assignment report should be written in our own words, even if AI was used for planning, code help, or editing support.

All experiment results should be treated honestly. If a dataset fails because of setup, timeout, missing Isabelle imports, model limits, or API issues, record that clearly. It is better to explain limitations properly than to hide them.

## Immediate Next Steps

The first priority is environment setup. Without Isabelle2025 and a compatible Python environment, the project cannot be tested end-to-end.

After the environment works, run the two smoke tests. If both pass, run the baseline experiments and improved planner experiments on the small datasets. Once those results are collected, move to synthetic datasets and then external datasets if time allows.

The report should be built in parallel. Person 4 can start the introduction and related work immediately. Person 5 can start the architecture figure and proposed approach immediately. Results tables can be filled in once Persons 2 and 3 complete the experiment runs.

## Teams Message

Hey everyone, quick update on Assignment 2.

I’ve reviewed the task sheet and marking rubric against the cloned `llm-isabelle` repo. The assignment requires an LLM-guided Isabelle/HOL prover with both a stepwise prover and an Isar-style planner. Since the base repo already has a lot implemented, our main focus is completing the WIP planner features: filling Isar `sorry` holes using the stepwise prover, and doing staged CEGIS-style proof repair.

So far, I’ve inspected the repo structure and made the first implementation pass. The planner repair flags are now properly wired, the staged repair loop has been improved so it escalates instead of getting stuck, repair attempts now respect the beam/attempt settings, and experiment logs now include useful configuration details. I’ve also added docs for setup, evaluation, report structure, the architecture figure, and AI-use logging.

The biggest blocker now is environment setup. We need Python 3.10-3.12, Isabelle2025 on PATH, dependencies installed, and an Ollama or Gemini model configured before we can run proper end-to-end tests.

Suggested split: one person handles environment and smoke testing, one person handles stepwise prover and Sledgehammer baselines, one person handles improved planner evaluation, one person handles the report introduction/related work/citations, and one person handles result tables, figures, discussion, and final formatting.

Once the environment is working, we should run the baseline and improved system on the same datasets, collect success rates and runtimes, then use those results in the LNCS report.


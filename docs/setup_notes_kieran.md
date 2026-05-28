\# Setup Notes — Kieran Ward

\*\*Date:\*\* 21/05/2026  

\*\*Project:\*\* Isabelle-LLM-Assignment-2



\---



\# Notes on Portability



The commands and troubleshooting below reflect a Windows setup.



Linux/macOS users may require different:



\- shell syntax

\- environment variables

\- executable paths

\- dependency installation methods



Avoid storing repositories or large dependencies inside cloud-sync folders

(e.g. OneDrive) where possible.



\---



\# Environment Configuration



| Component | Value |

|-----------|--------|

| Operating System | Windows |

| Python Version | 3.11.9 |

| Isabelle Version | Isabelle2025-2 |

| Virtual Environment | Created and active (`.venv`) |

| Ollama | Installed |

| Repository | Cloned from shared GitHub |



Project stored locally outside cloud-synchronised folders.



\---



\# Completed Setup Tasks



\## Repository \& Environment



✓ Installed Git  

✓ Cloned repository  

✓ Moved project outside OneDrive to reduce path/sync issues  

✓ Created Python 3.11 virtual environment  

✓ Installed dependencies from `requirements.txt`  

✓ Verified `isabelle\_client` imports successfully  



\---



\## Isabelle Configuration



Completed:



✓ Installed Isabelle2025-2  

✓ Configured environment variables/PATH  

✓ Verified Isabelle executable accessible through terminal  

✓ Confirmed Isabelle server launches  



Persistent environment variable required:



Windows example:



```powershell

\[Environment]::SetEnvironmentVariable(

"ISABELLE\_INST\_DIR",

"<path-to-Isabelle-install>",

"User"

)

```



Example used during setup:



```powershell

\[Environment]::SetEnvironmentVariable(

"ISABELLE\_INST\_DIR",

"C:\\Tools\\Isabelle2025-2",

"User"

)

```



Verification:



```bash

isabelle version

→ Isabelle2025-2

```



\---



\# Initial Runtime Test



\### Command



```powershell

python -m prover.cli

```



\### Result



\- Ollama connection timeout

\- Isabelle startup failure:



```text

ValueError: Unexpected server info

```



\### Interpretation



Environment partially functional.



Outstanding issues:



1\. Configure Ollama

2\. Diagnose Isabelle server startup



\---



\# Ollama Configuration



\### Check



```powershell

ollama --version

```



\### Result



Command not recognised.



\### Resolution



Installed Ollama for Windows.



\---



\# Prover Smoke Test After Ollama



\### Command



```powershell

python -m prover.cli --model "gemma3:4b"

```



\### Result



Ollama issue resolved.



Remaining error:



```text

ValueError: Unexpected server info

```



\### Interpretation



LLM backend functioning.



Issue isolated to Isabelle startup.



\---



\# Major Milestone: Isabelle Server Working



\### Command



Temporary session variable:



```powershell

$env:ISABELLE\_INST\_DIR="<path-to-Isabelle-install>"

```



Then:



```powershell

python -m prover.cli --model "gemma3:4b"

```



\### Result



Successfully:



✓ Started Isabelle server  

✓ Started HOL session  

✓ Generated session ID  

✓ Executed prover pipeline  



Output:



```text

FAILED | depth: 1

```



\### Interpretation



Environment setup effectively complete.



Work transitioned from:



\*\*Configuration debugging → Proof generation behaviour\*\*



\---



\# Baseline Experiment Smoke Test



\### Command



```powershell

python baselines\\sledge\_only.py `

\--file datasets\\logic.txt `

\--imports Main `

\--provers "e z3 vampire cvc5" `

\--sledge-timeout 60 `

\--goal-timeout 60 `

\--print-logs

```



\### Result



Script loaded goals successfully but failed during subprocess execution:



```text

FileNotFoundError

```



\---



\### Findings



Missing theorem provers on PATH:



\- `e`

\- `z3`

\- `cvc5`

\- `vampire`



Observed code:



```python

ISABELLE\_BIN = os.environ.get("ISABELLE\_BIN", "isabelle")

```



Direct PowerShell invocation appears problematic under Windows.



\---



\# Isabelle Subprocess Investigation



\### Test



Executed Isabelle through bundled Cygwin bash:



```bash

/cygdrive/c/.../Isabelle/bin/isabelle version

```



\### Result



```text

Isabelle2025-2

```



\### Interpretation



Isabelle installation is valid.



Failure source appears to be:



\*\*Windows subprocess invocation rather than Isabelle itself\*\*



Current hypothesis:



Windows systems may require launching Isabelle through bundled

Cygwin paths rather than direct PowerShell execution.



Linux/macOS behaviour not yet tested.



\---



\# Current Status



Environment status:



✓ Git configured  

✓ Python 3.11 functioning  

✓ Virtual environment functioning  

✓ Dependencies installed  

✓ Ollama working  

✓ Isabelle installed  

✓ Isabelle server launches  

✓ `prover.cli` executes  

✓ HOL session starts  



\---



\# Remaining Work



Outstanding tasks:



\- Patch baseline execution for Windows compatibility

\- Install/add theorem provers (`z3`, `e`, `vampire`, `cvc5`)

\- Run baseline benchmarks

\- Run planner benchmarks

\- Compare baseline vs planner performance

\- Document results for report



\---



\# Contribution Summary (Current)



Primary contributions so far:



\- Windows environment setup

\- Dependency installation

\- Isabelle configuration/debugging

\- Runtime troubleshooting

\- Baseline execution investigation

\- Cross-platform compatibility observations

\- Setup documentation



\---



\# Key Findings



1\. Python 3.11 works correctly with project dependencies.

2\. Isabelle requires `ISABELLE\_INST\_DIR` to be configured on Windows.

3\. Isabelle server launches successfully once environment variables are configured.

4\. Baseline execution currently appears limited by Windows subprocess behaviour and missing prover dependencies.

5\. Environment setup is complete enough to begin experiments.


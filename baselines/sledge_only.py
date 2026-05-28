#!/usr/bin/env python3
r"""
sledge_only.py — Standalone Sledgehammer-only runner (headless Isabelle).

Flow
1) Create a throwaway session with your goal and `sledgehammer [...]` inside `oops`.
2) `isabelle build` it (no docs/browser info).
3) Read the Sledgehammer suggestion ("Try this: by …") from the session log:
   - scan $ISABELLE_OUTPUT/log for latest SledgeOnly* (supports .gz),
   - else `isabelle build_log SledgeOnly` (no flags),
   - else `isabelle process` in the temp dir to print messages directly.
4) Re-write lemma to `by (…)` and rebuild to confirm.

Notes
- Converts Unicode (∈ ∪ ⟹ λ etc.) to Isabelle escapes (\<in> \<union> \<Longrightarrow> \<lambda> …).
- Imports default to `Main`; if `List` is also given alongside `Main`, it is stripped (Main already includes it).
- You can pick provers (e.g., "e vampire z3 cvc5"). If you only have some installed, narrow it (e.g., "z3 e").
"""

from __future__ import annotations
import argparse
import gzip
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

ISABELLE_BIN = os.environ.get("ISABELLE_BIN", "isabelle")
ISABELLE_INST_DIR = os.environ.get("ISABELLE_INST_DIR", "").strip()

# ---------- Unicode → Isabelle ----------
UNICODE_MAP = {
    "⟹": r"\<Longrightarrow>", "⇒": r"\<Longrightarrow>",
    "⟶": r"\<longrightarrow>", "→": r"\<longrightarrow>",
    "⟷": r"\<longleftrightarrow>", "↔": r"\<longleftrightarrow>",
    "¬": r"\<not>", "∧": r"\<and>", "∨": r"\<or>",
    "∀": r"\<forall>", "∃": r"\<exists>", "⋀": r"\<And>",
    "≤": r"\<le>", "≥": r"\<ge>", "≠": r"\<noteq>",
    "⊆": r"\<subseteq>", "⊇": r"\<supseteq>", "⊂": r"\<subset>", "⊃": r"\<supset>",
    "∈": r"\<in>", "∉": r"\<notin>",
    "∪": r"\<union>", "∩": r"\<inter>", "∖": r"\<setminus>",
    "⋃": r"\<Union>", "⋂": r"\<Inter>",
    "λ": r"\<lambda>",
}
UNICODE_RE = re.compile("|".join(map(re.escape, sorted(UNICODE_MAP.keys(), key=len, reverse=True))))

def to_isabelle_symbols(s: str) -> str:
    return UNICODE_RE.sub(lambda m: UNICODE_MAP[m.group(0)], s)

# ---------- Shell helpers ----------
def _cygpath(path: str) -> str:
    p = path.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", p):
        return f"/cygdrive/{p[0].lower()}{p[2:]}"
    return p

def _winpath(path: str) -> str:
    p = path.replace("\\", "/")
    m = re.match(r"^/cygdrive/([A-Za-z])/(.*)$", p)
    if not m:
        return path
    rest = m.group(2).replace("/", "\\")
    return f"{m.group(1).upper()}:\\{rest}"

def _is_pathish(s: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", s)) or "\\" in s

def _run_isabelle_windows(cmd: List[str], cwd: Optional[str], timeout: Optional[int]) -> Tuple[int, str, str]:
    if not ISABELLE_INST_DIR:
        return 127, "", "ISABELLE_INST_DIR is not set"
    bash = Path(ISABELLE_INST_DIR) / "contrib" / "cygwin" / "bin" / "bash.exe"
    if not bash.exists():
        return 127, "", f"Could not find Isabelle Cygwin bash: {bash}"

    args = []
    for part in cmd[1:]:
        s = str(part)
        if _is_pathish(s):
            s = _cygpath(s)
        args.append(shlex.quote(s))

    prefix = ""
    if cwd:
        prefix = "cd " + shlex.quote(_cygpath(cwd)) + " && "
    script = prefix + "isabelle " + " ".join(args)
    p = subprocess.run([str(bash), "-lc", script], capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or ""), (p.stderr or "")

def run(cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    try:
        if sys.platform == "win32" and cmd and cmd[0] == ISABELLE_BIN:
            return _run_isabelle_windows(cmd, cwd, timeout)
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode() if e.stdout else "")
        err = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else "")
        return 124, out, err + "\n[TIMEOUT]"

def isabelle_getenv(name: str) -> Optional[str]:
    rc, out, _ = run([ISABELLE_BIN, "getenv", "-b", name])
    return out.strip() if rc == 0 and out.strip() else None

# ---------- Session files ----------
def write_root(dirpath: Path, session_name: str, theories: List[str]) -> None:
    text = f"session {session_name} = HOL +\n  theories\n" + "".join(f"    {t}\n" for t in theories)
    (dirpath / "ROOT").write_text(text, encoding="utf-8")

def sanitize_imports(imports: List[str]) -> List[str]:
    imps = list(dict.fromkeys(imports))
    if "Main" not in imps:
        imps.insert(0, "Main")
    # Explicit 'List' can trigger local lookup in a fresh session; Main already includes it.
    if "List" in imps and "Main" in imps:
        imps = [x for x in imps if x != "List"]
    return imps

def thy_probe_text(theory: str, imports: List[str], goal: str, sh_timeout: int, provers: Optional[str]) -> str:
    imps = " ".join(sanitize_imports(imports))
    g = to_isabelle_symbols(goal)
    header = f'theory {theory}\n  imports {imps}\nbegin\n'
    opts = [f"timeout = {sh_timeout}", "verbose"]  # 'verbose' encourages a visible “Try this:”
    if provers:
        opts.append(f"provers = {provers}")
    sh = "  sledgehammer [" + ", ".join(opts) + "]\n"
    return header + "\n" + f'lemma "{g}"\n' + sh + "  oops\nend\n"

def thy_by_text(theory: str, imports: List[str], goal: str, by_text: str) -> str:
    imps = " ".join(sanitize_imports(imports))
    g = to_isabelle_symbols(goal)
    header = f'theory {theory}\n  imports {imps}\nbegin\n'
    return header + "\n" + f'lemma "{g}"\n  {by_text}\nend\n'

# ---------- Build + capture ----------
def build_session(dirpath: Path, session: str, timeout: int) -> Tuple[int, str, str]:
    return run([
        ISABELLE_BIN, "build",
        "-D", str(dirpath),
        "-o", "document=false",
        "-o", "browser_info=false",
        "-o", "parallel_proofs=0",
        "-o", "threads=1",
        session
    ], cwd=str(dirpath), timeout=timeout)

def read_log_from_store(session: str) -> str:
    out_dir = isabelle_getenv("ISABELLE_OUTPUT")
    if not out_dir:
        return ""
    log_dir = Path(_winpath(out_dir)) / "log"
    if not log_dir.is_dir():
        return ""
    # pick newest matching file
    candidates = list(log_dir.glob(f"{session}*"))
    if not candidates:
        return ""
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    p = candidates[0]
    try:
        if p.suffix == ".gz":
            with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
                return f.read()
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        try:
            return p.read_bytes().decode("utf-8", errors="replace")
        except Exception:
            return ""

def read_log_via_build_log(session: str) -> str:
    # Very conservative: no flags — some Isabelle versions have different options.
    rc, out, err = run([ISABELLE_BIN, "build_log", session])
    text = (out or "") + ("\n" + err if err else "")
    # ignore the usage banner if that’s all we got
    if "Usage: isabelle build_log" in text and len(text.strip().splitlines()) < 20:
        return ""
    return text.strip()

# ---------- Suggestion parsing ----------
TRY_THIS = re.compile(r"Try this:\s*(.*)")
BY_PAREN = re.compile(r"\bby\s*\([^)]*\)")
TIMING_TAIL = re.compile(r"\s*\(\s*\d+(?:\.\d+)?\s*(?:ms|s)\s*\)\s*$")

def clean_suggestion(s: str) -> str:
    s = TIMING_TAIL.sub("", s)  # drop trailing "(0.8 ms)" etc.
    s = s.rstrip(".")           # drop trailing period if present
    return s.strip()

def extract_suggestions(text: str) -> List[str]:
    lines = text.splitlines()
    out: List[str] = []

    # Primary: “Try this: …”
    for i, ln in enumerate(lines):
        m = TRY_THIS.search(ln)
        if not m:
            continue
        s = m.group(1).strip()
        # naive continuation
        if i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt.startswith("by ") or (s and not s.endswith(".")) and nxt and not nxt.endswith(":"):
                s = (s + " " + nxt).strip()
        s = clean_suggestion(s)
        if s.startswith("by ") or " by " in s:
            if s not in out:
                out.append(s)

    # Secondary: plain “by (metis …)” occurrences (without “Try this:”)
    for ln in lines:
        m = BY_PAREN.search(ln)
        if m:
            s = "by " + m.group(0)[3:].strip()
            s = clean_suggestion(s)
            if s not in out:
                out.append(s)

    return out

# ---------- Prove one goal ----------
def prove_with_isabelle_server(goal: str, sh_timeout: int, isabelle: Any, session_id: str) -> Tuple[bool, Optional[str], str]:
    try:
        from prover.tactics import sledgehammer_finishers
        from prover.prover import try_finish
    except Exception as ex:
        return False, None, f"server_import_error: {type(ex).__name__}: {ex}"

    steps = [f'lemma "{to_isabelle_symbols(goal)}"']
    try:
        suggestions = sledgehammer_finishers(
            isabelle, session_id, steps, timeout_s=sh_timeout, limit=8
        )
    except Exception as ex:
        return False, None, f"server_sledge_error: {type(ex).__name__}: {ex}"

    log = "server suggestions: " + repr(suggestions)
    for by in suggestions:
        try:
            ok, _ = try_finish(isabelle, session_id, steps, by, timeout_s=max(5, sh_timeout))
        except Exception:
            ok = False
        if ok:
            return True, by, log

    return False, None, log


def prove_with_sledgehammer(goal: str, imports: List[str], sh_timeout: int, timeout: int,
                            provers: Optional[str], isabelle: Any = None,
                            session_id: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
    if isabelle is not None and session_id:
        ok, method, log = prove_with_isabelle_server(goal, sh_timeout, isabelle, session_id)
        if ok:
            return ok, method, log

    with tempfile.TemporaryDirectory(prefix="sledge_only_") as tmp:
        tmp = Path(tmp)
        session = "SledgeOnly"
        theory = "SledgeOnly"

        write_root(tmp, session, [theory])
        (tmp / f"{theory}.thy").write_text(
            thy_probe_text(theory, imports, goal, sh_timeout, provers), encoding="utf-8"
        )

        # Build (so the session gets logged)
        _, build_out, build_err = build_session(tmp, session, timeout)

        # Try to read the log (store → build_log → process fallback)
        text = read_log_from_store(session)
        if not text.strip():
            text = read_log_via_build_log(session)
        if not text.strip():
            text = (build_out or "") + ("\n" + build_err if build_err else "")

        suggestions = extract_suggestions(text)

        # Validate the first proof that checks
        for by in suggestions:
            (tmp / f"{theory}.thy").write_text(thy_by_text(theory, imports, goal, by), encoding="utf-8")
            rc2, _, _ = build_session(tmp, session, timeout)
            if rc2 == 0:
                return True, by, text

        return False, None, text

# ---------- CLI ----------
def read_goals(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sledgehammer-only runner (headless Isabelle)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--goal", type=str)
    src.add_argument("--file", type=str)
    ap.add_argument("--imports", nargs="+", default=["Main"])
    ap.add_argument("--sledge-timeout", type=int, default=10)
    ap.add_argument("--goal-timeout", type=int, default=60)
    ap.add_argument("--provers", type=str, default=None)
    ap.add_argument("--print-logs", action="store_true")
    ap.add_argument("--log-lines", type=int, default=28)
    return ap.parse_args()

def print_log_snippet(text: str, n: int) -> None:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        print("(no log)")
        return
    head = lines[:n]
    tail = lines[-n:] if len(lines) > n else []
    print("----- Sledgehammer log (head) -----")
    for ln in head:
        print(ln)
    if tail:
        print("----- Sledgehammer log (tail) -----")
        for ln in tail:
            print(ln)

def main() -> None:
    args = parse_args()
    goals = [args.goal] if args.goal else read_goals(args.file)
    print("=== Sledgehammer-only (standalone) ===")
    print(f"Goals: {len(goals)} | imports: {' '.join(sanitize_imports(args.imports))} | "
          f"sledge-timeout: {args.sledge_timeout}s | goal-timeout: {args.goal_timeout}s")

    isabelle = None
    session_id = None
    server_proc = None
    try:
        from prover.config import ISABELLE_SESSION
        from prover.isabelle_api import extract_session_id, get_isabelle_client, start_isabelle_server
        server_info, server_proc = start_isabelle_server(name="sledge-only", log_file="logs/sledge_only_server.log")
        isabelle = get_isabelle_client(server_info)
        session_id = extract_session_id(isabelle.session_start(session=ISABELLE_SESSION))
    except Exception as ex:
        print(f"[warn] Isabelle server path unavailable; falling back to build logs: {type(ex).__name__}: {ex}")

    ok = 0
    times: List[float] = []
    try:
        for i, g in enumerate(goals, 1):
            print(f"[{i}/{len(goals)}] {g}")
            t0 = time.time()
            success, method, log = prove_with_sledgehammer(
                g, args.imports, args.sledge_timeout, args.goal_timeout, args.provers,
                isabelle=isabelle, session_id=session_id,
            )
            dt = time.time() - t0
            times.append(dt)
            if success:
                ok += 1
                print(f"  -> OK    ({dt:.2f}s)  {method}")
            else:
                print(f"  -> FAIL  ({dt:.2f}s)")
                if args.print_logs:
                    print_log_snippet(log, args.log_lines)
    finally:
        try:
            if isabelle is not None:
                isabelle.shutdown()
        except Exception:
            pass
        try:
            if server_proc is not None:
                server_proc.terminate()
        except Exception:
            pass

    mid = sorted(times)[len(times)//2] if times else 0.0
    avg = sum(times)/len(times) if times else 0.0
    print("\n=== Summary ===")
    print(f"Success: {ok}/{len(goals)} ({(ok/max(1,len(goals))*100):.1f}%)")
    print(f"Median time: {mid:.2f}s | Average time: {avg:.2f}s")

if __name__ == "__main__":
    main()

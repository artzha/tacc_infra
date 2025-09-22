from __future__ import annotations
import sys, os, subprocess, shutil
from pathlib import Path

try:
    from importlib.resources import files as res_files
except ImportError:  # Py3.8 fallback
    from importlib_resources import files as res_files  # type: ignore

def _repo_root_from_git() -> Path | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL, text=True
        )
        return Path(out.strip())
    except Exception:
        return None

def _resolve_infra_dir() -> Path:
    env_dir = os.environ.get("TACCENV_INFRA")
    if env_dir:
        p = Path(env_dir).expanduser()
        if p.is_dir():
            return p

    repo = _repo_root_from_git()
    if repo and (repo / "src" / "tacc_infra").is_dir():
        return repo / "src" / "tacc_infra"
    if repo and (repo / "tacc_infra").is_dir():
        return repo / "tacc_infra"

    pkg_dir = res_files("tacc_infra")
    return Path(str(pkg_dir))

def _list_script_paths(infra: Path) -> list[Path]:
    exts = {".sh", ".py"}
    out: list[Path] = []
    for p in infra.rglob("*"):
        if p.is_file() and (p.suffix in exts or os.access(p, os.X_OK)):
            out.append(p)
    return sorted(out)

def _list_script_names(infra: Path) -> list[str]:
    """Names suitable for completion: relative paths (no extension) and basenames (no extension)."""
    paths = _list_script_paths(infra)
    rels = []
    bases = []
    for p in paths:
        rel = p.relative_to(infra)
        rel_noext = rel.with_suffix("") if rel.suffix in {".sh", ".py"} else rel
        base_noext = p.stem
        rels.append(str(rel_noext))
        bases.append(base_noext)
    # de-dup while preserving order
    seen = set()
    ordered = []
    for x in rels + bases:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return ordered

def _resolve_script(infra: Path, name: str) -> Path | None:
    candidate = infra / name
    if candidate.is_file():
        return candidate
    for ext in (".sh", ".py"):
        c = infra / f"{name}{ext}"
        if c.is_file():
            return c
    matches = [p for p in infra.rglob("*") if p.is_file() and p.stem == name]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        rels = "\n  - " + "\n  - ".join(str(p.relative_to(infra)) for p in matches)
        print(f"taccenv: multiple matches for '{name}':{rels}", file=sys.stderr)
        return None
    return None

def _usage(infra: Path) -> str:
    items = "\n".join(f"  - {n}" for n in _list_script_names(infra))
    return f"""Usage:
  taccenv <scriptname> [args...]

Runs scripts from: {infra}

Examples:
  taccenv build_image --tag dev
  taccenv submit_job --time 02:00:00

Available scripts:
{items if items else '  (no scripts found)'}
"""

def main() -> None:
    infra = _resolve_infra_dir()

    # Completion helpers:
    if len(sys.argv) >= 2 and sys.argv[1] == "--list":
        # print one per line, no extra text
        print("\n".join(_list_script_names(infra)))
        return

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(_usage(infra))
        return

    name, *args = sys.argv[1:]
    target = _resolve_script(infra, name)
    if not target:
        print(f"taccenv: no script named '{name}' in {infra}", file=sys.stderr)
        print(_usage(infra))
        sys.exit(1)

    # Execute
    if target.suffix == ".py":
        python = shutil.which("python3") or "python3"
        os.execvp(python, [python, str(target), *args])
    elif target.suffix == ".sh" or os.access(target, os.X_OK):
        shell = shutil.which("bash") or "/bin/bash"
        os.execvp(shell, [shell, str(target), *args])
    else:
        shell = shutil.which("bash") or "/bin/bash"
        os.execvp(shell, [shell, str(target), *args])

if __name__ == "__main__":
    main()

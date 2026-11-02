"""Build and validate a portable Interview Intel Skill ZIP for Chinese marketplaces."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ("SKILL.md", "LICENSE", "README.md", "references", "scripts", "examples", "agents")
MAX_BYTES = 10 * 1024 * 1024


def collect() -> list[Path]:
    selected: list[Path] = []
    for name in INCLUDE:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(f"Missing required project component: {path}")
        candidates = (path,) if path.is_file() else sorted(path.rglob("*"))
        for candidate in candidates:
            if (not candidate.is_file() or candidate.is_symlink()
                    or any(part in {"__pycache__", ".git", "__MACOSX"} for part in candidate.parts)
                    or candidate.name == ".DS_Store" or candidate.suffix in {".pyc", ".pyo"}):
                continue
            selected.append(candidate)
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\n") or "\nname: interview-intel\n" not in skill or "\ndescription:" not in skill:
        raise ValueError("SKILL.md must have the expected YAML frontmatter")
    return selected


def package(output: Path, layout: str) -> tuple[int, int]:
    files = collect()
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = "" if layout == "qwen-ai" else "interview-intel/"
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=8) as archive:
        for source in files:
            archive.write(source, prefix + source.relative_to(ROOT).as_posix())

    with ZipFile(output) as archive:
        names = archive.namelist()
        expected = prefix + "SKILL.md"
        if expected not in names:
            raise ValueError(f"ZIP validation failed: {expected} missing")
        if any(name.endswith("/SKILL.md") and name != expected for name in names):
            raise ValueError("ZIP validation failed: unexpected nested SKILL.md")
        if any(name.startswith("../") or "/../" in name for name in names):
            raise ValueError("ZIP validation failed: unsafe path")
        if archive.testzip() is not None:
            raise ValueError("ZIP validation failed: corrupt member")

    size = output.stat().st_size
    if size > MAX_BYTES:
        raise ValueError(f"ZIP exceeds marketplace 10 MiB limit: {size} bytes")
    print(f"Created: {output}")
    print(f"Layout: {layout} | Files: {len(names)} | Size: {size} bytes")
    print(f"Verified skill entry: {expected}")
    return len(names), size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("qwen-ai", "qwenwork"), default="qwen-ai",
                        help="qwen-ai puts SKILL.md at ZIP root; qwenwork uses interview-intel/SKILL.md")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "interview-intel-skill.zip")
    arguments = parser.parse_args()
    package(arguments.output, arguments.format)


if __name__ == "__main__":
    main()

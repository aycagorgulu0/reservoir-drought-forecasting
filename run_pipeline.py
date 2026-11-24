"""Run the whole pipeline: every numbered script in src/, in order.

Step numbers follow the KDD phases:
    0x  data selection and understanding
    1x  preprocessing (cleaning, monthly aggregation)
    2x  integration of other sources (rainfall, climate indices)
    3x  transformation (labels, features)
    4x  data mining (models, clustering)
    5x  evaluation

Usage (from anywhere):
    python run_pipeline.py              run every step
    python run_pipeline.py --list       show the steps without running them
    python run_pipeline.py --from 10    start at step 10
    python run_pipeline.py --only 03    run a single step

If data/raw/BD-Embalses.mdb is missing but the converted CSV exists, steps 00-01
(which read the Access file) are skipped automatically.
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
from paths import MDB, WEEKLY_CSV  # noqa: E402

STEP = re.compile(r"^(\d{2})_.+\.py$")
NEEDS_MDB = {"00", "01"}


def find_steps():
    steps = []
    for f in sorted(SRC.glob("*.py")):
        m = STEP.match(f.name)
        if m:
            steps.append((m.group(1), f))
    return steps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", help="first step number to run, e.g. 10")
    ap.add_argument("--only", help="run only this step number, e.g. 03")
    ap.add_argument("--list", action="store_true", help="list the steps and exit")
    args = ap.parse_args()

    steps = find_steps()
    if args.only:
        steps = [s for s in steps if s[0] == args.only.zfill(2)]
    elif args.start:
        steps = [s for s in steps if s[0] >= args.start.zfill(2)]
    if not steps:
        sys.exit("No matching steps in src/.")

    if args.list:
        for num, f in steps:
            print(f"{num}  {f.name}")
        return

    skip_mdb = not MDB.exists()
    if skip_mdb and not WEEKLY_CSV.exists():
        sys.exit(f"Missing {MDB.relative_to(ROOT)}. See data/README.md for how to download it.")

    total = time.time()
    for num, f in steps:
        if skip_mdb and num in NEEDS_MDB:
            print(f"--- {f.name}: skipped (no .mdb; using existing {WEEKLY_CSV.name})")
            continue
        print(f"=== {f.name}", flush=True)
        t = time.time()
        result = subprocess.run([sys.executable, str(f)], cwd=ROOT)
        if result.returncode != 0:
            sys.exit(f"Step {f.name} failed (exit code {result.returncode}). Stopping.")
        print(f"--- {f.name}: done in {time.time() - t:.1f}s\n", flush=True)
    print(f"Pipeline finished in {time.time() - total:.1f}s")


if __name__ == "__main__":
    main()

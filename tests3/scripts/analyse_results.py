#!/usr/bin/env python3

import re
import csv
from pathlib import Path

ROOT = Path.home()

WORKLOAD_DIRS = [
    "sched_results1",
    "sched_results2",
    "sched_results4",
    "sched_results5",
]

OUTPUT_CSV = "all_results.csv"

rows = []

def extract_number(line):

    line = line.replace(",", "")

    m = re.search(r'([0-9]+(?:\.[0-9]+)?)', line)

    if m:
        return float(m.group(1))

    return None


for workload_name in WORKLOAD_DIRS:

    workload_root = ROOT / workload_name

    if not workload_root.exists():
        continue

    for mode_dir in workload_root.iterdir():

        if not mode_dir.is_dir():
            continue

        mode = mode_dir.name

        for cpu_dir in mode_dir.iterdir():

            if not cpu_dir.is_dir():
                continue

            workers = int(cpu_dir.name.replace("cpu", ""))

            for run_dir in cpu_dir.iterdir():

                if not run_dir.is_dir():
                    continue

                run = int(run_dir.name.replace("run", ""))

                perf_file = run_dir / "perf_stat.txt"

                if not perf_file.exists():
                    continue

                data = {
                    "workload": workload_name,
                    "mode": mode,
                    "workers": workers,
                    "run": run,
                    "task_clock": None,
                    "context_switches": None,
                    "cpu_migrations": None,
                    "cycles": None,
                    "instructions": None,
                    "ipc": None,
                    "elapsed_time": None,
                }

                with open(perf_file) as f:
                    lines = f.readlines()

                for line in lines:

                    if "task-clock" in line:
                        data["task_clock"] = extract_number(line)

                    elif "context-switches" in line:
                        data["context_switches"] = extract_number(line)

                    elif "cpu-migrations" in line:
                        data["cpu_migrations"] = extract_number(line)

                    elif "cycles" in line:
                        data["cycles"] = extract_number(line)

                    elif "instructions" in line:
                        data["instructions"] = extract_number(line)

                        ipc_match = re.search(
                            r'#\s+([0-9.]+)\s+insn per cycle',
                            line
                        )

                        if ipc_match:
                            data["ipc"] = float(ipc_match.group(1))

                    elif "seconds time elapsed" in line:
                        data["elapsed_time"] = extract_number(line)

                rows.append(data)

with open(OUTPUT_CSV, "w", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=rows[0].keys()
    )

    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")

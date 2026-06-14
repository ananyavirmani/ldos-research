import os
import re
import csv

ROOT = "results_2026-06-07_00-51-40"
SCHEDULER = "top3_random"


# -----------------------------
# Throughput
# -----------------------------
def parse_throughput(path):
    try:
        with open(path, "r") as f:
            for line in f:

                if "stress-ng: metrc:" not in line:
                    continue

                if "stressor" in line:
                    continue

                parts = line.split()

                try:
                    values = [float(x) for x in parts if re.match(r'^\d+(\.\d+)?$', x)]

                    # Expect:
                    # bogo_ops real_time usr_time sys_time bogo_ops/s(real) bogo_ops/s(cpu)

                    if len(values) >= 6:
                        return values[-2]

                except:
                    pass

    except:
        pass

    return None


# -----------------------------
# Perf (FIXED)
# -----------------------------
def parse_perf(path):
    data = {
        "cs": None,
        "migrations": None,
        "cycles": None,
        "instructions": None
    }

    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()

                if "context-switches" in line:
                    data["cs"] = float(line.split(",")[0])

                elif "cpu-migrations" in line:
                    data["migrations"] = float(line.split(",")[0])

                elif "cycles" in line:
                    data["cycles"] = float(line.split(",")[0])

                elif "instructions" in line:
                    data["instructions"] = float(line.split(",")[0])

    except:
        pass

    return data


# -----------------------------
# IOSTAT (FIXED PROPERLY)
# -----------------------------
def parse_iostat(path):
    iops_samples = []

    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()

                if line.startswith("sda"):
                    parts = re.split(r"\s+", line)
                    try:
                        r_s = float(parts[1])
                        w_s = float(parts[7])
                        iops_samples.append(r_s + w_s)
                    except:
                        continue

    except:
        pass

    if len(iops_samples) == 0:
        return None

    return sum(iops_samples) / len(iops_samples)


# -----------------------------
# Main
# -----------------------------
rows = []

for workload in os.listdir(ROOT):
    w_path = os.path.join(ROOT, workload)
    if not os.path.isdir(w_path):
        continue

    for worker_dir in os.listdir(w_path):
        if not worker_dir.startswith("w"):
            continue

        workers = int(worker_dir[1:])
        wk_path = os.path.join(w_path, worker_dir)

        for run_dir in os.listdir(wk_path):
            if not run_dir.startswith("run"):
                continue

            run = int(run_dir.replace("run", ""))
            run_path = os.path.join(wk_path, run_dir)

            out_file = os.path.join(run_path, "result.out")
            perf_file = os.path.join(run_path, "result.perf")
            io_file = os.path.join(run_path, "result.iostat")

            throughput = parse_throughput(out_file)
            perf = parse_perf(perf_file)
            iops = parse_iostat(io_file)

            cycles = perf["cycles"]
            instr = perf["instructions"]

            ipc = instr / cycles if cycles and instr else None

            rows.append([
                SCHEDULER,
                workload,
                workers,
                run,
                throughput,
                perf["cs"],
                perf["migrations"],
                cycles,
                instr,
                ipc,
                iops
            ])


# -----------------------------
# Write CSV
# -----------------------------
out_file = f"{SCHEDULER}.csv"

with open(out_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "scheduler",
        "workload",
        "workers",
        "run",
        "throughput",
        "context_switches",
        "cpu_migrations",
        "cycles",
        "instructions",
        "ipc",
        "iops"
    ])
    writer.writerows(rows)

print(f"✔ Wrote {out_file}")
print(f"✔ Rows: {len(rows)}")
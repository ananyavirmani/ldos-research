import subprocess
import datetime
import pandas as pd
from pathlib import Path
import re

# === Setup output directory ===
OUTDIR = Path.home() / "scheduler_bench_results"
OUTDIR.mkdir(parents=True, exist_ok=True)

# Workloads (command, label)
WORKLOADS = {
    "CFS": ["./hackbench", "-g", "2", "-l", "100"],
    "RT-FIFO": ["sudo", "./cyclictest", "-t", "2", "-p", "80", "-i", "1000", "-l", "100"],
    "DEADLINE": ["sudo", "./deadline_test", "-t", "2", "-i", "2000", "-p", "50", "-P", "100"],
}

# Perf events to capture
PERF_EVENTS = "task-clock,cycles,instructions,context-switches,cpu-migrations"

def run_benchmark(label, cmd):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = OUTDIR / f"{label}_{timestamp}.log"

    PERF = "/users/avirmani/bin/perf"
    perf_cmd = ["sudo", PERF, "stat", "-e", PERF_EVENTS, "-a", "--"] + cmd


    print(f"\n=== Running {label} ===")
    print(" ".join(perf_cmd))

    with open(logfile, "w") as f:
        subprocess.run(perf_cmd, stdout=f, stderr=f, text=True)

    print(f"Saved log to {logfile}")
    return logfile

def parse_logs(label, logfile, num_cpus=4):
    metrics = {
        "Scheduler": label,
        "Latency_us": None,
        "Throughput_ops_sec": None,
        "CPUUtil_percent": None,
        "ContextSwitches": None,
        "CpuMigrations": None,
        "MissedDeadlines": None,
        "Bandwidth_percent": None,
    }

    with open(logfile, "r") as f:
        content = f.read()

    # --- Perf metrics ---
    task_clock = None
    elapsed_time = None
    for line in content.splitlines():
        if "task-clock" in line:
            task_clock = float(line.strip().split()[0].replace(",", ""))
        elif "context-switches" in line:
            metrics["ContextSwitches"] = int(line.strip().split()[0].replace(",", ""))
        elif "cpu-migrations" in line:
            metrics["CpuMigrations"] = int(line.strip().split()[0].replace(",", ""))
        elif "seconds time elapsed" in line:
            elapsed_time = float(line.strip().split()[0].replace(",", ""))

    # CPU utilization
    if task_clock and elapsed_time and num_cpus > 0:
        metrics["CPUUtil_percent"] = (task_clock / (elapsed_time * 1000 * num_cpus)) * 100

    # --- Scheduler-specific ---
    if label == "CFS":
        m = re.search(r"Time:\s+([0-9.]+)", content)
        if m:
            total_time = float(m.group(1))
            messages = 2 * 20 * 100  # groups=2, 20 pairs/group, loops=100
            throughput = messages / total_time
            metrics["Latency_us"] = (total_time / messages) * 1e6
            metrics["Throughput_ops_sec"] = throughput

    elif label == "RT-FIFO":
        m = re.search(r"Min:\s+(\d+).*Avg:\s+(\d+).*Max:\s+(\d+)", content)
        if m:
            metrics["Latency_us"] = float(m.group(2))  # avg latency
        # Compute throughput from loops/elapsed
        if elapsed_time:
            loops = 100 * 2  # -l 100, -t 2 threads
            metrics["Throughput_ops_sec"] = loops / elapsed_time

    elif label == "DEADLINE":
        # Latency = configured deadline (-i arg)
        m_deadline = re.search(r"-i\s+(\d+)", " ".join(WORKLOADS["DEADLINE"]))
        if m_deadline:
            metrics["Latency_us"] = float(m_deadline.group(1))

        # Bandwidth = -p arg if present
        m_bw = re.search(r"-p\s+(\d+)", " ".join(WORKLOADS["DEADLINE"]))
        if m_bw:
            metrics["Bandwidth_percent"] = int(m_bw.group(1))

        # Throughput = tasks / (period in sec)
        m_tasks = re.search(r"-t\s+(\d+)", " ".join(WORKLOADS["DEADLINE"]))
        if m_tasks and m_deadline:
            tasks = int(m_tasks.group(1))
            period_sec = float(m_deadline.group(1)) / 1e6
            metrics["Throughput_ops_sec"] = tasks / period_sec

        # Missed deadlines
        missed = len(re.findall(r"missed", content.lower()))
        metrics["MissedDeadlines"] = missed

    return metrics

if __name__ == "__main__":
    summary = []

    for label, cmd in WORKLOADS.items():
        logfile = run_benchmark(label, cmd)
        metrics = parse_logs(label, logfile)
        summary.append(metrics)

    df = pd.DataFrame(summary)
    csvfile = OUTDIR / "summary.csv"
    df.to_csv(csvfile, index=False)
    print(f"\n=== Summary saved to {csvfile} ===")
    print(df)


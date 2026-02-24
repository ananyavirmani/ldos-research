import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

OUTDIR = Path.home() / "scheduler_bench_results"
csvfile = OUTDIR / "summary1.csv"

df = pd.read_csv(csvfile)


# 1. Latency per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['Latency_us'], color='skyblue')
plt.ylabel("Latency (us)")
plt.title("Latency per Scheduler - First Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "latency_first.png", dpi=300)
plt.show()

# 2. Throughput per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['Throughput_ops_sec'], color='lightgreen')
plt.ylabel("Throughput (ops/sec)")
plt.title("Throughput per Scheduler - First Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "throughput_first.png", dpi=300)
plt.show()

# 3. CPU Utilization per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['CPUUtil_percent'], color='salmon')
plt.ylabel("CPU Utilization (%)")
plt.title("CPU Utilization per Scheduler - First Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "cpuutil_first.png", dpi=300)
plt.show()

# 4. Context Switches / CPU Migrations per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['ContextSwitches'], color='orange')
plt.ylabel("Context Switches")
plt.title("Context Switches per Scheduler - First Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "context_switches_first.png", dpi=300)
plt.show()

csvfile = OUTDIR / "summary2.csv"

df = pd.read_csv(csvfile)

# 1. Latency per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['Latency_us'], color='skyblue')
plt.ylabel("Latency (us)")
plt.title("Latency per Scheduler - Second Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "latency_second.png", dpi=300)
plt.show()

# 2. Throughput per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['Throughput_ops_sec'], color='lightgreen')
plt.ylabel("Throughput (ops/sec)")
plt.title("Throughput per Scheduler - Second Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "throughput_second.png", dpi=300)
plt.show()

# 3. CPU Utilization per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['CPUUtil_percent'], color='salmon')
plt.ylabel("CPU Utilization (%)")
plt.title("CPU Utilization per Scheduler - Second Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "cpuutil_second.png", dpi=300)
plt.show()

# 4. Context Switches / CPU Migrations per Scheduler
plt.figure(figsize=(8,5))
plt.bar(df['Scheduler'], df['ContextSwitches'], color='orange')
plt.ylabel("Context Switches")
plt.title("Context Switches per Scheduler - Second Workload")
plt.grid(axis='y')
plt.savefig(OUTDIR / "context_switches_second.png", dpi=300)
plt.show()

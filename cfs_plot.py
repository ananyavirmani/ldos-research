import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv("scheduler_results.csv")

# Keep only CPU-bound workloads
cpu_df = df[df["Workload"] == "cpu_bound"].copy()

# Compute fairness (imbalance metric) = max-min / avg cycles
cpu_cols = ["cpu0_cycles", "cpu1_cycles", "cpu2_cycles", "cpu3_cycles"]
cpu_df["fairness"] = cpu_df[cpu_cols].max(axis=1) - cpu_df[cpu_cols].min(axis=1)
cpu_df["fairness"] /= cpu_df[cpu_cols].mean(axis=1)

# --- Plot 1: Latency vs Throughput for each tunable ---
plt.figure(figsize=(10,6))
for tunable in cpu_df["Tunable"].unique():
    subset = cpu_df[cpu_df["Tunable"] == tunable]
    plt.scatter(subset["Throughput_ops_sec"], subset["Latency_avg_us"], label=tunable, s=80)

plt.xlabel("Throughput (ops/sec)")
plt.ylabel("Average Latency (us)")
plt.title("Latency vs Throughput (CPU-bound)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("latency_vs_throughput.png")
plt.close()

# --- Plot 2: Fairness (imbalance) across tunables ---
plt.figure(figsize=(10,6))
for tunable in cpu_df["Tunable"].unique():
    subset = cpu_df[cpu_df["Tunable"] == tunable]
    plt.plot(subset["Setting"], subset["fairness"], marker="o", label=tunable)

plt.xlabel("Tunable Setting")
plt.ylabel("Fairness (imbalance ratio)")
plt.title("CPU Fairness Across Tunables")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("fairness.png")
plt.close()

# --- Plot 3: Throughput across tunables ---
plt.figure(figsize=(10,6))
for tunable in cpu_df["Tunable"].unique():
    subset = cpu_df[cpu_df["Tunable"] == tunable]
    plt.bar(subset["Setting"] + " (" + tunable + ")", subset["Throughput_ops_sec"])

plt.xticks(rotation=45, ha="right")
plt.ylabel("Throughput (ops/sec)")
plt.title("Throughput by Tunable (CPU-bound)")
plt.tight_layout()
plt.savefig("throughput.png")
plt.close()

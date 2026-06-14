import pandas as pd

# -------------------------
# Load data
# -------------------------

cfs = pd.read_csv("cfs.csv")
top3 = pd.read_csv("top3_random.csv")

# -------------------------
# Merge matching runs
# -------------------------

merged = pd.merge(
    cfs,
    top3,
    on=["workload", "workers", "run"],
    suffixes=("_cfs", "_top3")
)

# -------------------------
# Metrics to compare
# -------------------------

metrics = [
    "throughput",
    "context_switches",
    "cpu_migrations",
    "cycles",
    "instructions",
    "ipc",
    "iops"
]

# -------------------------
# Compute percent changes
# -------------------------

result = merged[
    ["workload", "workers", "run"]
].copy()

for m in metrics:

    result[f"{m}_cfs"] = merged[f"{m}_cfs"]
    result[f"{m}_top3"] = merged[f"{m}_top3"]

    result[f"{m}_pct_change"] = (
        (merged[f"{m}_top3"] - merged[f"{m}_cfs"])
        / merged[f"{m}_cfs"]
    ) * 100

# -------------------------
# Save
# -------------------------

result.to_csv("scheduler_comparison.csv", index=False)

print("Saved scheduler_comparison.csv")
print("Rows:", len(result))

summary = result.groupby(
    ["workload", "workers"]
).mean(numeric_only=True)

summary.reset_index(inplace=True)

summary.to_csv(
    "scheduler_comparison_summary.csv",
    index=False
)

print("Saved scheduler_comparison_summary.csv")
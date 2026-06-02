#!/usr/bin/env python3

import pandas as pd

df = pd.read_csv("summary_results.csv")

baseline = df[df["mode"] == 0]

merged = df.merge(
    baseline,
    on=["workload", "workers"],
    suffixes=("", "_baseline")
)

metrics = [
    "context_switches_mean",
    "cpu_migrations_mean",
    "ipc_mean",
    "elapsed_time_mean"
]

for metric in metrics:

    merged[f"{metric}_pct_change"] = (
        (merged[metric] - merged[f"{metric}_baseline"])
        / merged[f"{metric}_baseline"]
    ) * 100

merged.to_csv("relative_changes.csv", index=False)

print(merged.head())

print("\nWrote relative_changes.csv")
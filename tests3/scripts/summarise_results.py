#!/usr/bin/env python3

import pandas as pd

df = pd.read_csv("all_results.csv")

metrics = [
    "task_clock",
    "context_switches",
    "cpu_migrations",
    "cycles",
    "instructions",
    "ipc",
    "elapsed_time"
]

summary = (
    df
    .groupby(["workload", "mode", "workers"])[metrics]
    .agg(["mean", "std"])
)

summary.columns = [
    f"{col}_{stat}"
    for col, stat in summary.columns
]

summary = summary.reset_index()

summary.to_csv("summary_results.csv", index=False)

print(summary.head())

print("\nWrote summary_results.csv")
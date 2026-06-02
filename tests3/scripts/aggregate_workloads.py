#!/usr/bin/env python3

import pandas as pd

df = pd.read_csv("relative_changes.csv")

metrics = [
    "cpu_migrations_mean_pct_change",
    "context_switches_mean_pct_change",
    "ipc_mean_pct_change",
    "elapsed_time_mean_pct_change"
]

agg = (
    df
    .groupby(["mode", "workers"])[metrics]
    .agg(["mean", "std"])
)

agg.columns = [
    f"{metric}_{stat}"
    for metric, stat in agg.columns
]

agg = agg.reset_index()

agg.to_csv("aggregate_workload_results.csv", index=False)

print(agg.head())

print("\nWrote aggregate_workload_results.csv")
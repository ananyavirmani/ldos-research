import pandas as pd
import matplotlib.pyplot as plt

# Load comparison CSV
df = pd.read_csv("scheduler_comparison_summary.csv")

# ----------------------------------
# Application-level metric graph
# ----------------------------------

def get_app_metric(row):
    if row["workload"] == "cpu":
        return row["ipc_pct_change"]

    elif row["workload"] == "io":
        return row["iops_pct_change"]

    else:  # spawn, mixed
        return row["throughput_pct_change"]


df["app_metric_change"] = df.apply(get_app_metric, axis=1)

for workload in sorted(df["workload"].unique()):

    subset = df[df["workload"] == workload]

    plt.figure(figsize=(7,5))

    plt.plot(
        subset["workers"],
        subset["app_metric_change"],
        marker="o"
    )

    plt.axhline(0, linestyle="--")

    plt.title(f"{workload.upper()}: Application Metric Change")
    plt.xlabel("Workers")
    plt.ylabel("Application Metric Change (%)")

    plt.grid(True)

    plt.savefig(
        f"{workload}_app_metric_change.png",
        bbox_inches="tight"
    )

    plt.close()


# ----------------------------------
# Migration graph
# ----------------------------------

for workload in sorted(df["workload"].unique()):

    subset = df[df["workload"] == workload]

    plt.figure(figsize=(7,5))

    plt.plot(
        subset["workers"],
        subset["cpu_migrations_pct_change"],
        marker="o"
    )

    plt.axhline(0, linestyle="--")

    plt.title(f"{workload.upper()}: CPU Migration Change")
    plt.xlabel("Workers")
    plt.ylabel("Migration Change (%)")

    plt.grid(True)

    plt.savefig(
        f"{workload}_migration_change.png",
        bbox_inches="tight"
    )

    plt.close()

print("Done.")
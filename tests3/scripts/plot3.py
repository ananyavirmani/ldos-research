import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 16,
    "axes.titlesize": 20,
    "axes.labelsize": 18,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 16,
    "legend.title_fontsize": 17,
})

df = pd.read_csv("scheduler_comparison_summary.csv")

# -----------------------------
# Select application metric
# -----------------------------
def get_app_metric(row):
    if row["workload"] == "cpu":
        return row["ipc_pct_change"]

    elif row["workload"] == "spawn":
        return row["throughput_pct_change"]

    elif row["workload"] == "io":
        return row["iops_pct_change"]

    elif row["workload"] == "mixed":
        return row["throughput_pct_change"]

    return None

df["app_change"] = df.apply(get_app_metric, axis=1)

# -----------------------------
# GRAPH 1
# Workers vs App Metric Change
# -----------------------------
plt.figure(figsize=(8,5))

for workload in ["cpu","spawn","io","mixed"]:
    subset = df[df["workload"] == workload]

    plt.plot(
        subset["workers"],
        subset["app_change"],
        marker="o",
        label=workload.upper()
    )

plt.axhline(0, linestyle="--")
plt.xlabel("Workers")
plt.ylabel("Application Metric Change (%)")
plt.title("Application-Level Performance Change vs Oversubscription")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig("graph_workers_vs_app_change.png", dpi=300)
plt.close()

# -----------------------------
# GRAPH 2
# Migration Change vs App Change
# -----------------------------
plt.figure(figsize=(9,6))

cpu_colors = {
    40:"#9ecae1",
    80:"#6baed6",
    160:"#3182bd",
    320:"#08519c"
}

spawn_colors = {
    40:"#fdd0a2",
    80:"#fdae6b",
    160:"#fd8d3c",
    320:"#d94801"
}

io_colors = {
    40:"#a1d99b",
    80:"#74c476",
    160:"#31a354",
    320:"#006d2c"
}

mixed_colors = {
    40:"#dadaeb",
    80:"#bcbddc",
    160:"#9e9ac8",
    320:"#6a51a3"
}

for workload in ["cpu", "spawn", "io", "mixed"]:

    subset = df[df["workload"] == workload]

    for _, row in subset.iterrows():

        plt.scatter(
            row["cpu_migrations_pct_change"],
            row["app_change"],
            color=eval(f"{workload}_colors")[row["workers"]],
            s=225
        )

# create workload legend
for workload, color in {
    "cpu": "#3182bd",
    "spawn": "#fd8d3c",
    "io": "#31a354",
    "mixed": "#9e9ac8"
}.items():

    plt.scatter([], [], color=color, s=225,
                label=workload.upper())

plt.axhline(0, linestyle="--")
plt.axvline(0, linestyle="--")

plt.xlabel("CPU Migration Change Relative to CFS (%)")
plt.ylabel("Application Metric Change Relative to CFS (%)")

# plt.title("Application Performance vs Migration Change")

plt.legend(title="Workload")
plt.grid(True)

plt.tight_layout()
plt.savefig("graph_migrations_vs_app_change.png", dpi=300)
plt.close()
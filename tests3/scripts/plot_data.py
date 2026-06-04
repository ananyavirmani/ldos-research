import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set a clean academic plotting style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16
})

# Load your summary sheet
csv_path = os.path.expanduser('~/scheduler_comparison_summary.csv')
if not os.path.exists(csv_path):
    print("Error: Could not locate scheduler_comparison_summary.csv in your home folder.")
    exit(1)

df = pd.read_csv(csv_path)

# Melt the dataframe from wide to long format for easier Seaborn plotting
delta_cols = [
    'Perf_Score_Delta_%', 
    'Migrations_Delta_%', 
    'Switches_Delta_%', 
    'Cache_Misses_Delta_%'
]

df_long = pd.melt(
    df, 
    id_vars=['Workload', 'Cores'], 
    value_vars=delta_cols,
    var_name='Metric', 
    value_name='Delta_Percentage'
)

# Clean up the metric names for professional chart labels
metric_labels = {
    'Perf_Score_Delta_%': 'Performance Throughput Delta (%)',
    'Migrations_Delta_%': 'CPU Migrations Delta (%)',
    'Switches_Delta_%': 'Context Switches Delta (%)',
    'Cache_Misses_Delta_%': 'Cache Misses Delta (%)'
}
df_long['Metric'] = df_long['Metric'].map(metric_labels)

# Initialize a 2x2 grid of subplots (one for each metric)
fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
axes = axes.flatten()  # Flatten the 2D array into 1D for easy looping

unique_metrics = list(metric_labels.values())
workload_palette = {'cpu': '#1f77b4', 'spawn': '#ff7f0e', 'io': '#2ca02c', 'mixed': '#d62728'}

for i, metric in enumerate(unique_metrics):
    ax = axes[i]
    metric_data = df_long[df_long['Metric'] == metric]
    
    # Plot tracking lines for each workload profile
    sns.lineplot(
        data=metric_data,
        x='Cores',
        y='Delta_Percentage',
        hue='Workload',
        marker='o',
        markersize=8,
        linewidth=2.5,
        palette=workload_palette,
        ax=ax
    )
    
    # Draw a bold horizontal line at y=0 representing baseline CFS
    ax.axhline(0, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # Label tweaks
    ax.set_title(metric, fontweight='bold', pad=10)
    ax.set_ylabel('Delta Relative to CFS (%)')
    ax.set_xlabel('Worker Core Scale')
    
    # Ensure all core scales are explicitly ticked on the X-axis
    ax.set_xticks([40, 80, 160, 320])
    
    # Clean up individual legends to avoid duplication; we will build one master legend
    ax.get_legend().remove()

# Extract the legend handles from the first plot to build a unified top legend
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles, 
    [l.upper() for l in labels], 
    loc='upper center', 
    bbox_to_anchor=(0.5, 0.96),
    ncol=4, 
    fontsize=12, 
    frameon=True
)

# Add overarching title and adjust padding layout
plt.suptitle('Top-3 Randomization Scheduler vs. Default CFS Baseline\nEvaluation Matrix Across Hardware Scaling Bound Fields', y=1.02, fontweight='bold')
plt.tight_layout()

# Save image asset
output_img = os.path.expanduser('~/scheduler_deltas_matrix.png')
plt.savefig(output_img, dpi=300, bbox_inches='tight')
print(f"Success! Comparative matrix plot saved to: {output_img}")
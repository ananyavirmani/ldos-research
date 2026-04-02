import pandas as pd
import matplotlib.pyplot as plt
import re

def parse_research_data(latency_file, accuracy_file, label):
    with open(latency_file, 'r') as f:
        lat_content = f.read()
    with open(accuracy_file, 'r') as f:
        acc_content = f.read()
    
    data = {"Scheduler": label}
    
    # 1. Parse Latencies (Standardize naming)
    lat_matches = re.findall(r"\[(.*?)\]: (\d+)", lat_content)
    for key, val in lat_matches:
        if "Placement" in key: data["Placement_Lat"] = int(val)
        if "Accounting" in key or "Tick" in key: data["Accounting_Lat"] = int(val)
    
    # 2. Parse Hackbench Time
    times = re.findall(r"Time: (\d+\.\d+)", lat_content)
    if times: data["Workload_Time"] = sum(float(t) for t in times) / len(times)

    # 3. Parse Placement Accuracy (The "Decision" check)
    acc_matches = re.findall(r"\[(.*?)\]: (\d+)", acc_content)
    for key, val in acc_matches:
        if "Perfect Locality" in key: data["Perfect_Locality"] = int(val)
        if "Soft Migration" in key: data["Soft_Migration"] = int(val)
        if "Hard Migration" in key: data["Hard_Migration"] = int(val)
        
    return data

# Aggregate Data
results = [
    parse_research_data("cfs_latency.txt", "cfs_accuracy.txt", "CFS"),
    parse_research_data("scx_latency.txt", "scx_accuracy.txt", "SCX")
]

df = pd.DataFrame(results).set_index("Scheduler")
df.to_csv("final_results.csv")

# --- VISUAL ANALYSIS ---
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Plot 1: Logic Latency (Efficiency)
df[['Placement_Lat', 'Accounting_Lat']].plot(kind='bar', ax=axes[0], color=['#3498db', '#e74c3c'], edgecolor='black')
axes[0].set_title("Logic Latency (Lower is Better)")
axes[0].set_ylabel("Nanoseconds")

# Plot 2: Placement Accuracy (The 'Why')
# Using Log Scale because the differences are massive
df[['Perfect_Locality', 'Soft_Migration', 'Hard_Migration']].plot(kind='bar', ax=axes[1], logy=True, edgecolor='black')
axes[1].set_title("Placement Accuracy (Log Scale)")
axes[1].set_ylabel("Event Count")

# Plot 3: Throughput (The Bottom Line)
df['Workload_Time'].plot(kind='bar', ax=axes[2], color=['#2ecc71', '#f1c40f'], edgecolor='black')
axes[2].set_title("Total Workload Time (Lower is Better)")
axes[2].set_ylabel("Seconds")

plt.tight_layout()
plt.savefig("final_research_analysis.png")
print("\n--- ANALYSIS COMPLETE ---")
print(df)

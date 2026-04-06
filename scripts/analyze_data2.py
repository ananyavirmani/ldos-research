import pandas as pd
import matplotlib.pyplot as plt
import re

def parse_research_data(latency_file, accuracy_file, label):
    # This assumes the files exist in your directory
    with open(latency_file, 'r') as f:
        lat_content = f.read()
    with open(accuracy_file, 'r') as f:
        acc_content = f.read()
    
    data = {"Scheduler": label}
    
    # 1. Parse Latencies
    lat_matches = re.findall(r"\[(.*?)\]: (\d+)", lat_content)
    for key, val in lat_matches:
        if "Placement" in key: data["Placement_Lat"] = int(val)
        if "Accounting" in key or "Tick" in key: data["Accounting_Lat"] = int(val)
    
    # 2. Parse Hackbench Time
    times = re.findall(r"Time: (\d+\.\d+)", lat_content)
    if times: data["Workload_Time"] = sum(float(t) for t in times) / len(times)

    # 3. Parse Placement Accuracy
    acc_matches = re.findall(r"\[(.*?)\]: (\d+)", acc_content)
    for key, val in acc_matches:
        if "Perfect Locality" in key: data["Perfect_Locality"] = int(val)
        if "Soft Migration" in key: data["Soft_Migration"] = int(val)
        if "Hard Migration" in key: data["Hard_Migration"] = int(val)
        
    return data

# Aggregate Data
# Note: Ensure these files are present or the parse will fail
results = [
    parse_research_data("cfs_latency.txt", "cfs_accuracy.txt", "CFS"),
    parse_research_data("scx_latency.txt", "scx_accuracy.txt", "SCX")
]

df = pd.DataFrame(results).set_index("Scheduler")
df.to_csv("final_results.csv")

# --- SEPARATE VISUAL ANALYSIS ---

# Plot 1: Logic Latency (Efficiency)
plt.figure(figsize=(6, 6))
ax1 = df[['Placement_Lat', 'Accounting_Lat']].plot(kind='bar', color=['#3498db', '#e74c3c'], edgecolor='black')
plt.ylabel("Nanoseconds", fontsize=12)
plt.xlabel("Scheduler", fontsize=12)
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("logic_latency_clean.png")
plt.close()

# Plot 2: Placement Accuracy (The 'Why')
plt.figure(figsize=(6, 6))
# Using Log Scale because the differences are massive
ax2 = df[['Perfect_Locality', 'Soft_Migration', 'Hard_Migration']].plot(kind='bar', logy=True, edgecolor='black')
plt.ylabel("Event Count (Log Scale)", fontsize=12)
plt.xlabel("Scheduler", fontsize=12)
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("placement_accuracy_clean.png")
plt.close()


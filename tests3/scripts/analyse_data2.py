import os
import re
import glob
import pandas as pd

HOME = os.path.expanduser("~")

# Maps folder indicators directly to clean workload labels
WORKLOAD_MAP = {
    "sched_results1": "cpu",
    "sched_results2": "spawn",
    "sched_results4": "io",
    "sched_results5": "mixed"
}

def parse_perf_stat(file_path):
    metrics = {"migrations": 0, "switches": 0, "cache_misses": 0}
    if not os.path.exists(file_path):
        return metrics
    
    with open(file_path, 'r', errors='ignore') as f:
        content = f.read()
        mig_match = re.search(r'([\d,]+)\s+cpu-migrations', content)
        sw_match = re.search(r'([\d,]+)\s+context-switches', content)
        cache_match = re.search(r'([\d,]+)\s+cache-misses', content)
        
        if mig_match: metrics["migrations"] = float(mig_match.group(1).replace(',', ''))
        if sw_match: metrics["switches"] = float(sw_match.group(1).replace(',', ''))
        if cache_match: metrics["cache_misses"] = float(cache_match.group(1).replace(',', ''))
    return metrics

def parse_stress_output(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', errors='ignore') as f:
        content = f.read()
        
        ops_match = re.search(r'([\d\.]+)\s+bogo ops/s', content)
        if ops_match:
            return float(ops_match.group(1))
        time_match = re.search(r'Time:\s+([\d\.]+)', content)
        if time_match:
            return float(time_match.group(1))
            
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        for line in reversed(lines):
            nums = re.findall(r'\d+\.\d+', line)
            if nums:
                return float(nums[-1])
    return None

def find_workload_from_path(path_parts):
    """Robust lookup that finds sched_resultsX anywhere in the path string"""
    for part in path_parts:
        if "sched_results" in part:
            return WORKLOAD_MAP.get(part)
    return None

def extract_via_wildcards():
    raw_rows = []
    
    # 1. SCAN CUSTOM KERNEL RUNS
    custom_pattern = os.path.join(HOME, "sched_results*", "*", "cpu*", "run*", "stress_output.txt")
    custom_files = glob.glob(custom_pattern)
    print(f"Found {len(custom_files)} custom scheduler execution files via scan...")
    
    for stress_path in custom_files:
        path_parts = stress_path.split(os.sep)
        
        workload = find_workload_from_path(path_parts)
        if not workload: continue
        
        # Pull core and run strings reliably by looking at exact folder syntax patterns
        core_str = [p for p in path_parts if p.startswith("cpu")][0]
        run_str = [p for p in path_parts if p.startswith("run")][0]
        
        cores = int(re.sub(r'\D', '', core_str))
        run_num = int(re.sub(r'\D', '', run_str))
        
        perf_path = os.path.join(os.path.dirname(stress_path), "perf_stat.txt")
        s_score = parse_stress_output(stress_path)
        p_metrics = parse_perf_stat(perf_path)
        
        if s_score is not None:
            raw_rows.append({
                "Kernel": "Top3Random", "Workload": workload, "Cores": cores, "Iteration": run_num,
                "Performance_Score": s_score, "CPU_Migrations": p_metrics["migrations"],
                "Context_Switches": p_metrics["switches"], "Cache_Misses": p_metrics["cache_misses"]
            })

    # 2. SCAN BASELINE CFS RUNS
    base_pattern = os.path.join(HOME, "ldos-research", "tests3", "data", "sched_results*", "0", "cpu*", "run*", "stress_output.txt")
    base_files = glob.glob(base_pattern)
    print(f"Found {len(base_files)} baseline CFS scheduler execution files via scan...")
    
    for stress_path in base_files:
        path_parts = stress_path.split(os.sep)
        
        workload = find_workload_from_path(path_parts)
        if not workload: continue
        
        core_str = [p for p in path_parts if p.startswith("cpu")][0]
        run_str = [p for p in path_parts if p.startswith("run")][0]
        
        cores = int(re.sub(r'\D', '', core_str))
        run_num = int(re.sub(r'\D', '', run_str))
        
        perf_path = os.path.join(os.path.dirname(stress_path), "perf_stat.txt")
        s_score = parse_stress_output(stress_path)
        p_metrics = parse_perf_stat(perf_path)
        
        if s_score is not None:
            raw_rows.append({
                "Kernel": "CFS", "Workload": workload, "Cores": cores, "Iteration": run_num,
                "Performance_Score": s_score, "CPU_Migrations": p_metrics["migrations"],
                "Context_Switches": p_metrics["switches"], "Cache_Misses": p_metrics["cache_misses"]
            })
            
    return pd.DataFrame(raw_rows)

df_raw = extract_via_wildcards()

if df_raw.empty:
    print("\n[ERROR]: Extracted dataset is blank.")
    exit(1)

print(f"\nSuccessfully populated {len(df_raw)} total rows into unified dataframe! Processing exports...")

# Export Granular Individual Workload Sheets
for workload in WORKLOAD_MAP.values():
    workload_data = df_raw[df_raw["Workload"] == workload]
    if not workload_data.empty:
        csv_path = os.path.join(HOME, f"raw_data_{workload}.csv")
        workload_data.to_csv(csv_path, index=False)

# Export Paired Comparative Metrics Summary
df_avg = df_raw.groupby(["Kernel", "Workload", "Cores"]).mean().reset_index().drop(columns=["Iteration"])
cfs_set = df_avg[df_avg["Kernel"] == "CFS"].drop(columns=["Kernel"])
top3_set = df_avg[df_avg["Kernel"] == "Top3Random"].drop(columns=["Kernel"])

if cfs_set.empty or top3_set.empty:
    print("\n[ERROR]: Alignment failure. One of the sets has failed to match workloads or core markers.")
    print(f"CFS Data Matrix Count: {len(cfs_set)} rows | Top3Random Data Matrix Count: {len(top3_set)} rows")
    exit(1)

summary_df = pd.merge(cfs_set, top3_set, on=["Workload", "Cores"], suffixes=('_CFS', '_Top3Random'))

summary_df["Perf_Score_Delta_%"] = ((summary_df["Performance_Score_Top3Random"] - summary_df["Performance_Score_CFS"]) / summary_df["Performance_Score_CFS"]) * 100
summary_df["Migrations_Delta_%"] = ((summary_df["CPU_Migrations_Top3Random"] - summary_df["CPU_Migrations_CFS"]) / summary_df["CPU_Migrations_CFS"]) * 100
summary_df["Switches_Delta_%"]   = ((summary_df["Context_Switches_Top3Random"] - summary_df["Context_Switches_CFS"]) / summary_df["Context_Switches_CFS"]) * 100
summary_df["Cache_Misses_Delta_%"] = ((summary_df["Cache_Misses_Top3Random"] - summary_df["Cache_Misses_CFS"]) / summary_df["Cache_Misses_CFS"]) * 100

summary_csv_path = os.path.join(HOME, "scheduler_comparison_summary.csv")
summary_df.sort_values(by=["Workload", "Cores"]).to_csv(summary_csv_path, index=False)

print("\nSuccess! Data arms aligned perfectly:")
print("  -> Summary Delta Metrics Table: ~/scheduler_comparison_summary.csv")
print("  -> Raw Individual Plotting Sheets: ~/raw_data_cpu.csv, ~/raw_data_spawn.csv, etc.")
import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def run_benchmark(label, bpf_script, workload_cmd):
    """
    Runs bpftrace, captures output, and extracts standardized latency values.
    """
    print(f"\n--- Running {label} Benchmark ---")
    
    # We use the absolute path for bpftrace to ensure sudo finds it
    # No internal 'sudo' here; we assume the python script is run with sudo
    cmd = ["bpftrace", bpf_script, "-c", workload_cmd]
    
    try:
        # Run and capture STDOUT/STDERR. Timeout at 90s for heavy hackbench runs.
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        output = result.stdout
        stderr = result.stderr
        
        if result.returncode != 0:
            print(f"Error: bpftrace exited with code {result.returncode}")
            print(f"Stderr: {stderr}")
            return None

        print("Successfully captured output. Parsing results...")
        
        # Regex to find: @latency_ns[Label]: Value OR @scx_lat[Label]: Value
        # This matches the pattern regardless of the map name
        matches = re.findall(r"\[(.*?)\]: (\d+)", output)
        
        data = {"Scheduler": label}
        for metric_key, value in matches:
            # Standardize naming for the DataFrame
            if "Placement" in metric_key:
                data["Placement"] = int(value)
            elif "Accounting" in metric_key or "Tick" in metric_key:
                data["Accounting"] = int(value)
        
        # Capture the 'Time' reported by hackbench if available
        times = re.findall(r"Time: (\d+\.\d+)", output)
        if times:
            # Average the reported hackbench times for this run
            data["Workload_Time"] = sum(float(t) for t in times) / len(times)
            
        return data
    except subprocess.TimeoutExpired:
        print(f"Error: {label} benchmark timed out.")
        return None
    except Exception as e:
        print(f"Unexpected error running {label}: {e}")
        return None

def generate_plots(df):
    """
    Generates research-grade plots from the collected DataFrame.
    """
    # Ensure we have data to plot
    if df.empty:
        print("DataFrame is empty. Skipping plots.")
        return

    df.set_index('Scheduler', inplace=True)
    
    # Plot 1: Logic Latency (Placement vs Accounting)
    # We use 'Placement' and 'Accounting' as they were standardized in run_benchmark
    cols_to_plot = [c for c in ['Placement', 'Accounting'] if c in df.columns]
    
    if cols_to_plot:
        ax = df[cols_to_plot].plot(kind='bar', figsize=(10, 6), color=['#3498db', '#e74c3c'], edgecolor='black')
        plt.title("Scheduler Logic Latency: CFS vs. SCX")
        plt.ylabel("Average Latency (ns)")
        plt.xlabel("Scheduler Type")
        plt.xticks(rotation=0)
        plt.legend(title="Metric")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig("latency_results.png")
        print("Saved: latency_results.png")
    
    # Plot 2: Workload Execution Time
    if "Workload_Time" in df.columns:
        plt.figure(figsize=(8, 6))
        df['Workload_Time'].plot(kind='bar', color=['#2ecc71', '#f1c40f'], edgecolor='black')
        plt.title("Total Workload Execution Time")
        plt.ylabel("Time (seconds)")
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig("workload_time_results.png")
        print("Saved: workload_time_results.png")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Check for root privileges
    if os.geteuid() != 0:
        print("Error: This script must be run with sudo.")
        sys.exit(1)

    results = []
    
    # 1. Setup paths
    workload_path = os.path.abspath("./mixed_workloads.sh")
    os.chmod(workload_path, 0o755) # Ensure it is executable for root

    # 2. Define benchmarks
    # (Label, BPF Script Path)
    benchmarks = [
        ("CFS", "latency_btf5.bt"),
        ("SCX", "latency_scx4.bt")
    ]

    for label, script in benchmarks:
        if os.path.exists(script):
            data = run_benchmark(label, script, workload_path)
            if data:
                results.append(data)
        else:
            print(f"Warning: Script {script} not found. Skipping {label}.")

    # 3. Finalize Data
    if results:
        final_df = pd.DataFrame(results)
        final_df.to_csv("benchmark_data.csv", index=False)
        print("\nFinal Data Summary:")
        print(final_df)
        
        # Generate the visuals
        generate_plots(final_df)
    else:
        print("\nNo data was collected. Please check your .bt files and workload script.")

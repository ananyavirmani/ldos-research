import subprocess
import pandas as pd
import time
import os

# -----------------------------
# Configuration
# -----------------------------
WORKLOADS = ["cpu_bound", "memory_bound"]
DEFAULTS = {
    "base_slice_ns": 3000000,
    "migration_cost_ns": 500000,
    "nr_migrate": 32,
    "tunable_scaling": 1,
}

CPUS = [0, 1, 2, 3]
RUNS_PER_SETTING = 3
STRESS_DURATION = 30  # seconds for stress-ng
CYCLICTEST_INTERVAL_US = 10000
CYCLICTEST_LOOPS = 1000

# -----------------------------
# Helpers
# -----------------------------

def set_tunable(tunable, value):
    # Example: write to /proc/sys/kernel/<tunable>
    print(f"Setting {tunable} = {value}")
    # subprocess.run(["sudo", "sh", "-c", f"echo {value} > /proc/sys/kernel/{tunable}"])

def restore_defaults():
    for tunable, val in DEFAULTS.items():
        set_tunable(tunable, val)

def read_cpu_cycles():
    # Placeholder: use perf or RDTSC if needed
    # For now, return dummy zeros
    return {f"cpu{i}_cycles": 0 for i in CPUS}

# -----------------------------
# Workload runners
# -----------------------------

def run_cyclictest(workload, tunable_label):
    logfile = f"{workload}_{tunable_label}.log"
    cmd = [
        "sudo", "./cyclictest",
        "-t", str(len(CPUS)),
        "-p", "0",  # CFS priority
        "-a", "0-3",
        "-i", str(CYCLICTEST_INTERVAL_US),
        "-l", str(CYCLICTEST_LOOPS),
        "-m",  # mlockall
    ]
    print(f"Running cyclictest: {' '.join(cmd)}")
    with open(logfile, "w") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    return logfile

def parse_cyclictest_log(logfile):
    latency_sum = 0
    count = 0
    cpu_cycles = {f"cpu{i}_cycles": 0 for i in CPUS}
    
    with open(logfile) as f:
        for line in f:
            line = line.strip()
            if line.startswith("T:"):
                # T: 0 (...) ... Avg: 6 ...
                parts = line.split()
                cpu_id = int(parts[1].strip("()"))
                try:
                    avg_idx = parts.index("Avg:") + 1
                    avg_latency = int(parts[avg_idx])
                    latency_sum += avg_latency
                    count += 1
                    cpu_cycles[f"cpu{cpu_id}_cycles"] += avg_latency  # simple proxy
                except ValueError:
                    pass
    avg_latency_us = latency_sum / count if count else 0
    throughput_ops_sec = sum(cpu_cycles.values()) / STRESS_DURATION
    return avg_latency_us, throughput_ops_sec, cpu_cycles

# def run_stressng_vm(workload, tunable_label):
#     logfile = f"{workload}_{tunable_label}.log"
#     cmd = [
#         "stress-ng",
#         "--vm", str(len(CPUS)),
#         "--timeout", f"{STRESS_DURATION}s",
#         "--vm-method", "all",
#     ]
#     print(f"Running stress-ng: {' '.join(cmd)}")
#     with open(logfile, "w") as f:
#         subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
#     # stress-ng doesn't provide latency/throughput directly
#     cpu_before = read_cpu_cycles()
#     time.sleep(0.1)
#     cpu_after = read_cpu_cycles()
#     # cpu_deltas = {cpu: cpu_after[cpu]-cpu_before[cpu] for cpu in CPUS}
#     cpu_deltas = {f"cpu{i}_cycles": cpu_after[f"cpu{i}_cycles"] - cpu_before[f"cpu{i}_cycles"] for i in CPUS}
#     return logfile, cpu_deltas

# def run_stressng_vm(workload_name, label):
#     """
#     Run stress-ng vm stressor (memory-bound workload) with metrics.
#     Returns (logfile, cpu_deltas).
#     """
#     logfile = f"{workload_name}_{label}.log"

#     # capture CPU cycles before workload
#     cpu_before = read_cpu_cycles()

#     # run stress-ng with metrics-brief
#     cmd = [
#         "stress-ng", "--vm", "4", "--timeout", "30s",
#         "--metrics-brief", "--vm-bytes", "512M"  # allocate 512M per stressor
#     ]
#     with open(logfile, "w") as f:
#         subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

#     # capture CPU cycles after workload
#     cpu_after = read_cpu_cycles()
#     cpu_deltas = {cpu: cpu_after[cpu] - cpu_before[cpu] for cpu in CPUS}

#     return logfile, cpu_deltas

def run_stressng_vm(workload_name, label):
    """
    Run stress-ng vm stressor (memory-bound workload) with metrics.
    Returns (logfile, cpu_deltas).
    """
    logfile = f"{workload_name}_{label}.log"

    # capture CPU cycles before workload
    cpu_before = read_cpu_cycles()

    # run stress-ng with metrics-brief
    cmd = [
        "stress-ng", "--vm", "4", "--timeout", "30s",
        "--metrics-brief", "--vm-bytes", "512M"
    ]
    with open(logfile, "w") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

    # capture CPU cycles after workload
    cpu_after = read_cpu_cycles()

    # compute deltas safely
    cpu_deltas = {}
    for cpu in CPUS:
        before_val = cpu_before.get(cpu, 0)
        after_val = cpu_after.get(cpu, 0)
        cpu_deltas[cpu] = max(0, after_val - before_val)

    return logfile, cpu_deltas



# -----------------------------
# Main testing loop
# -----------------------------
all_results = []

for tunable, default_val in DEFAULTS.items():
    print(f"\n##### Testing tunable {tunable} (default={default_val}) #####")
    
    values = {
        "default": default_val,
        "small": max(1, default_val // 2),
        "large": default_val * 2,
    }

    for label, val in values.items():
        restore_defaults()
        set_tunable(tunable, val)
        
        for workload in WORKLOADS:
            print(f"\n[INFO] Workload={workload}, Tunable={tunable}, Setting={label}")

            if workload == "cpu_bound":
                logfile = run_cyclictest(workload, f"{tunable}_{label}")
                avg_latency_us, throughput_ops_sec, cpu_cycles = parse_cyclictest_log(logfile)
            else:
                logfile, cpu_cycles = run_stressng_vm(workload, f"{tunable}_{label}")
                avg_latency_us = 0
                throughput_ops_sec = 0

            metrics = {
                "Workload": workload,
                "Tunable": tunable,
                "Setting": label,
                "Value": val,
                "Latency_avg_us": avg_latency_us,
                "Throughput_ops_sec": throughput_ops_sec,
            }
            metrics.update(cpu_cycles)
            
            all_results.append(metrics)


# -----------------------------
# Write CSV
# -----------------------------
df = pd.DataFrame(all_results)
csv_file = "scheduler_results.csv"
df.to_csv(csv_file, index=False)
print(f"Results saved to {csv_file}")

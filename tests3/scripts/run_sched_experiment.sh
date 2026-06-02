#!/bin/bash
set -e

PERF=~/kernel-research/linux-6.6.42/tools/perf/perf
OUTDIR=~/sched_results5
MODE=$1
WORKERS=$2
RUN=$3
TIMEOUT=${4:-30}
WORKLOAD=$5

case $WORKLOAD in
  cpu)
    CMD="stress-ng --cpu $WORKERS --timeout ${TIMEOUT}s --metrics-brief"
    ;;
  spawn)
    CMD="stress-ng --spawn $WORKERS --timeout ${TIMEOUT}s --metrics-brief"
    ;;
  hackbench)
    CMD="hackbench -g 20 -f 25 -l 10000"
    ;;
  io)
    CMD="stress-ng --hdd 8 --io 8 --timeout ${TIMEOUT}s"
    ;;
  mixed)
    CMD="stress-ng --cpu $((WORKERS/2)) --io 8 --vm 4 --timeout ${TIMEOUT}s"
    ;;
  *)
    echo "Unknown workload"
    exit 1
    ;;
esac

if [ -z "$MODE" ] || [ -z "$WORKERS" ] || [ -z "$RUN" ]; then
  echo "Usage: $0 <mode_name> <workers> <run_number> [timeout_seconds]"
  echo "Example: $0 mode1_prev_cpu 80 1 30"
  exit 1
fi

DIR=$OUTDIR/${MODE}/cpu${WORKERS}/run${RUN}
mkdir -p $DIR

echo "=== Saving metadata ==="
{
  echo "date=$(date)"
  echo "hostname=$(hostname)"
  echo "kernel=$(uname -r)"
  echo "nproc=$(nproc)"
  echo "mode=$MODE"
  echo "workers=$WORKERS"
  echo "run=$RUN"
  echo "timeout=${TIMEOUT}s"
  echo "cmd=stress-ng --cpu $WORKERS --timeout ${TIMEOUT}s --metrics-brief"
  grep -n "SELECT_TASK_RQ_FAIR_EXP_MODE" ~/kernel-research/linux-6.6.42/kernel/sched/fair.c || true
} > $DIR/metadata.txt

echo "=== Running perf stat: hardware + scheduler metrics ==="
sudo $PERF stat \
  -e task-clock,context-switches,cpu-migrations,cycles,instructions,cache-misses,branches,branch-misses  -a -- su - $USER -c "$CMD" \
  > $DIR/stress_output.txt \
  2> $DIR/perf_stat.txt

echo "=== Running perf sched record ==="
# sudo $PERF sched record \
#  -o $DIR/perf_sched.data \
#  -- stress-ng --cpu $WORKERS --timeout ${TIMEOUT}s --metrics-brief \
#  > $DIR/stress_sched_output.txt \
#  2> $DIR/perf_sched_record.txt

# echo "=== Generating perf sched latency report ==="
# sudo $PERF sched latency \
#  -i $DIR/perf_sched.data \
#  > $DIR/perf_sched_latency.txt \
#  2> $DIR/perf_sched_latency.err || true

echo "=== Done ==="
echo "Results saved in: $DIR"

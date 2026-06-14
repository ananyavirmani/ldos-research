#!/bin/bash

set -euo pipefail

WORKERS_LIST=(40 80 160 320)
RUNS=3
DURATION=30

BASE_DIR=~/top3_random

PERF_CMD="sudo ~/kernel-research/linux-6.6.42/tools/perf/perf stat -a -x, -e context-switches,cpu-migrations,cycles,instructions"

mkdir -p $BASE_DIR

# =========================
# AUTO-DETECT ACTIVE DISK
# =========================
get_disk() {
    lsblk -no PKNAME $(df / | tail -1 | awk '{print $1}')
}

DISK="/dev/$(get_disk)"

echo "Detected active disk: $DISK"

# =========================
# PERF PARSER
# =========================
parse_perf () {
    file=$1

    cs=$(grep context-switches "$file" | awk -F',' '{print $1}')
    mig=$(grep cpu-migrations "$file" | awk -F',' '{print $1}')
    cyc=$(grep cycles "$file" | awk -F',' '{print $1}')
    ins=$(grep instructions "$file" | awk -F',' '{print $1}')

    ipc=$(awk -v i="$ins" -v c="$cyc" 'BEGIN { if (c>0) print i/c; else print 0 }')

    echo "$cs,$mig,$cyc,$ins,$ipc"
}

# =========================
# FIXED IO PARSER (IOPS)
# =========================
parse_iops () {
    file=$1

    awk -v disk="$DISK" '
    $1 == disk {
        ops += ($2 + $7)   # r/s + w/s
        n++
    }
    END {
        if (n > 0)
            printf "%.3f\n", ops/n;
        else
            print 0
    }' "$file"
}

# =========================
# CPU
# =========================
run_cpu () {
    W=$1
    R=$2
    OUTDIR=$3

    STRESS_OUT="$OUTDIR/stress.txt"
    PERF_OUT="$OUTDIR/perf.txt"

    sudo ~/kernel-research/linux-6.6.42/tools/perf/perf stat -a -x, \
        -e context-switches,cpu-migrations,cycles,instructions \
        stress-ng --cpu $W --timeout ${DURATION}s --metrics-brief \
        > "$STRESS_OUT" 2> "$PERF_OUT"

    read cs mig cyc ins ipc <<< $(parse_perf "$PERF_OUT")

    bogo=$(grep -i "bogo ops" "$STRESS_OUT" | awk '{print $(NF-1)}')

    echo "cpu,$W,$R,$cs,$mig,$cyc,$ins,$ipc,$bogo"
}

# =========================
# SPAWN
# =========================
run_spawn () {
    W=$1
    R=$2
    OUTDIR=$3

    STRESS_OUT="$OUTDIR/stress.txt"
    PERF_OUT="$OUTDIR/perf.txt"

    sudo ~/kernel-research/linux-6.6.42/tools/perf/perf stat -a -x, \
        -e context-switches,cpu-migrations,cycles,instructions \
        -- su - $USER -c "stress-ng --spawn $W --timeout ${DURATION}s --metrics-brief" \
        > "$STRESS_OUT" 2> "$PERF_OUT"

    read cs mig cyc ins ipc <<< $(parse_perf "$PERF_OUT")

    proc=$(grep -i "bogo ops" "$STRESS_OUT" | awk '{print $(NF-1)}')

    echo "spawn,$W,$R,$cs,$mig,$cyc,$ins,$ipc,$proc"
}

# =========================
# IO (FIXED IOPS)
# =========================
run_io () {
    W=$1
    R=$2
    OUTDIR=$3

    STRESS_OUT="$OUTDIR/stress.txt"
    PERF_OUT="$OUTDIR/perf.txt"
    IO_OUT="$OUTDIR/iostat.txt"

    iostat -dx 1 $DURATION > "$IO_OUT" &
    IO_PID=$!

    sudo ~/kernel-research/linux-6.6.42/tools/perf/perf stat -a -x, \
        -e context-switches,cpu-migrations,cycles,instructions \
        -- su - $USER -c "stress-ng --hdd $W --io $W --timeout ${DURATION}s" \
        > "$STRESS_OUT" 2> "$PERF_OUT"

    wait $IO_PID

    read cs mig cyc ins ipc <<< $(parse_perf "$PERF_OUT")
    iops=$(parse_iops "$IO_OUT")

    echo "io,$W,$R,$cs,$mig,$cyc,$ins,$ipc,$iops"
}

# =========================
# MIXED
# =========================
run_mixed () {
    W=$1
    R=$2
    OUTDIR=$3

    STRESS_OUT="$OUTDIR/stress.txt"
    PERF_OUT="$OUTDIR/perf.txt"

    sudo ~/kernel-research/linux-6.6.42/tools/perf/perf stat -a -x, \
        -e context-switches,cpu-migrations,cycles,instructions \
        -- su - $USER -c "stress-ng --cpu $((W/2)) --io 8 --vm 4 --timeout ${DURATION}s" \
        > "$STRESS_OUT" 2> "$PERF_OUT"

    read cs mig cyc ins ipc <<< $(parse_perf "$PERF_OUT")

    mix=$(grep -i "bogo ops" "$STRESS_OUT" | awk '{print $(NF-1)}')

    echo "mixed,$W,$R,$cs,$mig,$cyc,$ins,$ipc,$mix"
}

# =========================
# MAIN OUTPUT
# =========================
echo "workload,workers,run,context_switches,cpu_migrations,cycles,instructions,ipc,app_metric" \
    > $BASE_DIR/all_results.csv

for W in "${WORKERS_LIST[@]}"; do
    for R in $(seq 1 $RUNS); do

        for TYPE in cpu spawn io mixed; do

            OUTDIR="$BASE_DIR/${TYPE}${W}/run${R}"
            mkdir -p "$OUTDIR"

            echo "Running $TYPE W=$W R=$R"

            if [ "$TYPE" == "cpu" ]; then
                line=$(run_cpu $W $R $OUTDIR)
            elif [ "$TYPE" == "spawn" ]; then
                line=$(run_spawn $W $R $OUTDIR)
            elif [ "$TYPE" == "io" ]; then
                line=$(run_io $W $R $OUTDIR)
            else
                line=$(run_mixed $W $R $OUTDIR)
            fi

            echo "$line" >> $BASE_DIR/all_results.csv

        done
    done
done

echo "DONE -> $BASE_DIR/all_results.csv"
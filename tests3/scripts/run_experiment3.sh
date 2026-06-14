#!/bin/bash

WORKERS_LIST=(40 80 160 320)
RUNS=3
DURATION=30

PERF="sudo ~/kernel-research/linux-6.6.42/tools/perf/perf stat -x, -e context-switches,cpu-migrations,cycles,instructions"
IOSTAT_INTERVAL=1

OUTDIR="results_$(date +%F_%H-%M-%S)"
mkdir -p "$OUTDIR"

get_iops() {
    local file=$1
    # sum r/s + w/s averaged over run (simple extraction)
    awk -F, '
    /^[0-9]/ {
        rs+=$4; ws+=$5; n++
    }
    END {
        if (n > 0) print (rs+ws)/n;
        else print 0;
    }' "$file"
}

run_perf_wrapped () {
    local cmd="$1"
    local outfile="$2"

    /usr/bin/time -v bash -c "$PERF -- $cmd" 2> "$outfile.perf" > "$outfile.out"
}

run_iostat_bg () {
    local outfile=$1
    iostat -dx $IOSTAT_INTERVAL > "$outfile.iostat" &
    echo $!
}

for workload in spawn cpu io mixed; do
    echo "Running workload: $workload"

    WORKDIR="$OUTDIR/$workload"
    mkdir -p "$WORKDIR"

    for w in "${WORKERS_LIST[@]}"; do
        for r in $(seq 1 $RUNS); do

            echo "  Workers=$w Run=$r"

            BASE="$WORKDIR/w${w}_r${r}"

            IO_PID=""

            if [[ "$workload" == "io" || "$workload" == "mixed" ]]; then
                IO_PID=$(run_iostat_bg "$BASE")
            fi

            case $workload in
                cpu)
                    CMD="stress-ng --cpu $w --timeout ${DURATION}s --metrics-brief"
                    ;;
                spawn)
                    CMD="sudo -u $USER stress-ng --spawn $w --timeout ${DURATION}s --metrics-brief"
                    ;;
                io)
                    CMD="stress-ng --iomix $w --timeout ${DURATION}s --metrics-brief"
                    ;;
                mixed)
                    CMD="stress-ng --cpu $((w/2)) --iomix $((w/2)) --vm 2 --timeout ${DURATION}s --metrics-brief"
                    ;;
            esac

            run_perf_wrapped "$CMD" "$BASE"

            # stop iostat
            if [[ -n "$IO_PID" ]]; then
                kill $IO_PID 2>/dev/null
            fi

            # extract IOPS if applicable
            if [[ "$workload" == "io" || "$workload" == "mixed" ]]; then
                IOPS=$(get_iops "$BASE.iostat")
            else
                IOPS="NA"
            fi

            # extract stress-ng throughput
            BOGO=$(grep -E "bogo ops" "$BASE.out" | awk '{print $NF}' | tail -1)
            if [[ -z "$BOGO" ]]; then
                BOGO="NA"
            fi

            echo "$workload,$w,$r,$BOGO,$IOPS" >> "$WORKDIR/summary.csv"

        done
    done
done

echo "Done. Results in $OUTDIR"
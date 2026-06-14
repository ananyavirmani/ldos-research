#!/bin/bash

WORKERS_LIST=(40 80 160 320)
RUNS=3
DURATION=30

PERF="$HOME/kernel-research/linux-6.6.42/tools/perf/perf"

OUTDIR="results_$(date +%F_%H-%M-%S)"
mkdir -p "$OUTDIR"

run_perf_wrapped() {
    local cmd="$1"
    local base="$2"

    echo "Running: $cmd"

    sudo $PERF stat -a \
        -x, \
        -e context-switches,cpu-migrations,cycles,instructions \
        -- bash -c "$cmd" \
        > "${base}.out" \
        2> "${base}.perf"

    echo $? > "${base}.exitcode"
}

run_iostat_bg() {
    local base="$1"

    iostat -dx 1 > "${base}.iostat" &
    echo $!
}

for workload in cpu spawn io mixed; do

    echo "======================================="
    echo "Workload: $workload"
    echo "======================================="

    WORKDIR="$OUTDIR/$workload"
    mkdir -p "$WORKDIR"

    for w in "${WORKERS_LIST[@]}"; do

        WDIR="$WORKDIR/w${w}"
        mkdir -p "$WDIR"

        for r in $(seq 1 $RUNS); do

            echo "Workers=$w Run=$r"

            RUNDIR="$WDIR/run${r}"
            mkdir -p "$RUNDIR"

            BASE="$RUNDIR/result"

            IOPID=""

            case "$workload" in

                cpu)
                    CMD="stress-ng --cpu $w --timeout ${DURATION}s --metrics-brief"
                    ;;

                spawn)
                    CMD="sudo -u $USER stress-ng --spawn $w --timeout ${DURATION}s --metrics-brief"
                    ;;

                io)
                    CMD="stress-ng --hdd 8 --io 8 --timeout ${DURATION}s --metrics-brief"

                    IOPID=$(run_iostat_bg "$BASE")
                    ;;

                mixed)
                    CMD="stress-ng \
                        --cpu $((w/2)) \
                        --io 8 \
                        --vm 4 \
                        --timeout ${DURATION}s \
                        --metrics-brief"

                    IOPID=$(run_iostat_bg "$BASE")
                    ;;
            esac

            run_perf_wrapped "$CMD" "$BASE"

            if [[ -n "$IOPID" ]]; then
                kill "$IOPID" 2>/dev/null
                wait "$IOPID" 2>/dev/null
            fi

            if [[ "$(cat "${BASE}.exitcode")" != "0" ]]; then
                echo "FAILED: $workload workers=$w run=$r"
            fi
        done
    done
done

echo
echo "Finished."
echo "Results stored in:"
echo "$OUTDIR"
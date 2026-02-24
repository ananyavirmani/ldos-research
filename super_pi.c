#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    int accuracy = 20; 
    if (argc > 1) accuracy = atoi(argv[1]);
    long long iterations = 20000000LL * accuracy; 

    double a = 1.0, pi = 0.0;
    for (long long i = 0; i < iterations; i++) {
        pi += a / (2 * i + 1);
        a = -a;
    }

    // Read exact scheduler metrics from the kernel before exiting
    FILE *f = fopen("/proc/self/schedstat", "r");
    if (f) {
        unsigned long long exec_ns, wait_ns, slices;
        // schedstat format: exec_runtime wait_runtime run_times
        if (fscanf(f, "%llu %llu %llu", &exec_ns, &wait_ns, &slices) == 3) {
            // Print out execution time, wait latency, and context switches
            printf("%llu,%llu,%llu\n", exec_ns, wait_ns, slices);
        }
        fclose(f);
    }
    return 0;
}

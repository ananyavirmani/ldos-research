#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    long long accuracy = 20; 
    if (argc > 1) accuracy = atoll(argv[1]);

    // Reduced the base multiplier slightly so the accuracy numbers are easier to tune
    long long iterations = 2000000LL * accuracy; 

    double a = 1.0, pi = 0.0;
    for (long long i = 0; i < iterations; i++) {
        pi += a / (2 * i + 1);
        a = -a;
    }

    // Force the compiler to keep the loop by outputting the result to stderr
    fprintf(stderr, "Calculation complete. (PI ~ %.5f)\n", pi * 4);

    // Read exact scheduler metrics from the kernel before exiting
    FILE *f = fopen("/proc/self/schedstat", "r");
    if (f) {
        unsigned long long exec_ns, wait_ns, slices;
        if (fscanf(f, "%llu %llu %llu", &exec_ns, &wait_ns, &slices) == 3) {
            printf("%llu,%llu,%llu\n", exec_ns, wait_ns, slices);
        }
        fclose(f);
    }
    return 0;
}

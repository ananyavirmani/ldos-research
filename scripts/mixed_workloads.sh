#!/bin/bash
# mixed_workload.sh

# Run 4 separate instances of hackbench in the background with different priorities
# Total tasks: 400 * 4 = 1600 (Matching your previous run)

nice -n -20 hackbench -g 10 -l 10000 &   # High Priority (Premium)
nice -n -10 hackbench -g 10 -l 10000 &   # Above Normal
nice -n 10  hackbench -g 10 -l 10000 &   # Below Normal
nice -n 19  hackbench -g 10 -l 10000 &   # Low Priority (Background)

wait # Wait for all instances to finish

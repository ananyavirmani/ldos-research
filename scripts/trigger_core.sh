#!/bin/bash
# 1. Setup two cgroups with unique "Core Cookies"
sudo mkdir -p /sys/fs/cgroup/sec_a
sudo mkdir -p /sys/fs/cgroup/sec_b

# Enable core tagging (the cookie)
echo 1 | sudo tee /sys/fs/cgroup/sec_a/cpu.core_tag
echo 1 | sudo tee /sys/fs/cgroup/sec_b/cpu.core_tag

# 2. Run the workload across these boundaries
# This forces the scheduler to constantly call __sched_core_less 
# to ensure 'sec_a' tasks don't leak data to 'sec_b' tasks on SMT siblings.
sudo cgexec -g cpu:sec_a hackbench -g 20 -l 5000 &
sudo cgexec -g cpu:sec_b hackbench -g 20 -l 5000 &

wait

# 3. Cleanup
sudo rmdir /sys/fs/cgroup/sec_a
sudo rmdir /sys/fs/cgroup/sec_b

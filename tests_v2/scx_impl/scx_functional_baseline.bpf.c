#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <scx/common.bpf.h>

char _license[] SEC("license") = "GPL";

s32 BPF_STRUCT_OPS(simple_select_cpu, struct task_struct *p, 
                   s32 prev_cpu, u32 wake_flags)
{
    s32 cpu;

    /* 1. Try to find any idle CPU in the system */
    cpu = scx_bpf_pick_idle_cpu(p->cpus_ptr, 0);
    if (cpu >= 0)
        return cpu;

    /* 2. If no idle CPU, just fall back to where we were */
    return prev_cpu;
}

void BPF_STRUCT_OPS(simple_enqueue, struct task_struct *p, u64 enq_flags)
{
    /* Use the built-in global dispatch for simplicity */
    scx_bpf_dispatch(p, SCX_DSQ_GLOBAL, SCX_SLICE_DFL, enq_flags);
}

SEC(".struct_ops")
struct sched_ext_ops functional_ops = {
    .select_cpu         = (void *)simple_select_cpu,
    .enqueue            = (void *)simple_enqueue,
    .name               = "scx_functional",
};

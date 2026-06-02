#!/bin/bash
# setup.sh - Environment preparation for Linux 6.12 SCHED_EXT testing
set -e

echo "--- 1. Installing System Dependencies ---"
sudo apt update
sudo apt install -y build-essential libncurses-dev bison flex libssl-dev \
    libelf-dev dwarves zstd bc git wget tar libudev-dev libpci-dev \
    python3 python3-pip python3-numpy python3-matplotlib python3-pandas \
    clang llvm lld pkg-config libbpf-dev linux-tools-common linux-tools-generic meson ninja-build cargo

echo "--- 2. Downloading Linux Kernel 6.12 Source ---"
# We place the kernel source one directory up so it doesn't clutter your git repo
cd ..
mkdir -p kernel-work && cd kernel-work
if [ ! -d "linux-6.12" ]; then
    wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.tar.xz
    tar -xvf linux-6.12.tar.xz
fi
cd linux-6.12

echo "--- 3. Configuring Kernel for SCHED_EXT ---"
cp /boot/config-$(uname -r) .config
make olddefconfig
scripts/config --enable CONFIG_SCHED_CLASS_EXT
scripts/config --enable CONFIG_BPF_SYSCALL
scripts/config --enable CONFIG_DEBUG_INFO_BTF
scripts/config --set-str CONFIG_LOCALVERSION "-sched-ext-612"
scripts/config --disable SYSTEM_TRUSTED_KEYS
scripts/config --disable SYSTEM_REVOCATION_KEYS

echo "--- 4. Downloading and Building SCX Schedulers ---"
cd ../../ldos-research  # Return to your git repo
if [ ! -d "scx" ]; then
    git clone https://github.com/sched-ext/scx.git
    cd scx
    make all
    cd ..
fi

echo "-------------------------------------------------------"
echo "SETUP COMPLETE!"
echo "Kernel Source is located at: ../kernel-work/linux-6.12"
echo "You can now compile it: cd ../kernel-work/linux-6.12 && make -j\$(nproc)"
echo "-------------------------------------------------------"

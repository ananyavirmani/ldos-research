#!/bin/bash
set -e
# Configuration
KERNEL_VERSION="6.6.42"
NUM_CORES=$(nproc)
echo “==== Installing build dependencies ====”
sudo apt update
sudo apt install -y build-essential libncurses-dev bison flex libssl-dev libelf-dev wget pahole dwarves
echo “==== Downloading Linux Kernel $KERNEL_VERSION ====”
cd /usr/src
# git clone https://github.com/YushanQ/linux-6.6.42-annotation.git
sudo wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KERNEL_VERSION}.tar.xz
sudo tar -xf linux-${KERNEL_VERSION}.tar.xz
cd linux-${KERNEL_VERSION}
# cd linux-6.6.42-annotation
cp /boot/config-$(uname -r) .config
export KCONFIG_OVERWRITECONFIG=1
make olddefconfig
scripts/config --disable SYSTEM_TRUSTED_KEYS
scripts/config --disable SYSTEM_REVOCATION_KEYS
scripts/config --disable MODULE_SIG
scripts/config --enable DEBUG_INFO_BTF
make olddefconfig
echo “==== Compiling Kernel ====”
sudo bash -c "make -j${NUM_CORES} 2>&1 | tee build.log"
sudo make modules_install
sudo make install
sudo update-grub

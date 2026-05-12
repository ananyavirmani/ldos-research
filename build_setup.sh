#!/bin/bash

set -e

KDIR=~/kernel-research/linux-6.6.42

echo "=== Building kernel ==="
cd $KDIR
make -j$(nproc)

echo "=== Installing modules ==="
sudo make modules_install

echo "=== Installing kernel ==="
sudo make install

echo "=== Done. Rebooting into new kernel ==="
echo "=== Setting next boot kernel ==="
ENTRY=$(sudo grep -R "menuentry " /boot/grub/grub.cfg | grep "6.6.42" | head -1 | cut -d"'" -f2)

sudo grub-reboot "Advanced options for Ubuntu>$ENTRY"

echo "=== Rebooting ==="
sudo reboot
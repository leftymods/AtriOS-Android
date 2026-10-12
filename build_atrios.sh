#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Sanitize PATH to prevent Buildroot dependency errors due to Windows spaces in WSL
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PROJECT_ROOT/tools/bin"

BUILDROOT_DIR="$PROJECT_ROOT/buildroot"
BOARD_DIR="$PROJECT_ROOT/board/yandex/station2"
OVERLAY_DIR="$BOARD_DIR/rootfs_overlay"
TOOLS_DIR="$PROJECT_ROOT/tools/fw_builder"
MAKE_EXT4FS="$PROJECT_ROOT/tools/bin/make_ext4fs"
[ ! -x "$MAKE_EXT4FS" ] && MAKE_EXT4FS="$(which make_ext4fs 2>/dev/null || true)"

echo "=========================================================="
echo "          AtriOS Linux Master Build System                 "
echo "      Target: Yandex Station Max [Amlogic S905X3]         "
echo "=========================================================="

echo "[1/6] Verifying toolchain and build directories..."
if [ ! -d "$BUILDROOT_DIR" ]; then
    echo "[!] Buildroot source tree not found at $BUILDROOT_DIR"
    echo "[!] Fetching Buildroot 2024.02 LTS..."
    git clone --depth 1 -b 2024.02.x https://github.com/buildroot/buildroot.git "$BUILDROOT_DIR"
fi

# Ensure defconfig is available in Buildroot with dynamic OVERLAY_DIR
if [ -f "$BOARD_DIR/station2_defconfig" ]; then
    mkdir -p "$BUILDROOT_DIR/configs"
    sed "s|BR2_ROOTFS_OVERLAY=.*|BR2_ROOTFS_OVERLAY=\"$OVERLAY_DIR\"|" \
        "$BOARD_DIR/station2_defconfig" > "$BUILDROOT_DIR/configs/yandex_station2_defconfig"
fi

echo "[2/6] Updating kernel modules dependency map (depmod)..."
depmod -b "$OVERLAY_DIR" 4.9.113 2>/dev/null || true

echo "[3/6] Compiling Device Tree with Dual Top Buttons..."
dtc -I dts -O dtb -o "$TOOLS_DIR/overlay/dts/sm1_s905x3_yandex.dtb" "$TOOLS_DIR/overlay/dts/sm1_s905x3_yandex.dts" 2>/dev/null || true
cp "$TOOLS_DIR/overlay/dts/sm1_s905x3_yandex.dtb" "$PROJECT_ROOT/common/arch/arm64/boot/dts/amlogic/sm1_s905x3_yandex.dtb" 2>/dev/null || true

echo "[4/6] Configuring & Building Buildroot rootfs..."
cd "$BUILDROOT_DIR"
if [ ! -f .config ]; then
    echo "Applying AtriOS Station 2 configuration..."
    make yandex_station2_defconfig
fi

make -j$(nproc)

echo "[5/6] Generating ext4 system.PARTITION from Buildroot rootfs..."
ROOTFS_TAR="$BUILDROOT_DIR/output/images/rootfs.tar"
if [ -f "$ROOTFS_TAR" ]; then
    echo "Rootfs archive found: $ROOTFS_TAR"
    mkdir -p "$TOOLS_DIR/overlay/system"
    rm -rf "$TOOLS_DIR/overlay/system"/* 2>/dev/null || true
    tar -xf "$ROOTFS_TAR" -C "$TOOLS_DIR/overlay/system"
    ln -sf sbin/init "$TOOLS_DIR/overlay/system/init"
    chmod 755 "$TOOLS_DIR/overlay/system/lib/ld-"* 2>/dev/null || true
    chmod 755 "$TOOLS_DIR/overlay/system/bin/busybox" 2>/dev/null || true

    echo "root=/dev/mmcblk0p18 rootfstype=ext4 rw rootwait skip_initramfs init=/init selinux=0 enforcing=0 androidboot.selinux=permissive androidboot.hardware=amlogic androidboot.hardware.amlogic_dt_id=g12a_s905x2_rev376f console=ttyS0,115200 androidboot.console=ttyS0 no_console_suspend earlyprintk=aml-uart,0xff803000" > "$TOOLS_DIR/overlay/boot/cmdline.txt"

    mkdir -p "$TOOLS_DIR/staging"
    if [ -x "$MAKE_EXT4FS" ]; then
        echo "Building raw ext4 system.PARTITION (1.44 GB)..."
        "$MAKE_EXT4FS" -l 1551892480 "$TOOLS_DIR/staging/system.PARTITION" "$TOOLS_DIR/overlay/system"
    fi
fi

echo "[6/6] Packaging and signing AtriOS firmware image..."
cd "$TOOLS_DIR"
rm -f .fw_builder_cache.json
python3 fw_builder.py build --version-num 100
echo "=========================================================="
echo "SUCCESS: AtriOS Linux Firmware build complete!"
echo "Image location: $TOOLS_DIR/yandex_s905x3_custom_v100.img"
echo "=========================================================="

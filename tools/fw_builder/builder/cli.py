"""
Command Line Interface (CLI) Framework for fw_builder.py.
Module: builder.cli
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from builder.pristine import (
    DEFAULT_BASE_IMG,
    DEFAULT_CACHE_DIR,
    DEFAULT_VENDOR_CACHE,
    STOCK_21_ITEMS,
    ensure_pristine_base,
    validate_pristine_base,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Exit codes per specification
EXIT_SUCCESS = 0
EXIT_BUILD_FAILURE = 1
EXIT_ARG_ERROR = 2
EXIT_MISSING_TOOL = 3
EXIT_MOUNT_ERROR = 4
EXIT_KEYBOARD_INTERRUPT = 130


# Structured logging utilities
def log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def log_build(msg: str) -> None:
    print(f"[BUILD] {msg}")


def log_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def log_error(msg: str) -> None:
    sys.stderr.write(f"[ERROR] {msg}\n")


def log_success(msg: str) -> None:
    print(f"[SUCCESS] {msg}")


def log_clean(msg: str) -> None:
    print(f"[CLEAN] {msg}")


def log_status(msg: str) -> None:
    print(f"[STATUS] {msg}")


def log_mount(msg: str) -> None:
    print(f"[MOUNT] {msg}")


def log_unmount(msg: str) -> None:
    print(f"[UNMOUNT] {msg}")


def log_watch(msg: str) -> None:
    print(f"[WATCH] {msg}")


def scan_existing_versions(search_dir: Optional[Path | str] = None) -> Tuple[List[int], int]:
    """
    Scan directory for existing versioned custom images:
    yandex_s905x3_custom_v(\\d+).img
    Returns (sorted_version_list, next_version_number).
    """
    target = Path(search_dir or PROJECT_ROOT)
    versions: List[int] = []

    if target.exists() and target.is_dir():
        pattern = re.compile(r"^yandex_s905x3_custom_v(\d+)\.img$")
        for item in target.iterdir():
            if item.is_file():
                match = pattern.match(item.name)
                if match:
                    versions.append(int(match.group(1)))

    versions.sort()
    next_ver = (max(versions) + 1) if versions else 1
    return versions, next_ver


def build_parser() -> argparse.ArgumentParser:
    """Construct argument parser with all required subcommands and flags."""
    parser = argparse.ArgumentParser(
        prog="fw_builder.py",
        description="Automated Firmware Assembly & Watcher Tool for Amlogic S905X3 / Yandex Station Max",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging output")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # 1. build
    p_build = subparsers.add_parser("build", help="Incremental firmware assembly or build from scratch")
    p_build.add_argument(
        "-s", "--from-scratch",
        action="store_true",
        help="Rebuild firmware from zero using stock base yandex_1.99.img",
    )
    p_build.add_argument(
        "-c", "--clean",
        action="store_true",
        help="Clean intermediate compilation artifacts before building",
    )
    p_build.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Simulate assembly steps without writing output images",
    )
    p_build.add_argument("-v", "--verbose", action="store_true", help="Verbose build logging")
    p_build.add_argument(
        "--version-num",
        type=int,
        default=None,
        help="Explicit version number to assign to output image",
    )
    p_build.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to place compiled .img output (defaults to project root)",
    )
    p_build.add_argument(
        "--overlay",
        type=str,
        default=None,
        help="Path to overlay directory (defaults to overlay/ in project root)",
    )

    # 2. watch
    p_watch = subparsers.add_parser("watch", help="Monitor overlay directories and auto-rebuild on changes")
    p_watch.add_argument(
        "-d", "--debounce",
        type=float,
        default=2.0,
        help="Debounce quiet interval in seconds (default: 2.0)",
    )
    p_watch.add_argument(
        "-p", "--poll-interval",
        type=float,
        default=0.5,
        help="Polling loop fallback interval in seconds (default: 0.5)",
    )
    p_watch.add_argument(
        "--initial-build",
        action="store_true",
        help="Trigger an incremental build immediately upon daemon launch",
    )
    p_watch.add_argument("-v", "--verbose", action="store_true", help="Verbose watcher logging")

    # 3. mount
    p_mount = subparsers.add_parser("mount", help="Loop-mount ext4 partition for inspection and editing")
    p_mount.add_argument(
        "partition",
        type=str,
        help="Partition name to mount (e.g. vendor, system, odm, product)",
    )
    p_mount.add_argument(
        "--mount-point",
        type=str,
        default=None,
        help="Target mount directory (defaults to <project_root>/mnt_<part>/)",
    )
    p_mount.add_argument(
        "--ro",
        action="store_true",
        help="Mount filesystem read-only (default: read-write)",
    )

    # 4. unmount
    p_unmount = subparsers.add_parser("unmount", help="Sync filesystem and unmount active loop partition")
    p_unmount.add_argument(
        "partition",
        type=str,
        help="Partition name to unmount (e.g. vendor, system, odm, product, or 'all')",
    )
    p_unmount.add_argument(
        "-l", "--lazy",
        action="store_true",
        help="Lazy unmount (umount -l) if partition device is busy",
    )
    p_unmount.add_argument(
        "--all",
        action="store_true",
        help="Unmount all currently mounted partitions",
    )

    # 5. status
    subparsers.add_parser("status", help="Display toolchain, cache, and build environment status")

    # 6. clean
    p_clean = subparsers.add_parser("clean", help="Purge build cache and temporary staging files")
    p_clean.add_argument(
        "--all",
        action="store_true",
        help="Also purge pristine base (.pristine_base/) and pristine vendor cache",
    )

    return parser


def handle_build(args: argparse.Namespace) -> int:
    """Handle build subcommand."""
    log_info("Executing build subcommand...")

    # Check stock base image (only required if pristine cache is not already populated)
    base_img = DEFAULT_BASE_IMG
    if not base_img.exists() and (args.from_scratch or not DEFAULT_CACHE_DIR.exists()):
        log_error(f"Base firmware image missing: {base_img}")
        return EXIT_MISSING_TOOL

    if args.dry_run:
        log_info("[DRY-RUN] Simulating firmware assembly pipeline:")
        log_info(f"[DRY-RUN] 1. Stock image: {base_img.name} (size: {base_img.stat().st_size:,} bytes)")
        log_info(f"[DRY-RUN] 2. Pristine cache: {DEFAULT_CACHE_DIR}")
        existing, next_v = scan_existing_versions(args.output_dir)
        target_v = args.version_num or next_v
        log_info(f"[DRY-RUN] 3. Target version: v{target_v} -> yandex_s905x3_custom_v{target_v}.img")
        log_info("[DRY-RUN] 4. Overlay directories: overlay/vendor, overlay/dts, overlay/boot")
        log_success("[DRY-RUN] Dry run completed successfully.")
        return EXIT_SUCCESS

    if args.clean:
        log_clean("Cleaning incremental state cache prior to build...")
        cache_file = PROJECT_ROOT / ".fw_builder_cache.json"
        if cache_file.exists():
            cache_file.unlink()

    if args.from_scratch:
        log_build("Rebuilding from scratch requested. Initializing pristine base...")
        try:
            ensure_pristine_base(base_img=base_img, cache_dir=DEFAULT_CACHE_DIR, force=True)
            log_success("Pristine base extracted and validated from scratch.")
        except Exception as exc:
            log_error(f"Failed to extract pristine base: {exc}")
            return EXIT_BUILD_FAILURE
    else:
        # Incremental check
        try:
            ensure_pristine_base(base_img=base_img, cache_dir=DEFAULT_CACHE_DIR, force=False)
            log_info("Pristine base cache verified.")
        except Exception as exc:
            log_error(f"Failed to verify pristine base: {exc}")
            return EXIT_BUILD_FAILURE

    # Delegate to builder.repack
    try:
        from builder.repack import build_image  # type: ignore
        code, out_img = build_image(
            from_scratch=args.from_scratch,
            verbose=args.verbose,
            output_dir=args.output_dir,
            version_num=args.version_num,
        )
        if code == 0:
            log_success(f"Firmware image built successfully: {out_img}")
        else:
            log_error(f"Firmware build failed (code {code}): {out_img}")
        return code
    except Exception as exc:
        log_error(f"Build failed with exception: {exc}")
        return EXIT_BUILD_FAILURE


def handle_watch(args: argparse.Namespace) -> int:
    """Handle watch subcommand."""
    log_watch(f"Starting firmware watcher daemon (debounce: {args.debounce}s, poll: {args.poll_interval}s)...")
    try:
        import time
        from builder.watcher import start_watcher
        from builder.repack import build_image

        def rebuild_callback():
            log_watch("Quiescence reached. Starting incremental build...")
            t0 = time.perf_counter()
            code, out_img = build_image(from_scratch=False, verbose=args.verbose)
            duration = time.perf_counter() - t0
            if code == 0:
                log_success(f"Firmware image rebuilt in {duration:.2f}s: {out_img}")
            else:
                log_error(f"Firmware rebuild failed in {duration:.2f}s (code: {code})")

        if getattr(args, "initial_build", False):
            rebuild_callback()

        start_watcher(
            debounce_seconds=args.debounce,
            poll_interval=args.poll_interval,
            callback=rebuild_callback,
            verbose=args.verbose,
        )
        return EXIT_SUCCESS
    except KeyboardInterrupt:
        log_info("Watcher daemon stopped by user.")
        return EXIT_KEYBOARD_INTERRUPT
    except Exception as exc:
        log_error(f"Watcher daemon error: {exc}")
        return EXIT_BUILD_FAILURE


def handle_mount(args: argparse.Namespace) -> int:
    """Handle mount subcommand."""
    partition = args.partition
    log_mount(f"Mounting partition '{partition}' (ro={args.ro})...")
    try:
        from builder.mount import mount_partition
        mnt_path = mount_partition(partition, read_only=args.ro, mount_point=args.mount_point)
        log_success(f"Partition '{partition}' successfully mounted at {mnt_path}")
        return EXIT_SUCCESS
    except ValueError as exc:
        log_error(f"Invalid partition argument: {exc}")
        return EXIT_ARG_ERROR
    except Exception as exc:
        log_error(f"Failed to mount partition '{partition}': {exc}")
        return EXIT_MOUNT_ERROR


def handle_unmount(args: argparse.Namespace) -> int:
    """Handle unmount subcommand."""
    partition = args.partition
    log_unmount(f"Unmounting partition '{partition}' (lazy={args.lazy})...")
    try:
        from builder.mount import unmount_partition, list_mounted_partitions
        if getattr(args, "all", False) or partition.lower() == "all":
            mounted = list_mounted_partitions()
            if not mounted:
                log_info("No active partitions currently mounted.")
                return EXIT_SUCCESS
            all_ok = True
            for part_name in list(mounted.keys()):
                ok = unmount_partition(part_name, lazy=args.lazy)
                if ok:
                    log_success(f"Partition '{part_name}' unmounted cleanly.")
                else:
                    log_error(f"Failed to unmount '{part_name}'.")
                    all_ok = False
            return EXIT_SUCCESS if all_ok else EXIT_MOUNT_ERROR

        ok = unmount_partition(partition, lazy=args.lazy)
        if ok:
            log_success(f"Partition '{partition}' unmounted cleanly.")
            return EXIT_SUCCESS
        else:
            log_error(f"Failed to unmount partition '{partition}' (not mounted or device busy).")
            return EXIT_MOUNT_ERROR
    except Exception as exc:
        log_error(f"Unmount error: {exc}")
        return EXIT_MOUNT_ERROR



def handle_status(args: argparse.Namespace) -> int:
    """Handle status subcommand."""
    log_status("=== Automated Firmware Assembly Status ===")

    # 1. Base firmware
    if DEFAULT_BASE_IMG.exists():
        size_gb = DEFAULT_BASE_IMG.stat().st_size / (1024 ** 3)
        log_status(f"Stock Firmware Base : {DEFAULT_BASE_IMG.name} ({size_gb:.2f} GB) [FOUND]")
    else:
        log_status(f"Stock Firmware Base : {DEFAULT_BASE_IMG.name} [MISSING]")

    # 2. Pristine cache
    valid, errors = validate_pristine_base(DEFAULT_CACHE_DIR)
    if valid:
        log_status(f"Pristine Base Cache : {DEFAULT_CACHE_DIR.name} (21 items verified) [READY]")
    else:
        item_count = len(list(DEFAULT_CACHE_DIR.iterdir())) if DEFAULT_CACHE_DIR.exists() else 0
        log_status(f"Pristine Base Cache : {DEFAULT_CACHE_DIR.name} ({item_count} items) [NOT READY]")

    # 3. Pristine vendor
    if DEFAULT_VENDOR_CACHE.exists():
        fc = (DEFAULT_VENDOR_CACHE / "vendor_file_contexts").exists()
        fs = (DEFAULT_VENDOR_CACHE / "vendor_fs_config").exists()
        log_status(f"Pristine Vendor     : {DEFAULT_VENDOR_CACHE.name} (SELinux: {fc}, fs_config: {fs}) [READY]")
    else:
        log_status(f"Pristine Vendor     : {DEFAULT_VENDOR_CACHE.name} [NOT EXTRACTED]")

    # 4. Overlays
    for sub in ["vendor", "dts", "boot"]:
        ov = PROJECT_ROOT / "overlay" / sub
        cnt = len(list(ov.iterdir())) if ov.exists() else 0
        log_status(f"Overlay '{sub:<6}'     : {ov.relative_to(PROJECT_ROOT)} ({cnt} items)")

    # 5. Version scanner
    versions, next_v = scan_existing_versions()
    log_status(f"Existing Versions   : {len(versions)} custom images found (v{versions[0]}..v{versions[-1]})" if versions else "No custom images found")
    log_status(f"Next Target Version : v{next_v} (yandex_s905x3_custom_v{next_v}.img)")

    return EXIT_SUCCESS


def handle_clean(args: argparse.Namespace) -> int:
    """Handle clean subcommand."""
    log_clean("Purging cache and temporary compilation files...")
    cache_file = PROJECT_ROOT / ".fw_builder_cache.json"
    if cache_file.exists():
        cache_file.unlink()
        log_clean(f"Removed cache file: {cache_file.name}")

    if args.all:
        if DEFAULT_CACHE_DIR.exists():
            shutil.rmtree(DEFAULT_CACHE_DIR)
            log_clean(f"Purged pristine base directory: {DEFAULT_CACHE_DIR.name}")
        if DEFAULT_VENDOR_CACHE.exists():
            shutil.rmtree(DEFAULT_VENDOR_CACHE)
            log_clean(f"Purged pristine vendor directory: {DEFAULT_VENDOR_CACHE.name}")

    log_success("Clean completed successfully.")
    return EXIT_SUCCESS


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return EXIT_SUCCESS

    handler_map = {
        "build": handle_build,
        "watch": handle_watch,
        "mount": handle_mount,
        "unmount": handle_unmount,
        "status": handle_status,
        "clean": handle_clean,
    }

    handler = handler_map.get(args.subcommand)
    if not handler:
        parser.print_help()
        return EXIT_ARG_ERROR

    try:
        return handler(args)
    except KeyboardInterrupt:
        log_info("Operation interrupted by user.")
        return EXIT_KEYBOARD_INTERRUPT
    except Exception as exc:
        log_error(f"Command execution error: {exc}")
        return EXIT_BUILD_FAILURE


if __name__ == "__main__":
    sys.exit(main())

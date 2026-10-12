"""
Base Firmware Extraction & Pristine Base Cache Engine.
Module: builder.pristine
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from builder.bridge import is_windows, win_to_wsl_path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_IMG = PROJECT_ROOT / "yandex_1.99.img"
DEFAULT_CACHE_DIR = PROJECT_ROOT / ".pristine_base"
DEFAULT_VENDOR_CACHE = PROJECT_ROOT / ".pristine_vendor"

AMPACK_CANDIDATES = [
    PROJECT_ROOT.parent / "bin" / "ampack",
    PROJECT_ROOT / "tools" / "bin" / "ampack",
    "/home/lmods/AtriOS-Android/tools/bin/ampack",
]

IMGEXTRACTOR_CANDIDATES = [
    PROJECT_ROOT.parent / "bin" / "imgextractor.py",
    PROJECT_ROOT / "tools" / "bin" / "imgextractor.py",
    "/home/lmods/AtriOS-Android/tools/bin/imgextractor.py",
]

# The complete 21 items contained within stock yandex_1.99.img
STOCK_21_ITEMS: Dict[str, int] = {
    "DDR.USB": 1553264,
    "DDR_ENC.USB": 1553264,
    "UBOOT.USB": 1553264,
    "UBOOT_ENC.USB": 1553264,
    "_aml_dtb.PARTITION": 128032,
    "aml_sdc_burn.UBOOT": 1553264,
    "aml_sdc_burn.UBOOT.ENC": 1553264,
    "aml_sdc_burn.ini": 602,
    "boot.PARTITION": 16777216,
    "bootloader.PARTITION": 1553264,
    "dtbo.PARTITION": 8388608,
    "logo.PARTITION": 1338688,
    "meson1.dtb": 128032,
    "meson1_ENC.dtb": 128032,
    "odm.PARTITION": 134217728,
    "platform.conf": 155,
    "product.PARTITION": 134217728,
    "recovery.PARTITION": 25165824,
    "system.PARTITION": 1551892480,
    "vbmeta.PARTITION": 4096,
    "vendor.PARTITION": 536870912,
}

STOCK_SHA1_HASHES: Dict[str, str] = {
    "_aml_dtb.PARTITION": "c044c66f42048c38438aa59ac34eaf19f5bf8105",
    "boot.PARTITION": "3af8b524895573d8fe1df2d3f2928443e5e1a520",
    "bootloader.PARTITION": "85a74248134c249ebdedc23315ab497e7de73aa0",
    "dtbo.PARTITION": "da5913756cc5f6b81d03cbdcd924668bd10cf544",
    "logo.PARTITION": "6ca5a420ffb7fc28aaa2450094f0ab838d02fdd0",
    "odm.PARTITION": "eebb9acf2570601ebe999f4b86b35d8882c95789",
    "product.PARTITION": "6ccd449c53023d8f6916cb0550193844126c0f3e",
    "recovery.PARTITION": "e6293a1d11b1dd5f2c22856d19ef63fa3bf30b8f",
    "system.PARTITION": "84181ad46faeb34ab13c78a6af52d2c4192579fa",
    "vbmeta.PARTITION": "762b70a3e70c89aaa43ed7f0e1780174dc510f3e",
    "vendor.PARTITION": "4d6756755aa10c29acc8580838e45258144337e5",
}

IMMUTABLE_STOCK_PARTITIONS: List[str] = [
    "system.PARTITION",
    "odm.PARTITION",
    "product.PARTITION",
    "recovery.PARTITION",
    "dtbo.PARTITION",
    "logo.PARTITION",
    "platform.conf",
]


def _find_binary(candidates: List[str]) -> Optional[str]:
    """Find existing binary path from list of candidates."""
    for c in candidates:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    return candidates[0] if candidates else None


def validate_pristine_base(
    cache_dir: Path | str,
    strict_sizes: bool = False,
    verify_checksums: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate that all expected items exist in pristine base cache.
    Returns (is_valid, list_of_error_messages).
    """
    cd = Path(cache_dir)
    errors: List[str] = []

    if not cd.exists() or not cd.is_dir():
        return False, [f"Pristine cache directory does not exist: {cd}"]

    for item_name, expected_size in STOCK_21_ITEMS.items():
        item_path = cd / item_name
        if not item_path.exists():
            errors.append(f"Missing pristine item: {item_name}")
            continue

        if strict_sizes:
            actual_size = item_path.stat().st_size
            if actual_size != expected_size:
                errors.append(
                    f"Size mismatch for {item_name}: expected {expected_size}, got {actual_size}"
                )

        if verify_checksums and item_name in STOCK_SHA1_HASHES:
            sha1 = hashlib.sha1()
            with open(item_path, "rb") as f:
                while chunk := f.read(65536):
                    sha1.update(chunk)
            if sha1.hexdigest() != STOCK_SHA1_HASHES[item_name]:
                errors.append(
                    f"SHA1 mismatch for {item_name}: expected {STOCK_SHA1_HASHES[item_name]}, got {sha1.hexdigest()}"
                )

    return len(errors) == 0, errors


def ensure_pristine_vendor(
    vendor_partition_path: Path | str,
    vendor_cache_dir: Optional[Path | str] = None,
) -> Dict[str, str]:
    """
    Extract stock vendor filesystem and filesystem configs (vendor_fs_config,
    vendor_file_contexts) into .pristine_vendor/ cache.
    """
    vp = Path(vendor_partition_path)
    vc = Path(vendor_cache_dir or DEFAULT_VENDOR_CACHE)
    vc.mkdir(parents=True, exist_ok=True)

    config_fc = vc / "vendor_file_contexts"
    config_fs = vc / "vendor_fs_config"
    vendor_tree = vc / "vendor"

    # If already extracted and configs present, return mapping
    if config_fc.exists() and config_fs.exists() and (vendor_tree.exists() or (vc / "app").exists()):
        return {
            "vendor_file_contexts": str(config_fc),
            "vendor_fs_config": str(config_fs),
            "vendor_dir": str(vendor_tree if vendor_tree.exists() else vc),
        }

    # Extract vendor filesystem via imgextractor.py
    print("[BUILD] Extracting stock vendor filesystem and SELinux configs...")
    imgextractor = _find_binary(IMGEXTRACTOR_CANDIDATES)

    if is_windows():
        wsl_imgextractor = imgextractor
        wsl_vp = win_to_wsl_path(str(vp))
        wsl_vc = win_to_wsl_path(str(vc))
        cmd = [
            "wsl.exe", "-d", "Ubuntu-22.04", "-u", "lmods", "--",
            "sudo", "python3", wsl_imgextractor, wsl_vp, wsl_vc,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"imgextractor failed: {res.stderr}\n{res.stdout}")
    else:
        cmd = ["sudo", "python3", imgextractor, str(vp), str(vc)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"imgextractor failed: {res.stderr}\n{res.stdout}")

    # Ensure configs are copied to root of vendor_cache_dir if placed inside config/
    sub_config = vc / "config"
    if sub_config.exists():
        for cfg_file in sub_config.iterdir():
            target_cfg = vc / cfg_file.name
            if not target_cfg.exists():
                shutil.copy2(cfg_file, target_cfg)

    return {
        "vendor_file_contexts": str(vc / "vendor_file_contexts"),
        "vendor_fs_config": str(vc / "vendor_fs_config"),
        "vendor_dir": str(vc / "vendor" if (vc / "vendor").exists() else vc),
    }


def ensure_pristine_base(
    base_img: Optional[str | Path] = None,
    cache_dir: Optional[str | Path] = None,
    force: bool = False,
) -> Dict[str, str]:
    """
    Ensure base firmware image (yandex_1.99.img) is extracted to .pristine_base/.
    Validates all 21 items and returns a mapping of partition/item name -> file path.
    Guarantees pristine base is immutable.
    """
    img_path = Path(base_img or DEFAULT_BASE_IMG)
    cd = Path(cache_dir or DEFAULT_CACHE_DIR)

    # 1. Check if cache directory already exists and contains partitions
    if cd.exists() and not force:
        # Check if files are present
        existing_files = list(cd.iterdir())
        if existing_files:
            mapping: Dict[str, str] = {}
            for f in existing_files:
                mapping[f.name] = str(f.resolve())
                stem = f.name.split(".")[0]
                if stem not in mapping:
                    mapping[stem] = str(f.resolve())

            # If at least boot partition or majority items exist, cache is populated
            if "boot.PARTITION" in mapping or "boot" in mapping:
                return mapping

    # 2. Base image check
    if not img_path.exists():
        raise FileNotFoundError(f"Base firmware image not found: {img_path}")

    # 3. Perform genuine ampack unpack
    cd.mkdir(parents=True, exist_ok=True)
    ampack = _find_binary(AMPACK_CANDIDATES)

    print(f"[BUILD] Unpacking stock base image: {img_path.name} -> {cd.name} via ampack...")

    if is_windows():
        wsl_img = win_to_wsl_path(str(img_path))
        wsl_cd = win_to_wsl_path(str(cd))
        cmd = [
            "wsl.exe", "-d", "Ubuntu-22.04", "-u", "lmods", "--",
            ampack, "unpack", wsl_img, wsl_cd,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"ampack unpack failed: {res.stderr}\n{res.stdout}")
    else:
        cmd = [ampack, "unpack", str(img_path), str(cd)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"ampack unpack failed: {res.stderr}\n{res.stdout}")

    # 4. Validate extracted items
    valid, errors = validate_pristine_base(cd, strict_sizes=True)
    if not valid:
        print(f"[WARN] Pristine base validation warnings: {errors}")

    # 5. Extract stock vendor filesystem to .pristine_vendor/
    vendor_part = cd / "vendor.PARTITION"
    if vendor_part.exists():
        try:
            ensure_pristine_vendor(vendor_part)
        except Exception as e:
            print(f"[WARN] Could not unpack vendor filesystem: {e}")

    # 6. Build partition mapping
    mapping = {}
    for f in cd.iterdir():
        mapping[f.name] = str(f.resolve())
        stem = f.name.split(".")[0]
        if stem not in mapping:
            mapping[stem] = str(f.resolve())

    return mapping


def get_stock_partition(name: str, cache_dir: Optional[str | Path] = None) -> Optional[str]:
    """
    Retrieve absolute path to a stock partition file from pristine base cache.
    Accepts stem ("boot", "vendor", "system") or full filename ("boot.PARTITION").
    """
    cd = Path(cache_dir or DEFAULT_CACHE_DIR)

    # Direct filename check
    candidate = cd / name
    if candidate.exists():
        return str(candidate.resolve())

    # Try common extensions
    for ext in [".PARTITION", ".USB", ".dtb", ".conf", ".ini"]:
        candidate = cd / f"{name}{ext}"
        if candidate.exists():
            return str(candidate.resolve())

    # If cache not populated yet, ensure pristine base and check mapping
    if not cd.exists() or not any(cd.iterdir()):
        mapping = ensure_pristine_base(cache_dir=cd)
        if name in mapping:
            return mapping[name]
        for ext in [".PARTITION", ".USB", ".dtb", ".conf", ".ini"]:
            full = f"{name}{ext}"
            if full in mapping:
                return mapping[full]

    return None

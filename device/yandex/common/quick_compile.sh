#! /bin/bash

if [ $# -eq 1 ] && [ $1 == "help" ]; then
    printf "Usage:\n"
    printf "./device/yandex/common/quick_compile.sh\n"
    printf "    select project name number and drm type to compile otapackage\n\n"
    printf "./device/yandex/common/quick_compile.sh uboot\n"
    printf "    select project name number and drm type to compile someone uboot\n\n"
    printf "./device/yandex/common/quick_compile.sh all\n"
    printf "    select project name number and drm type to compile all chip uboot\n\n"
    printf "./device/yandex/common/quick_compile.sh [bootimage|dtbimage|vendorimage]\n"
    printf "    select project name number and drm type to compile sub-image\n\n"
    exit
fi

#Project Name             SOC Name                Hardware Name                  device project name            uboot compile params                 tdk path
project[1]="x3_yandex"    ;soc[1]="S905X3"        ;hardware[1]="yandex_station"  ;module[1]="x3_yandex"         ;uboot[1]="yandex_station_v1"        ;tdk[1]="g12a/bl32.img"
project[2]="x2_m401a"     ;soc[2]="S905X2"        ;hardware[2]="flyer_x2"        ;module[2]="x2_m401a"          ;uboot[2]="g12a_u212_v1"             ;tdk[2]="g12a/bl32.img"
project[3]="x2_m401a_atv" ;soc[3]="S905X2"        ;hardware[3]="flyer_x2"        ;module[3]="x2_m401a_atv"      ;uboot[3]="g12a_u212_v1"             ;tdk[3]="g12a/bl32.img"
project[4]="x2_e900v22c"  ;soc[4]="S905X2"        ;hardware[4]="flyer_x2"        ;module[4]="x2_e900v22c"       ;uboot[4]="g12a_u212_v1"             ;tdk[4]="g12a/bl32.img"
project[5]="x3_x96q5"     ;soc[5]="S905X3"        ;hardware[5]="flyer_x96q5"     ;module[5]="x3_x96q5"          ;uboot[5]="g12a_x96_q1_v1"           ;tdk[5]="g12a/bl32.img"
project[6]="x3_x96q5_atv" ;soc[6]="S905X3"        ;hardware[6]="x96q5"           ;module[6]="x3_x96q5_atv"      ;uboot[6]="g12a_x96_q1_v1"           ;tdk[6]="g12a/bl32.img"

platform_avb_param=""
platform_type=1
project_path="null"
uboot_name="null"

read_platform_type() {
    while true :
    do
        printf "[%3s]   [%15s]   [%15s]  [%15s]\n" "NUM" "PROJECT" "SOC TYPE" "HARDWARE TYPE"
        echo "---------------------------------------------"
        for i in `seq ${#project[@]}`;do
            printf "[%3d]   [%15s]  [%15s]  [%15s]\n" $i ${project[i]} ${soc[i]} ${hardware[i]}
        done

        echo "---------------------------------------------"
        read -p "please select platform type (default 1 (x3_yandex)):" platform_type
        if [ ${#platform_type} -eq 0 ]; then
            platform_type=1
        fi
        if [[ $platform_type -lt 1 || $platform_type -gt ${#project[@]} ]]; then
            echo -e "The platform type is illegal!!! Need select again [1 ~ ${#project[@]}]\n"
        else
            break
        fi
    done
    project_path=${module[platform_type]}
    uboot_name=${uboot[platform_type]}
}

compile_uboot(){
    echo -e "[./mk $uboot_name --systemroot]"
    ./mk $uboot_name --systemroot;

    target_dir="../../device/yandex/station_max"
    if [ ! -d "$target_dir" ]; then
        target_dir="../../device/yandex/$project_path"
    fi
    mkdir -p "$target_dir/upgrade"
    cp build/u-boot.bin "$target_dir/bootloader.img" 2>/dev/null || true
    cp build/u-boot.bin.usb.bl2 "$target_dir/upgrade/u-boot.bin.usb.bl2" 2>/dev/null || true
    cp build/u-boot.bin.usb.tpl "$target_dir/upgrade/u-boot.bin.usb.tpl" 2>/dev/null || true
    cp build/u-boot.bin.sd.bin "$target_dir/upgrade/u-boot.bin.sd.bin" 2>/dev/null || true
}

read_platform_type
source build/envsetup.sh
lunch "${project_path}-userdebug"
make installclean

if [ $# -eq 1 ]; then
    if [ $1 == "bootimage" ] \
    || [ $1 == "logoimg" ] \
    || [ $1 == "recoveryimage" ] \
    || [ $1 == "systemimage" ] \
    || [ $1 == "vendorimage" ] \
    || [ $1 == "odm_image" ] \
    || [ $1 == "dtbimage" ] ; then
        make $1 -j32
        exit
    fi
fi

cd bootloader/uboot-repo
compile_uboot

cd ../../
make otapackage -j32
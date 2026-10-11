BOARD_SEPOLICY_DIRS += \
    device/yandex/common/sepolicy \
    device/yandex/common/sepolicy/aml_core
ifneq ($(TARGET_BUILD_GOOGLE_ATV), true)
BOARD_SEPOLICY_DIRS += \
    device/google/atv/sepolicy
endif

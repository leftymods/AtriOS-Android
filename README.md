# AtriOS Linux — Yandex Station Max (Replaced SoC to S905X3)

<p align="center">
  <strong>Autonomous Embedded Linux Distribution for Yandex Station Max with replaced SoC to S905X3</strong>
  <br />
  <em>Complete local, cloud-free replacement firmware for <strong>Yandex Station Max</strong> (Hardware mod: S905X3 / SM1 SoC swap)</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Target-Yandex%20Station%20Max-blue?style=flat-square" alt="Target" />
  <img src="https://img.shields.io/badge/Hardware%20Mod-SoC%20Replaced%20to%20S905X3-orange?style=flat-square" alt="SoC Mod" />
  <img src="https://img.shields.io/badge/Architecture-ARM64%20(aarch64)-0284c7?style=flat-square" alt="Architecture" />
  <img src="https://img.shields.io/badge/Buildroot-2024.02%20LTS-16a34a?style=flat-square" alt="Buildroot" />
  <img src="https://img.shields.io/badge/Linux%20Kernel-4.9.113%20(SMP%20PREEMPT)-7c3aed?style=flat-square" alt="Kernel" />
  <img src="https://img.shields.io/badge/Audio-PipeWire%20%7C%20ALSA%20Plug%20%7C%20SY6045S-purple?style=flat-square" alt="Audio" />
  <img src="https://img.shields.io/badge/Hardware%20Testing-Physical%20Device%20Boot%20Verified-brightgreen?style=flat-square" alt="Hardware Testing" />
  <img src="https://img.shields.io/badge/License-GPL--2.0-slate?style=flat-square" alt="License" />
</p>

> [!NOTE]
> **Physical Device Boot Verified / Проверено на реальном железе**:
> Прошивка успешно загружается на **Яндекс Станции Макс с аппаратно заменённым процессором на Amlogic S905X3 (SM1)**. Матричный дисплей 25x16 (Gowin FPGA, монохромный с индивидуальной яркостью каждого светодиода), верхнее 24-канальное RGB-кольцо (IS31FL3236A), датчик освещенности (LTR-308ALS), энкодер громкости и обе верхние физические кнопки аппаратно поддержаны и работают в среде Linux.

---

## Обзор проекта / Overview

**AtriOS Linux** — независимый автономный дистрибутив встроенного Linux от **leftymods** для умной колонки **Яндекс Станция Макс** с аппаратно заменённым процессором на **Amlogic S905X3 (SM1)** ARM Cortex-A55.

Проект полностью заменяет штатный закрытый Android 9 на чистую систему на базе **Buildroot 2024.02 LTS**:
- Загрузка напрямую в `/sbin/init` (Busybox) за считанные секунды без Android/AOSP, ART, Zygote и сервисов Яндекса.
- Облегченный образ (~1.46 ГБ вместо 2.4 ГБ): исключены неиспользуемые разделы Android (`vendor`, `product`, `odm`, `recovery`, `dtbo`, `vbmeta`).
- Звуковая подсистема ALSA и PipeWire с автоконверсией форматов (`asound.conf` plug) для исключения ошибок EINVAL (-22), автоматической инициализацией усилителей Silergy SY6045S и поддержкой микрофонного массива.
- Прямое управление всей периферией Станции Макс: монохромный матричный экран 25x16 Gowin FPGA с поканальным управлением яркостью светодиодов (0..255), 24-канальное RGB-кольцо, энкодер громкости, датчик света, обе верхние кнопки (опрос через таймер 20мс в DTS).
- Wi-Fi SDIO контроллер (RTL8822CS/ES) с автоматическим управлением питанием через `/dev/wifi_power`.
- **100% автономность репозитория**: все инструменты сборки, драйверы, оверлеи и упаковщик прошивки живут в репозитории без внешних зависимостей.

---

## Hardware & Subsystem Status (Yandex Station Max)

| Subsystem | Hardware Component | Bus / Interface | Driver / Daemon | Status |
|---|---|---|---|:---:|
| **Firmware Build System** | Self-contained build pipeline (`build_atrios.sh`) | Host / WSL2 | `make_ext4fs` + `ampack` (Lightweight 1.46GB) | [x] Verified in pipeline |
| **Bootloader & ROM Code** | Native S905X3 Bootloader (`DDR.USB`, `UBOOT.USB`) | eMMC / USB Burn | `ampack` v2 verified | [x] Verified on hardware |
| **UART Serial Console** | Amlogic UART0 (115200 8N1) | `/dev/ttyS0` | `ttyS0` interactive root shell | [x] Verified on hardware |
| **Monochrome LED Screen** | Gowin GW1N FPGA (25×16 white LEDs, per-pixel brightness 0..255) | SPI1 (`GPIOX_8`), CS: `GPIOH_7` | `gowin_led_device` (`/dev/fb4`, RGB888 1200B) | [x] Hardware verified |
| **LED Ring** | Dual IS31FL3236A (24 RGB channels / 72 LEDs, Red/Blue fixed in DTB) | I2C0 (`0x3c`, `0x3f`) | `quasar_led_ring.ko` (`/dev/fb5`) | [x] Hardware verified |
| **Light Sensor** | Lite-On LTR-308ALS ambient light sensor | I2C0 (`0x53`) | `ltr308als01` (`iio:device0`) | [x] Hardware verified |
| **Rotary Knob (Volume)** | Dual-phase quadrature encoder | `GPIOH_6` (A), `GPIOAO_10` (B) | `rotary-volume.ko` | [x] Hardware verified |
| **Top Buttons (Alice / Mute)**| Dual Tactile Push Buttons | `GPIOA_15` (Alice), `GPIOA_14` (Mute) | `gpio_keypad` (polling mode) | [x] Configured in DTS |
| **Speaker Amplifiers** | Silergy SY6045S 20V + ES8156 DAC | TDM-B, I2C2 (`0x2a`, `0x2b`) | `snd-soc-sy6045s` + `S03amplifiers` | [x] Configured & firmware loaded |
| **Audio Playback & Capture** | AML-AUGESOUND I2S / PDM | ALSA / PipeWire | `asound.conf` (Plug adapter) | [x] Configured |
| **Microphone Array** | Everest ES7210 4-ch ADC + TDM-C | TDM-C, I2C1 | `snd-soc-es7210` (8-channel capture) | [x] Driver registered |
| **Wi-Fi** | Realtek RTL8822CS (802.11ac 2×2 Dual-Band) | SDIO (`sd_emmc_a`), `/dev/wifi_power` | `88x2es.ko` + `atrios-wifi-power` | [x] Power sequence added |
| **Bluetooth** | Realtek RTL8822CS Bluetooth 5.0 | UART_A (`/dev/ttyAML1`), BT_EN: Pin 84 | `rtk_bt` (`hci0`) | [ ] Untested on hardware |
| **Zigbee** | Silicon Labs EFR32 | UART_AO_B (`/dev/ttyAML4`), Pin 82/83 | `zb_control` (Z2M coordinator) | [ ] Driver registered |
| **HDMI Video** | MPI7002 / Generic HDMI TX | HDMI TX (`osd1` / `fb0`) | `/dev/fb0` (1024x600 @ 60Hz) | [x] Verified on hardware |

---

## Built-in CLI: единая команда `atrios`

Все утилиты объединены в одну команду `/usr/bin/atrios` (внутренние модули лежат в `/usr/lib/atrios/`, отдельных `atrios-*` в PATH больше нет). Без аргументов `atrios` печатает список команд.

| Команда | Что делает |
|---|---|
| `atrios status` | Обзор Wi-Fi / Bluetooth / Zigbee |
| `atrios test` | Тест динамиков и 8-канального массива микрофонов |
| `atrios screen clock \| smile \| happy \| eyes [state] \| ticker "TEXT" \| fill [0..255] \| pixel X Y [B] \| gradient \| off` | Монохромный экран 25x16 |
| `atrios ring rainbow \| volume N \| off` | RGB-кольцо (24 светодиода) |
| `atrios sensor` | Датчик освещённости (люксы) |
| `atrios volume [0..100%]`, `atrios mute [on\|off]`, `atrios play [file]`, `atrios record [sec] [file]`, `atrios amps` | Звук и усилители SY6045S |
| `atrios wifi [scan \| connect SSID PASS \| power 1\|0]` | Wi-Fi |
| `atrios bt [init \| scan]` | Bluetooth |
| `atrios zigbee [reset \| ping]` | Zigbee (EFR32) |
| `atrios input` | Монитор кнопок, крутилки и пульта |

Фоновые демоны запускаются из `/etc/init.d/S60atrios`: часы на экране (`/usr/lib/atrios/screend`) и громкость/мут (`/usr/lib/atrios/rotaryd`). Мут микрофона кольцом не подсвечивается.

Оболочка: `sh` остаётся login-shell, а `~/.profile` запускает fish только если он реально стартует (иначе остаётся `sh`). Настройки fish: `/etc/fish/config.fish`.

---

## Чек-лист проверки на плате (по UART)

Подключаемся к UART-консоли (`ttyS0`, 115200 8N1):

```bash
lsmod                      # модули ядра
atrios input               # кнопки и энкодер
atrios ring rainbow        # кольцо
atrios screen ticker HELLO # экран
atrios sensor              # датчик света
atrios test                # звук и микрофоны
atrios status              # Wi-Fi / BT / Zigbee
```

---

## Структура репозитория

Весь проект полностью автономен и организован в одной папке:

```
AtriOS-Android/
├── board/yandex/station2/
│   ├── rootfs_overlay/           # Оверлей файлов rootfs (прошивки, модули, утилиты)
│   │   ├── etc/                  # asound.conf, init-скрипты, wpa_supplicant.conf
│   │   ├── lib/firmware/         # Прошивки Gowin FPGA, SY6045S, Realtek Wi-Fi
│   │   ├── lib/modules/4.9.113/  # Модули ядра кольца, экрана, звука, сенсора
│   │   └── usr/bin/              # Команда atrios (usr/bin) и модули (usr/lib/atrios)
│   └── station2_defconfig        # Конфиг Buildroot под Станцию Макс (S905X3)
├── common/                       # Ядро 4.9.113 и дерево устройств (DTS)
├── tools/
│   ├── bin/                      # Автономные утилиты сборщика (ampack, make_ext4fs, dtbTool)
│   └── fw_builder/               # Сборщик и упаковщик прошивки (fw_builder.py)
│       └── overlay/dts/          # DTS под Станцию Макс (S905X3) с обеими кнопками
└── build_atrios.sh               # Главный скрипт сборки одной командой
```

---

## Сборка прошивки / How to Build

Сборка полностью автономна и выполняется в окружении Linux / WSL2:

```bash
cd /home/lmods/AtriOS-Android
./build_atrios.sh 106
```

Готовый образ для прошивки:  
`tools/fw_builder/yandex_s905x3_custom_v106.img` (1.46 ГБ)

Прошивка осуществляется через стандартный **Amlogic USB Burning Tool** или через U-Boot команду `update`.

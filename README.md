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

## Built-in CLI Tooling & Daemons

В состав rootfs включены готовые диагностические утилиты и сервисы в `/usr/bin/`:

| Utility | Description | Example Command |
|---|---|---|
| `atrios-test-buttons` | Мониторинг кнопок Алисы, Mic Mute, крутилки и датчика света | `atrios-test-buttons` |
| `atrios-rotaryd` | Демон громкости на кольце и софтового мута (красное кольцо) | `atrios-rotaryd &` |
| `atrios-test-ring` | Тест эффектов 24 RGB-каналов (радуга, дуга, заливка, выключение) | `atrios-test-ring rainbow` |
| `atrios-test-screen` | Тест монохромного экрана 25x16 (бегущая строка, часы, глаза Алисы, смайлы, поканальная яркость) | `atrios-test-screen ticker "ATRIOS"` |
| `atrios-screend` | Фоновый демон часов (HH:MM) на экране 25x16 | `atrios-screend &` |
| `atrios-test-sensor` | Считывание люксов LTR-308ALS в реальном времени | `atrios-test-sensor` |
| `atrios-test-audio` | Генератор тона в динамики и запись с микрофонов (ALSA plug) | `atrios-test-audio` |
| `atrios-wifi-power` | Управление питанием SDIO-шины Wi-Fi контроллера | `atrios-wifi-power 1` |
| `atrios-test-wifi` | Диагностика питания SDIO, сканирование и подключение Wi-Fi | `atrios-test-wifi` |

---

## Чек-лист проверки на плате (по UART)

Подключаемся к UART-консоли (`ttyS0`, 115200 8N1):

### 1. Проверка загруженных модулей ядра:
```bash
lsmod
```
В списке присутствуют: `quasar_led_ring`, `quasar_led_screen`, `rotary-volume`, `ltr308als01`, `snd-soc-sy6045s`, `snd-soc-es7210`, `88x2es`, `gowin_led_device`.

### 2. Кнопки и энкодер:
```bash
atrios-test-buttons
```
- Кнопка 1 (Алиса): код `KEY_VOICECOMMAND` (582) / `KEY_POWER` (116).
- Кнопка 2 (Mic Mute): код `KEY_MICMUTE` (248), срабатывание софтового мута и красного кольца.
- Крутилка: шаги громкости `KEY_PAGEUP` / `KEY_PAGEDOWN`.

### 3. Верхнее RGB-кольцо:
```bash
atrios-test-ring rainbow          # бегущая радуга
atrios-test-ring volume 70        # индикатор громкости на 70%
atrios-test-ring fill 255 0 0     # красный цвет
atrios-test-ring off              # выключить
```

### 4. Монохромный экран 25x16 (Gowin FPGA, 1200 байт RGB888, яркость 0..255):
```bash
atrios-test-screen clock          # текущее время (HH:MM)
atrios-test-screen ticker "HELLO" # плавная бегущая строка с полным шрифтом
atrios-test-screen eyes           # анимированные глаза Алисы
atrios-test-screen smile          # улыбающееся лицо
atrios-test-screen gradient       # 2D градиент яркости (0..255)
atrios-test-screen fill 120       # равномерная заливка с заданной яркостью
atrios-test-screen pixel 12 8 255 # установка одного пикселя (x, y, brightness)
atrios-test-screen test           # полный демонстрационный тест экрана
atrios-test-screen off            # выключить экран
```

### 5. Датчик освещенности:
```bash
atrios-test-sensor
```
Выводит показания в люксах. При закрытии рукой значения падают.

### 6. Звук и усилители SY6045S:
```bash
atrios-test-audio
```
Проверяет привязку усилителей `2-002a` и `2-002b`, воспроизводит проверочный тон 48 кГц через `asound.conf` plug и записывает 3 сек аудио.

### 7. Wi-Fi (RTL8822CS/ES):
```bash
atrios-test-wifi
# Или подключение к сети:
atrios-test-wifi "MySSID" "Password123"
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
│   │   └── usr/bin/              # Утилиты и демоны atrios-*
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

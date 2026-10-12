# 🚀 AtriOS Linux — Yandex Station 2 / Max (Amlogic S905X3 / SM1)

<div align="center">

![Platform](https://img.shields.io/badge/Platform-Amlogic%20S905X3%20%28SM1%29-blue.svg?style=for-the-badge)
![OS](https://img.shields.io/badge/OS-AtriOS%20Linux%20%28Buildroot%202024.02%29-green.svg?style=for-the-badge)
![Kernel](https://img.shields.io/badge/Kernel-Linux%204.9.113%20%28SMP%20PREEMPT%29-orange.svg?style=for-the-badge)
![Audio](https://img.shields.io/badge/Audio-PipeWire%20%2F%20ALSA%208--Ch-purple.svg?style=for-the-badge)
![Security](https://img.shields.io/badge/AVB%202.0-RSA%204096--bit-red.svg?style=for-the-badge)
![Maintainer](https://img.shields.io/badge/Maintainer-leftymods-cyan.svg?style=for-the-badge)

**Clean, high-performance embedded Linux distribution (Buildroot LTS) replacing stock Android on Yandex Station 2 / Station Max hardware.**

[English Documentation](#-english-documentation) • [Русская документация](#-русская-документация)

</div>

---

<a name="-english-documentation"></a>
## 📖 English Documentation

### 1. Overview & Architecture

**AtriOS Linux** is a modern, lightweight embedded Linux distribution developed by **leftymods** for the **Yandex Station 2** and **Station Max** smart speaker hardware platform, powered by the **Amlogic S905X3 (SM1)** quad-core ARM Cortex-A55 SoC.

Instead of heavy and locked-down Android userspace frameworks, AtriOS boots directly into an optimized **Buildroot 2024.02 LTS** environment with native ALSA/PipeWire audio, full reverse-engineered hardware control, and dedicated system daemons.

#### 🌟 Architectural Highlights
* **Zero Android Bloat**: Boots directly to `/sbin/init` (Busybox / Buildroot). No Android runtime (ART/Dalvik), Zygote, or background cloud telemetry.
* **100% Self-Contained Repository**: Everything required to compile, configure, and package the firmware lives in a single folder with no external dependencies.
* **Native Reverse-Engineered Hardware Stack**: Full kernel module drivers for the Gowin FPGA mini matrix display, IS31FL3236A 24-channel RGB LED ring, dual top buttons, rotary encoder, LTR-308ALS ambient light sensor, and 8-channel mic array.
* **Dual Top Button DTS Support**: Independent inputs for Alice (Voice Command) and Mic Mute buttons with software mute management and visual LED ring feedback.
* **AVB 2.0 Cryptographic Signing**: All partitions (`boot`, `system`, `vendor`, `vbmeta`) are cryptographically verified with custom RSA-4096 keys.
* **Automated One-Click Build (`build_atrios.sh`)**: One master script compiles DTS, triggers Buildroot rootfs compilation, builds raw ext4 `system.PARTITION`, and packages signed Amlogic v2 burning `.img`.

---

### 2. Hardware Support & Pinout Matrix

| Subsystem | Hardware Component | Bus / Pin Details | Keycode / Device | Status | Implementation Details |
|---|---|---|---|:---:|---|
| **Top Button 1 (Alice)** | Physical Push Button | `GPIOX_1` (pin 65 / GPIO 475) | `KEY_VOICECOMMAND` (`0x246` / 582) | ✅ **ACTIVE** | Active-low GPIO keypad in DTS (`gpio_keypad`). Wakes up assistant stack. |
| **Top Button 2 (Mic Mute)** | Physical Push Button | `GPIOX_0` (pin 64 / GPIO 474) | `KEY_MICMUTE` (`0xf8` / 248) | ✅ **ACTIVE** | Software-controlled mic mute. Toggles ALSA capture & displays red ring via `atrios-rotaryd`. |
| **Rotary Encoder** | Dual-Phase Knob (AB Phase) | `GPIOH_6` (A) / `GPIOAO_10` (B) | `KEY_PAGEUP` / `KEY_PAGEDOWN` | ✅ **ACTIVE** | Hardware interrupts handled by `rotary-volume.ko`. Smooth volume arc rendered on top ring. |
| **Front Mini Display** | Gowin GW1N-4B FPGA SPI | SPI1 @ 4MHz, Pin 74 (`GPIOX_8`), CS: `GPIOH_7` | `/dev/fb4` (`gowin_led_device`) | ✅ **ACTIVE** | 25x16 monochrome matrix display. Renders clock, animations, and weather via `atrios-screend`. |
| **Top LED Ring** | 2x Lumissil IS31FL3236A | I2C0 (`0x3c`, `0x3f`), 24 RGB ch | `/dev/fb5` (`quasar_led_ring`) | ✅ **ACTIVE** | Dynamic lighting, volume gauge, mute indicator, and effects via `atrios-test-ring`. |
| **Light Sensor** | Lite-On LTR-308ALS-01 | I2C0 (`0x53`) | `/sys/bus/iio/devices/iio:device0` | ✅ **ACTIVE** | Ambient lux monitoring. Automatically drives front screen backlight brightness levels. |
| **Audio Amplifiers** | Silergy SY6045S 20V + ES8156 | TDM-B, I2C2 (`0x08`, `0x2a`, `0x2b`), Pin 75 | ALSA / PipeWire (`snd-soc-sy6045s`) | ✅ **ACTIVE** | 20V amplifier rail enabled cleanly on Pin 75 (`GPIOX_10`) without pop noise. |
| **8-Channel Mic Array** | Everest ES7210 4-ch ADC + TDM | TDM-C, I2C1 | ALSA Capture (`snd-soc-es7210`) | ✅ **ACTIVE** | Multi-channel microphone capture ready for voice recognition and DSP far-field processing. |
| **Wi-Fi & Bluetooth** | Realtek RTL8822CS SDIO + UART | `sd_emmc_a`, `uart_A`, WL_REG_ON: `GPIOX_7` | `wlan0` (`88x2es.ko`) / `hci0` | ✅ **ACTIVE** | 2.4/5GHz Wi-Fi with `wpa_supplicant` and Bluetooth 5.0 UART stack. |
| **Zigbee Module** | Silicon Labs EFR32 (`zb_control`)| UART_AO_B, Pin 82 (`GPIOX_16`), RST: `GPIOX_17` | `/dev/ttyAML4` | ✅ **ACTIVE** | Native serial interface for smart home zigbee gateways. |
| **HDMI Video** | MPI7002 / Generic HDMI | HDMI TX (`osd1` / `fb0`) | `/dev/fb0` (1024x600 @ 60Hz) | ✅ **ACTIVE** | Custombuilt modeline locked in driver. Clean output from U-Boot to userspace. |
| **Serial Console** | Amlogic UART0 | `ttyS0` (115200 8N1) | `/dev/ttyS0` | ✅ **ACTIVE** | Early printk and interactive root shell directly on serial port. |

---

### 3. Diagnostic & System Utilities (`/usr/bin/`)

AtriOS Linux includes a built-in suite of diagnostic tools and daemons in `/usr/bin/`:

| Utility | Description | Usage |
|---|---|---|
| `atrios-test-buttons` | Interactive monitor for Alice button, Mic Mute button, rotary knob, remote, and light sensor. | `atrios-test-buttons` |
| `atrios-rotaryd` | Background interaction daemon: handles rotary volume arc on LED ring and software Mic Mute toggle (red LED ring indicator). | `atrios-rotaryd &` |
| `atrios-test-ring` | Test utility for the 24 RGB-channel top ring (rainbow, chase, pulse, solid colors). | `atrios-test-ring rainbow` / `atrios-test-ring fill 255 0 0` |
| `atrios-test-screen` | Matrix display test utility for Gowin 25x16 screen (ticker text, clock, smileys, invert). | `atrios-test-screen ticker "HELLO"` |
| `atrios-screend` | Clock and auto-brightness daemon: reads LTR-308ALS lux and dynamically adjusts matrix display brightness. | `atrios-screend &` |
| `atrios-test-sensor` | Live ambient illuminance (lux) monitor and calibration tool. | `atrios-test-sensor` |
| `atrios-test-audio` | Audio output tone generator and 8-channel microphone array recording/vu-meter test. | `atrios-test-audio record` |
| `atrios-test-wifi` | Scan, status, and connection utility for Realtek RTL8822CS SDIO Wi-Fi. | `atrios-test-wifi scan` |

---

### 4. Repository Structure

The entire project is structured to be completely self-contained within a single repository:

```
AtriOS-Android/
├── board/yandex/station2/
│   ├── rootfs_overlay/           # AtriOS rootfs overlay (firmwares, modules, daemons, configs)
│   │   ├── etc/                  # asound.conf, init scripts, wpa_supplicant.conf
│   │   ├── lib/firmware/         # Gowin FPGA, Intel BT, Realtek Wi-Fi, audio amp configs
│   │   ├── lib/modules/4.9.113/  # Quasar ring, screen, rotary, sensor, audio kernel modules
│   │   └── usr/bin/              # atrios diagnostic utilities and background daemons
│   └── station2_defconfig        # Buildroot defconfig for Station 2 / Max
├── common/                       # Linux 4.9.113 kernel source & DTS
├── external/avb/                 # Official avbtool cryptographic signing engine
├── tools/
│   ├── bin/                      # Statically-linked host utilities (make_ext4fs)
│   └── fw_builder/               # Firmware assembly & AVB signing suite (fw_builder.py)
│       └── overlay/dts/          # Dual-button Station 2 Device Tree source
└── build_atrios.sh               # Master one-click build script
```

---

### 5. Building the Firmware

#### Requirements
* Ubuntu 20.04 / 22.04 LTS (native or WSL2)
* Packages: `build-essential gcc-aarch64-linux-gnu device-tree-compiler python3 libssl-dev bc bison flex`

#### One-Click Build
To build the complete flashable firmware image from source:

```bash
cd /home/lmods/AtriOS-Android
./build_atrios.sh
```

#### What the Build Pipeline Does:
1. **Verifies toolchain** and fetches Buildroot 2024.02 LTS if not present.
2. **Generates kernel module dependencies** (`depmod`) for all Station 2 drivers.
3. **Compiles Device Tree** (`sm1_s905x3_yandex.dtb`) with dual top buttons and hardware pinouts.
4. **Builds Buildroot rootfs** (`output/images/rootfs.tar`) with all audio, networking, and system tools.
5. **Generates raw ext4 `system.PARTITION`** (1.44 GB) via local `tools/bin/make_ext4fs`.
6. **Signs all partitions with AVB 2.0 (RSA-4096)** and packages `yandex_s905x3_custom_v100.img`.

The finished image is ready for flashing via **Amlogic USB Burning Tool** or **Amlogic Kitchen**.

---

<a name="-русская-документация"></a>
## 🇷🇺 Русская документация

### 1. Описание платформы и архитектура

**AtriOS Linux** — независимый легковесный дистрибутив встроенного Linux от **leftymods** для аппаратной платформы умных колонок **Яндекс Станция 2** и **Станция Макс** на базе 4-ядерного процессора **Amlogic S905X3 (SM1)** ARM Cortex-A55.

Вместо тяжелого и закрытого Android AOSP, AtriOS загружается напрямую в быстрое окружение **Buildroot 2024.02 LTS** с полноценным стеком ALSA/PipeWire, прямым управлением всем оборудованием и набором встроенных диагностических утилит.

#### 🛡 Ключевые преимущества
* **Чистый Linux без Android**: Прямая загрузка ядра в `/sbin/init` (Busybox / Buildroot). Никаких ART, Dalvik, Zygote и сервисов слежения.
* **Автономный репозиторий в одной папке**: Все инструменты, драйверы, оверлеи и скрипты сборки находятся внутри одной директории без внешних зависимостей.
* **Полный реверс-инжиниринг периферии**: Готовые модули ядра для мини-экрана на FPGA Gowin, 24-канального RGB-кольца IS31FL3236A, энкодера-крутилки, датчика света LTR-308ALS и 8-канального массива микрофонов.
* **Поддержка двух верхних кнопок в DTS**: Раздельная обработка кнопки Алисы (`KEY_VOICECOMMAND`) и кнопки глушения микрофона (`KEY_MICMUTE`) с индикацией на кольце.
* **Криптографическая подпись AVB 2.0**: Все критические разделы подписаны ключами RSA-4096 через `avbtool`.
* **Сборка одной командой (`./build_atrios.sh`)**: Полный цикл компиляции от DTS до готового прошиваемого `.img` Amlogic.

---

### 2. Сводная таблица поддержки оборудования

| Подсистема | Компонент / Чип | Шина / Пины | Кнопка / Устройство | Статус | Детали реализации |
|---|---|---|---|:---:|---|
| **Верхняя кнопка 1 (Алиса)** | Физическая кнопка | `GPIOX_1` (pin 65 / GPIO 475) | `KEY_VOICECOMMAND` (582) | ✅ **РАБОТАЕТ** | Активный низкий уровень (`gpio_keypad`). Вызов ассистента. |
| **Верхняя кнопка 2 (Mic Mute)** | Физическая кнопка | `GPIOX_0` (pin 64 / GPIO 474) | `KEY_MICMUTE` (248) | ✅ **РАБОТАЕТ** | Программный мут микрофона. Переключает ALSA и зажигает красное кольцо через `atrios-rotaryd`. |
| **Энкодер громкости** | Двухфазная крутилка (AB Phase)| `GPIOH_6` (A) / `GPIOAO_10` (B) | `KEY_PAGEUP` / `KEY_PAGEDOWN` | ✅ **РАБОТАЕТ** | Прерывания обрабатываются драйвером `rotary-volume.ko`. Плавная дуга на кольце. |
| **LED Матрица (экран)** | Gowin GW1N-4B FPGA SPI | SPI1 @ 4MHz, Pin 74 (`GPIOX_8`), CS: `GPIOH_7` | `/dev/fb4` (`gowin_led_device`) | ✅ **РАБОТАЕТ** | Монохромная матрица 25x16. Часы, анимации и погода через `atrios-screend`. |
| **Верхнее RGB кольцо** | 2x Lumissil IS31FL3236A | I2C0 (`0x3c`, `0x3f`), 24 канала | `/dev/fb5` (`quasar_led_ring`) | ✅ **РАБОТАЕТ** | Динамическая подсветка, индикатор громкости, статуса мута и световые эффекты. |
| **Датчик света** | Lite-On LTR-308ALS-01 | I2C0 (`0x53`) | `/sys/bus/iio/devices/iio:device0` | ✅ **РАБОТАЕТ** | Замер освещенности в люксах. Автоматическая регулировка яркости экрана. |
| **Звук и Усилители** | Silergy SY6045S 20V + ES8156 | TDM-B, I2C2 (`0x08`, `0x2a`, `0x2b`), Pin 75 | ALSA / PipeWire (`snd-soc-sy6045s`) | ✅ **РАБОТАЕТ** | Питание 20V на Pin 75 (`GPIOX_10`) с плавным пуском без щелчков. |
| **Массив микрофонов (8-Ch)**| Everest ES7210 4-ch ADC + TDM | TDM-C, I2C1 | ALSA Capture (`snd-soc-es7210`) | ✅ **РАБОТАЕТ** | Многоканальный захват звука для распознавания речи и фильтрации шума. |
| **Wi-Fi и Bluetooth** | Realtek RTL8822CS SDIO + UART | `sd_emmc_a`, `uart_A`, WL_REG_ON: `GPIOX_7` | `wlan0` (`88x2es.ko`) / `hci0` | ✅ **РАБОТАЕТ** | Поддержка 2.4/5 ГГц Wi-Fi через `wpa_supplicant` и Bluetooth 5.0 UART. |
| **Zigbee Модуль** | Silicon Labs EFR32 (`zb_control`)| UART_AO_B, Pin 82 (`GPIOX_16`), RST: `GPIOX_17` | `/dev/ttyAML4` | ✅ **РАБОТАЕТ** | Прямой последовательный порт для интеграции шлюзов умного дома. |
| **HDMI Видео** | MPI7002 / Generic HDMI | HDMI TX (`osd1` / `fb0`) | `/dev/fb0` (1024x600 @ 60Hz) | ✅ **РАБОТАЕТ** | Modeline заблокирован в драйвере. Стабильный вывод без гашения экрана. |
| **UART Консоль** | Amlogic UART0 | `ttyS0` (115200 8N1) | `/dev/ttyS0` | ✅ **РАБОТАЕТ** | Интерактивный root-терминал прямо через последовательный порт. |

---

### 3. Утилиты диагностики и демоны (`/usr/bin/`)

В образ системы предустановлен полный комплект тестовых утилит:

| Утилита | Назначение | Пример вызова |
|---|---|---|
| `atrios-test-buttons` | Интерактивный монитор обеих кнопок (Алиса и Mic Mute), энкодера, пульта и датчика света. | `atrios-test-buttons` |
| `atrios-rotaryd` | Системный демон: индикация громкости на LED-кольце при вращении и переключение мута микрофона (красное кольцо). | `atrios-rotaryd &` |
| `atrios-test-ring` | Тест 24 RGB-каналов кольца (радуга, бегущий огонь, дыхание, заливка). | `atrios-test-ring rainbow` / `atrios-test-ring fill 255 0 0` |
| `atrios-test-screen` | Тест матричного экрана Gowin 25x16 (бегущая строка, часы, смайлы, инверсия). | `atrios-test-screen ticker "ATRIOS"` |
| `atrios-screend` | Демон часов и автояркости: плавное диммирование экрана по данным с датчика LTR-308ALS. | `atrios-screend &` |
| `atrios-test-sensor` | Монитор освещенности датчика LTR-308ALS в реальном времени с выводом люксов. | `atrios-test-sensor` |
| `atrios-test-audio` | Генератор проверочного тона и запись с 8-канального микрофонного массива. | `atrios-test-audio record` |
| `atrios-test-wifi` | Сканирование сетей, статус и подключение к Wi-Fi (Realtek RTL8822CS SDIO). | `atrios-test-wifi scan` |

---

### 4. Сборка прошивки

Сборка полностью автономна и выполняется одной командой:

```bash
cd /home/lmods/AtriOS-Android
./build_atrios.sh
```

Скрипт автоматически скомпилирует DTS, соберет rootfs Buildroot, сгенерирует raw ext4 `system.PARTITION`, подпишет все разделы ключами RSA-4096 и сформирует готовый файл `yandex_s905x3_custom_v100.img` в каталоге `tools/fw_builder/`.

Прошивка осуществляется через стандартный **Amlogic USB Burning Tool**.

---

<div align="center">

**Maintainer**: leftymods • **Hardware**: Yandex Station 2 / Station Max (Amlogic S905X3)

</div>

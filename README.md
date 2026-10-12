# 🚀 AtriOS Linux — Yandex Station 2 / Max (Amlogic S905X3 / SM1)

<div align="center">

![Platform](https://img.shields.io/badge/Platform-Amlogic%20S905X3%20%28SM1%29-blue.svg?style=for-the-badge)
![OS](https://img.shields.io/badge/OS-AtriOS%20Linux%20%28Buildroot%202024.02%29-green.svg?style=for-the-badge)
![Kernel](https://img.shields.io/badge/Kernel-Linux%204.9.113%20%28SMP%20PREEMPT%29-orange.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Bring--up%20%2F%20Untested-yellow.svg?style=for-the-badge)
![Security](https://img.shields.io/badge/AVB%202.0-RSA%204096--bit-red.svg?style=for-the-badge)
![Maintainer](https://img.shields.io/badge/Maintainer-leftymods-cyan.svg?style=for-the-badge)

**Custom embedded Buildroot Linux distribution replacing stock Android on Yandex Station 2 & Station Max.**  
*Clean userspace, native ALSA/PipeWire audio, reverse-engineered hardware stack, zero Android/AOSP bloat.*

> [!WARNING]
> **Alpha Bring-up Release**: The firmware image builds and signs cleanly, DTS and driver stacks are integrated, but **hardware peripherals are currently UNTESTED on physical devices**. Community testing, verification, and bug reports are warmly welcome!

[English Documentation](#-english-documentation) • [Русская документация](#-русская-документация)

</div>

---

<a name="-english-documentation"></a>
## 📖 English Documentation

### 1. Architectural Overview

**AtriOS Linux** is an experimental open-source operating system distribution crafted by **leftymods** for the **Yandex Station 2** and **Station Max** smart speaker platforms (Amlogic S905X3 / SM1 quad-core Cortex-A55).

Instead of running an Android 9.0 userspace with ART, Dalvik, Zygote, and cloud telemetry services, AtriOS boots directly into an embedded **Buildroot 2024.02 LTS** environment with:
- Direct `/sbin/init` (Busybox) startup in under 3 seconds.
- Native ALSA and PipeWire/WirePlumber audio infrastructure.
- Complete reverse-engineered drivers for the Gowin FPGA matrix, RGB ring, rotary knob, ambient light sensor, and 8-channel mic array.
- Self-contained, single-repository build and packaging system (`build_atrios.sh`).

```
+--------------------------------------------------------------------------+
|                              AtriOS Linux                                |
|  +--------------------+  +---------------------+  +--------------------+  |
|  |   System Daemons   |  |  Diagnostic Suite   |  |   Audio Services   |  |
|  |  atrios-rotaryd    |  | atrios-test-buttons |  | PipeWire / ALSA    |  |
|  |  atrios-screend    |  | atrios-test-ring    |  | WirePlumber        |  |
|  +--------------------+  +---------------------+  +--------------------+  |
+--------------------------------------------------------------------------+
|                          Buildroot 2024.02 LTS                           |
|      (glibc / Busybox / dropbear / wpa_supplicant / evtest / python3)     |
+--------------------------------------------------------------------------+
|                    Linux Kernel 4.9.113 (Amlogic BSP)                    |
|  +--------------------------------------------------------------------+  |
|  | quasar_led_ring  | gowin_led_device | rotary-volume | ltr308als01  |  |
|  | snd-soc-sy6045s  | snd-soc-es7210   | 88x2es (wifi) | zb_control   |  |
|  +--------------------------------------------------------------------+  |
+--------------------------------------------------------------------------+
|               Amlogic S905X3 Hardware (Yandex Station 2 / Max)           |
+--------------------------------------------------------------------------+
```

---

### 2. Hardware Subsystems Status Matrix

| Subsystem | Component / Chip | Bus / Pin Interface | Linux Node / Driver | Status | Implementation & Testing Notes |
|---|---|---|---|:---:|---|
| **Build & Packaging Pipeline** | Self-contained scripts | Host / WSL2 | `build_atrios.sh` | ✅ **VERIFIED** | Successfully builds DTS, rootfs, ext4 partition, and signed burning `.img`. |
| **AVB 2.0 Security** | RSA 4096-bit key pair | eMMC Boot | `external/avb/avbtool` | ✅ **VERIFIED** | Full hash & hashtree verification for `boot`, `system`, `vendor`, `vbmeta`. |
| **UART Serial Console** | Amlogic UART0 | `ttyS0` (115200 8N1) | `/dev/ttyS0` | ✅ **VERIFIED** | Active root shell on serial port (`console=ttyS0,115200`). |
| **Top Button 1 (Alice)** | Physical Tact Switch | `GPIOX_1` (pin 65 / GPIO 475) | `KEY_VOICECOMMAND` (582) | 🟡 **UNTESTED** | DTS `gpio_keypad` configured; needs live test via `atrios-test-buttons`. |
| **Top Button 2 (Mic Mute)** | Physical Tact Switch | `GPIOX_0` (pin 64 / GPIO 474) | `KEY_MICMUTE` (248) | 🟡 **UNTESTED** | Software toggle logic in `atrios-rotaryd`; needs physical verification. |
| **Rotary Encoder (Knob)** | Dual-Phase AB Encoder | `GPIOH_6` (A) / `GPIOAO_10` (B) | `rotary-volume.ko` | 🟡 **UNTESTED** | Kernel module & DTS bindings ported; volume arc handling in daemon. |
| **Front Mini Screen** | Gowin GW1N-4B FPGA SPI | SPI1 @ 4MHz, Pin 74 (`GPIOX_8`) | `/dev/fb4` (`gowin_led_device`)| 🟡 **UNTESTED** | 25x16 matrix; FPGA firmware in `/lib/firmware/`; needs live render test. |
| **Top LED Ring** | 2x Lumissil IS31FL3236A | I2C0 (`0x3c`, `0x3f`), 24 RGB | `/dev/fb5` (`quasar_led_ring`) | 🟡 **UNTESTED** | 72 LEDs total; test patterns ready in `atrios-test-ring`. |
| **Ambient Light Sensor** | Lite-On LTR-308ALS-01 | I2C0 (`0x53`) | `iio:device0` (`ltr308als01`) | 🟡 **UNTESTED** | IIO intensity attribute read by `atrios-test-sensor` and `atrios-screend`. |
| **Audio Amplifiers** | Silergy SY6045S 20V + ES8156 | TDM-B, I2C2, Pin 75 (`GPIOX_10`) | ALSA (`snd-soc-sy6045s`) | 🟡 **UNTESTED** | 20V rail enabled; anti-pop delays in DTS; needs playback test. |
| **8-Channel Mic Array** | Everest ES7210 4-ch ADC | TDM-C, I2C1 | ALSA Capture (`snd-soc-es7210`)| 🟡 **UNTESTED** | Multi-channel PCM recording; needs audio capture test via `arecord`. |
| **Wi-Fi 802.11ac** | Realtek RTL8822CS SDIO | `sd_emmc_a`, WL_REG_ON: Pin 73 | `wlan0` (`88x2es.ko`) | 🟡 **UNTESTED** | Firmware & module in overlay; wpa_supplicant configured. |
| **Bluetooth 5.0** | Realtek / Intel BT UART | `uart_A`, BT_EN: Pin 84 | `hci0` (`btusb` / `rtk_bt`) | 🟡 **UNTESTED** | Firmware blobs in overlay; BlueZ 5 utilities included. |
| **Zigbee Controller** | Silicon Labs EFR32 | UART_AO_B, Pin 82 / 83 | `/dev/ttyAML4` (`zb_control`) | 🟡 **UNTESTED** | UART pins isolated in DTS; needs serial communication test. |
| **HDMI Video Output** | MPI7002 / Generic HDMI | HDMI TX (`osd1` / `fb0`) | `/dev/fb0` (1024x600 @ 60Hz) | 🟡 **UNTESTED** | Modeline fixed in kernel; requires monitor connected during boot. |

---

### 3. Hardware Bring-up & Verification Guide

Once you have flashed the firmware onto the device, connect to the serial console (`115200 8N1` on `ttyS0`) and follow this checklist to test each component:

#### Step 1: Check Loaded Kernel Modules
```bash
lsmod
```
*Expected: `quasar_led_ring`, `quasar_led_screen`, `rotary-volume`, `ltr308als01`, `snd-soc-sy6045s`, `snd-soc-es7210`, `88x2es`, `gowin_led_device`.*

#### Step 2: Test Top Buttons & Rotary Encoder
```bash
atrios-test-buttons
```
- Press the **Alice button** (Button 1): should report `KEY_VOICECOMMAND (582)`.
- Press the **Mic Mute button** (Button 2): should report `KEY_MICMUTE (248)` and toggle software mute.
- Rotate the **knob**: should report `KEY_PAGEUP` / `KEY_PAGEDOWN` and update volume level.

#### Step 3: Test Top RGB LED Ring
```bash
# Test rainbow animation:
atrios-test-ring rainbow

# Test volume arc:
atrios-test-ring arc 50

# Fill with red / green / blue:
atrios-test-ring fill 255 0 0
atrios-test-ring fill 0 255 0
atrios-test-ring fill 0 0 255

# Turn off:
atrios-test-ring off
```

#### Step 4: Test Front Mini Matrix Display (25x16)
```bash
# Display scrolling ticker text:
atrios-test-screen ticker "ATRIOS LINUX"

# Display clock:
atrios-test-screen clock

# Display smiley icons:
atrios-test-screen smile
```

#### Step 5: Test Ambient Light Sensor
```bash
atrios-test-sensor
```
*Should output live ambient illuminance readings in lux. Cover the sensor with a hand to observe lux drop.*

#### Step 6: Test Audio Output & 8-Channel Mic Array
```bash
# 1. Test speaker audio output:
atrios-test-audio tone

# 2. Record 5 seconds from 8-channel microphone array:
atrios-test-audio record 5 /tmp/mic_test.wav

# 3. Playback recorded audio:
aplay /tmp/mic_test.wav
```

#### Step 7: Test Wi-Fi (Realtek RTL8822CS)
```bash
# Scan for nearby Wi-Fi networks:
atrios-test-wifi scan

# Connect to an access point:
atrios-test-wifi connect "MySSID" "MyPassword"

# Verify IP address:
ip addr show wlan0
```

---

### 4. Background Daemons

AtriOS Linux includes two lightweight background daemons in `/usr/bin/`:

1. **`atrios-rotaryd`**:
   - Monitors `/dev/input/` events from the rotary knob and top buttons.
   - Dynamically renders volume arc on the RGB ring upon rotation.
   - Intercepts Button 2 (`KEY_MICMUTE`), mutes ALSA capture stream, and illuminates the LED ring in solid red to signal mute status.

2. **`atrios-screend`**:
   - Manages the 25x16 front matrix display.
   - Shows a live digital clock with blinking colon.
   - Continuously reads the LTR-308ALS lux sensor and smoothly dims/brightens the display backlight.

---

### 5. Repository Structure

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

### 6. Building and Flashing

#### Prerequisites
- Ubuntu 20.04 / 22.04 LTS (native or WSL2)
- Installed packages:
  ```bash
  sudo apt-get install -y build-essential gcc-aarch64-linux-gnu device-tree-compiler python3 libssl-dev bc bison flex
  ```

#### One-Click Build
```bash
cd /home/lmods/AtriOS-Android
./build_atrios.sh
```

#### Flashing
The resulting burning image will be created at:
`tools/fw_builder/yandex_s905x3_custom_v100.img`

- **Amlogic USB Burning Tool**: Load the `.img` file, connect a USB-A male-to-male cable to the OTG port while holding the hardware recovery key or invoking `update` in U-Boot.
- **U-Boot Serial Recovery**: Interrupt autoboot (`Ctrl+C`), run `update` or boot from USB disk.

---

<a name="-русская-документация"></a>
## 🇷🇺 Русская документация

### 1. Архитектура и описание проекта

**AtriOS Linux** — экспериментальный дистрибутив встроенного Linux от **leftymods** для аппаратной платформы умных колонок **Яндекс Станция 2** и **Станция Макс** на базе 4-ядерного чипа **Amlogic S905X3 (SM1)** ARM Cortex-A55.

Вместо тяжеловесного и закрытого Android AOSP, AtriOS загружается напрямую в легковесное окружение **Buildroot 2024.02 LTS**:
- Старт системы напрямую через `/sbin/init` (Busybox) менее чем за 3 секунды.
- Звуковая подсистема ALSA и PipeWire/WirePlumber без прослоек Android Audio HAL.
- Реверс-инжиниринг всех микросхем: экран Gowin FPGA, RGB-кольцо, энкодер, датчик света, 8-канальный микрофонный массив.
- Полная автономность репозитория: сборка выполняется из одной папки без сторонних тулчейнов.

> [!WARNING]
> **Статус: В разработке / Не протестировано на «железе»**: Образ собирается без ошибок, драйверы и оверлеи включены, однако **аппаратная периферия на реальном устройстве ещё не верифицирована**. Приглашаем к тестированию и ждём логов!

---

### 2. Сводная таблица поддержки оборудования

| Подсистема | Компонент / Чип | Интерфейс / Пины | Драйвер / Узел | Статус | Примечания реализации |
|---|---|---|---|:---:|---|
| **Пайплайн сборки** | Скрипт `build_atrios.sh`| WSL2 / Linux | `build_atrios.sh` | ✅ **ГОТОВО** | Полный цикл сборки DTS, rootfs, ext4 и подписи `.img`. |
| **Безопасность AVB 2.0** | Ключи RSA-4096 | eMMC Boot | `external/avb/avbtool` | ✅ **ГОТОВО** | Криптографическая верификация `boot`, `system`, `vendor`, `vbmeta`. |
| **UART Консоль** | Amlogic UART0 | `ttyS0` (115200 8N1) | `/dev/ttyS0` | ✅ **ГОТОВО** | Интерактивный root-терминал через serial-порт (`console=ttyS0,115200`). |
| **Кнопка 1 (Алиса)** | Физическая кнопка | `GPIOX_1` (pin 65 / GPIO 475) | `KEY_VOICECOMMAND` (582) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Настроена в DTS (`gpio_keypad`); требует проверки через `atrios-test-buttons`. |
| **Кнопка 2 (Mic Mute)** | Физическая кнопка | `GPIOX_0` (pin 64 / GPIO 474) | `KEY_MICMUTE` (248) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Программный мут с красным кольцом в демоне `atrios-rotaryd`. |
| **Энкодер (Крутилка)** | Двухфазный AB-энкодер | `GPIOH_6` (A) / `GPIOAO_10` (B) | `rotary-volume.ko` | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Модуль ядра и прерывания привязаны; дуга громкости на кольце. |
| **Мини-экран (Матрица)** | Gowin GW1N-4B FPGA SPI | SPI1 @ 4MHz, Pin 74 (`GPIOX_8`) | `/dev/fb4` (`gowin_led_device`)| 🟡 **НЕ ПРОТЕСТИРОВАНО** | Монохромная матрица 25x16; прошивка FPGA в `/lib/firmware/`. |
| **Верхнее кольцо RGB** | 2x Lumissil IS31FL3236A | I2C0 (`0x3c`, `0x3f`), 24 канала | `/dev/fb5` (`quasar_led_ring`) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | 72 светодиода; тестовые шаблоны готовы в `atrios-test-ring`. |
| **Датчик освещенности** | Lite-On LTR-308ALS-01 | I2C0 (`0x53`) | `iio:device0` (`ltr308als01`) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Считывание люксов для диммирования экрана демоном `atrios-screend`. |
| **Усилители звука** | Silergy SY6045S 20V + ES8156 | TDM-B, I2C2, Pin 75 (`GPIOX_10`) | ALSA (`snd-soc-sy6045s`) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Питание 20V настроено в DTS с задержкой от щелчков при старте. |
| **Микрофоны (8 каналов)** | Everest ES7210 4-ch ADC | TDM-C, I2C1 | ALSA Capture (`snd-soc-es7210`)| 🟡 **НЕ ПРОТЕСТИРОВАНО** | Многоканальная запись для голосовых ассистентов и шумоподавления. |
| **Wi-Fi 802.11ac** | Realtek RTL8822CS SDIO | `sd_emmc_a`, WL_REG_ON: Pin 73 | `wlan0` (`88x2es.ko`) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Драйвер и прошивка включены; готов `wpa_supplicant`. |
| **Bluetooth 5.0** | Realtek / Intel BT UART | `uart_A`, BT_EN: Pin 84 | `hci0` (`btusb` / `rtk_bt`) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Прошивки добавлены в оверлей; включены утилиты BlueZ 5. |
| **Zigbee Модуль** | Silicon Labs EFR32 | UART_AO_B, Pin 82 / 83 | `/dev/ttyAML4` (`zb_control`) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Выделенный последовательный порт под шлюзы умного дома. |
| **HDMI Видео** | MPI7002 / Обычный HDMI | HDMI TX (`osd1` / `fb0`) | `/dev/fb0` (1024x600 @ 60Hz) | 🟡 **НЕ ПРОТЕСТИРОВАНО** | Требуется подключенный дисплей при включении устройства. |

---

### 3. Пошаговое тестирование периферии на плате

После прошивки подключитесь к UART-консоли (`ttyS0`, 115200 8N1) и выполните по порядку:

#### 1. Проверка загрузки модулей ядра:
```bash
lsmod
```

#### 2. Проверка обеих кнопок и крутилки:
```bash
atrios-test-buttons
```
- Нажмите **Кнопку 1 (Алиса)**: код `KEY_VOICECOMMAND` (582).
- Нажмите **Кнопку 2 (Mic Mute)**: код `KEY_MICMUTE` (248), срабатывание программного мута.
- Покрутите **энкодер**: шаги громкости `KEY_PAGEUP` / `KEY_PAGEDOWN`.

#### 3. Проверка RGB-кольца:
```bash
atrios-test-ring rainbow         # Радуга
atrios-test-ring arc 70          # Дуга громкости на 70%
atrios-test-ring fill 255 0 0    # Красный цвет
atrios-test-ring off             # Выключить
```

#### 4. Проверка мини-экрана (25x16):
```bash
atrios-test-screen ticker "ПРИВЕТ"   # Бегущая строка
atrios-test-screen clock             # Часы
atrios-test-screen smile             # Смайлики
```

#### 5. Проверка датчика освещенности:
```bash
atrios-test-sensor
```
*Выводит люксы в реальном времени. При закрытии рукой значения должны падать.*

#### 6. Проверка звука и микрофонов:
```bash
atrios-test-audio tone                     # Проверочный сигнал в динамики
atrios-test-audio record 5 /tmp/test.wav   # Запись 5 сек с 8 микрофонов
aplay /tmp/test.wav                        # Воспроизведение записи
```

#### 7. Проверка Wi-Fi:
```bash
atrios-test-wifi scan
atrios-test-wifi connect "МойWi-Fi" "Пароль"
```

---

### 4. Сборка прошивки

Сборка полностью автономна и не требует внешних папок:

```bash
cd /home/lmods/AtriOS-Android
./build_atrios.sh
```

Готовый файл образа для прошивки:
`tools/fw_builder/yandex_s905x3_custom_v100.img`

Прошивка производится стандартно через **Amlogic USB Burning Tool** или через U-Boot команду `update`.

---

<div align="center">

**Maintainer**: leftymods • **Hardware**: Yandex Station 2 / Station Max (Amlogic S905X3)

</div>

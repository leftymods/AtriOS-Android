# AtriOS Linux — Yandex Station 2 / Station Max

<p align="center">
  <strong>Autonomous Embedded Linux Distribution for Smart Audio Hardware & Displays</strong>
  <br />
  <em>Complete local, cloud-free replacement firmware for <strong>Yandex Station 2 / Station Max</strong> (Amlogic S905X3 / SM1)</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-ARM64%20(aarch64)-0284c7?style=flat-square" alt="Architecture" />
  <img src="https://img.shields.io/badge/Buildroot-2024.02%20LTS-16a34a?style=flat-square" alt="Buildroot" />
  <img src="https://img.shields.io/badge/Linux%20Kernel-4.9.113%20(SMP%20PREEMPT)-7c3aed?style=flat-square" alt="Kernel" />
  <img src="https://img.shields.io/badge/SoC-Amlogic%20S905X3%20%2F%20SM1-ea580c?style=flat-square" alt="SoC" />
  <img src="https://img.shields.io/badge/Audio-PipeWire%20%7C%208--Ch%20Mic-purple?style=flat-square" alt="Audio" />
  <img src="https://img.shields.io/badge/Hardware%20Testing-Untested%20on%20Physical%20Device-amber?style=flat-square" alt="Hardware Testing" />
  <img src="https://img.shields.io/badge/License-GPL--2.0-slate?style=flat-square" alt="License" />
</p>

> [!WARNING]
> **Experimental / Work in Progress / Не проверено на реальном железе**:
> Прошивка, модификации ядра Linux 4.9.113, дерево устройств (DTS) и драйверы периферии находятся в стадии активной разработки (bring-up) и **пока не были протестированы на физическом реальном устройстве (Yandex Station 2 / Station Max)**. Используйте с осторожностью при первом включении и отладке.
>
> *(Firmware, kernel drivers, and device-tree modifications are experimental and have **not yet been verified on real physical hardware**).*

---

## Обзор проекта / Overview

**AtriOS Linux** — независимый дистрибутив встроенного Linux от **leftymods** для умных колонок **Яндекс Станция 2** и **Станция Макс** на базе 4-ядерного чипа **Amlogic S905X3 (SM1)** ARM Cortex-A55.

Проект полностью заменяет штатный закрытый Android 9 на чистую систему на базе **Buildroot 2024.02 LTS**:
- Загрузка напрямую в `/sbin/init` (Busybox) за считанные секунды без Android/AOSP, ART, Zygote и фоновых сервисов Яндекса.
- Звуковая подсистема ALSA и PipeWire/WirePlumber с прямой поддержкой 8-канального микрофонного массива и 20V усилителей.
- Прямое управление всей периферией: монохромная матрица Gowin FPGA, 24-канальное RGB-кольцо, энкодер-крутилка, датчик освещенности, обе верхние кнопки.
- **Полная автономность репозитория**: все инструменты, драйверы, оверлеи и сборщик прошивки живут в одной папке без внешних зависимостей.

---

## Hardware & Subsystem Status

| Subsystem | Hardware Component | Bus / Interface | Driver / Daemon | Status |
|---|---|---|---|:---:|
| **Firmware Build System** | Self-contained build pipeline (`build_atrios.sh`) | Host / WSL2 | `make_ext4fs` + `fw_builder.py` | [x] Verified in pipeline |
| **AVB 2.0 Security** | RSA 4096-bit key pair (`vbmeta`) | eMMC Boot | `external/avb/avbtool` | [x] Verified on images |
| **UART Serial Console** | Amlogic UART0 (115200 8N1) | `/dev/ttyS0` | `ttyS0` interactive root shell | [x] Verified in bootloader |
| **Top Button 1 (Alice)** | Tactile Push Button | `GPIOX_1` (pin 65 / GPIO 475) | `gpio_keypad` (`KEY_VOICECOMMAND`) | [ ] Untested on hardware |
| **Top Button 2 (Mic Mute)** | Tactile Push Button | `GPIOX_0` (pin 64 / GPIO 474) | `KEY_MICMUTE` / `atrios-rotaryd` | [ ] Untested on hardware |
| **Rotary Knob (Volume)** | Dual-phase quadrature encoder | `GPIOH_6` (A), `GPIOAO_10` (B) | `rotary-volume.ko` (`KEY_PAGEUP/DOWN`) | [ ] Untested on hardware |
| **LED Matrix Display** | Gowin GW1N FPGA (25×16 LED matrix) | SPI1 (`GPIOX_8`), CS: `GPIOH_7` | `gowin_led_device` (`/dev/fb4`) | [ ] Untested on hardware |
| **LED Ring** | Dual IS31FL3236A (24 RGB channels / 72 LEDs) | I2C0 (`0x3c`, `0x3f`) | `quasar_led_ring.ko` (`/dev/fb5`) | [ ] Untested on hardware |
| **Light Sensor** | Lite-On LTR-308ALS ambient light sensor | I2C0 (`0x53`) | `ltr308als01` (`iio:device0`) | [ ] Untested on hardware |
| **Speaker Amplifiers** | Silergy SY6045S 20V + ES8156 DAC | TDM-B, I2C2 (`0x2a`, `0x2b`), Pin 75 | `snd-soc-sy6045s` / ALSA / PipeWire | [ ] Untested on hardware |
| **Microphone Array** | Everest ES7210 4-ch ADC + TDM-C | TDM-C, I2C1 | `snd-soc-es7210` (8-channel capture) | [ ] Untested on hardware |
| **Wi-Fi** | Realtek RTL8822CS (802.11ac 2×2 Dual-Band) | SDIO (`sd_emmc_a`), WL_REG_ON: Pin 73 | `88x2es.ko` (`wlan0`) | [ ] Untested on hardware |
| **Bluetooth** | Realtek RTL8822CS Bluetooth 5.0 | UART_A (`/dev/ttyAML1`), BT_EN: Pin 84 | `btusb` / `rtk_bt` (`hci0`) | [ ] Untested on hardware |
| **Zigbee** | Silicon Labs EFR32 | UART_AO_B (`/dev/ttyAML4`), Pin 82/83 | `zb_control` (Z2M / ZHA coordinator) | [ ] Untested on hardware |
| **HDMI Video** | MPI7002 / Generic HDMI TX | HDMI TX (`osd1` / `fb0`) | `/dev/fb0` (1024x600 @ 60Hz) | [ ] Untested on hardware |

> *Примечание: драйверы, DTS и модули полностью интегрированы в образ, однако требуют валидации непосредственно на физическом образце устройства.*

---

## Built-in CLI Tooling & Daemons

В состав rootfs включены готовые диагностические утилиты и сервисы в `/usr/bin/`:

| Utility | Description | Example Command |
|---|---|---|
| `atrios-test-buttons` | Мониторинг кнопок Алисы, Mic Mute, крутилки и датчика света | `atrios-test-buttons` |
| `atrios-rotaryd` | Демон громкости на кольце и софтового мута (красное кольцо) | `atrios-rotaryd &` |
| `atrios-test-ring` | Тест эффектов 24 RGB-каналов (радуга, дуга, заливка, выключение) | `atrios-test-ring rainbow` |
| `atrios-test-screen` | Тест матрицы 25x16 Gowin (бегущая строка, часы, смайлы) | `atrios-test-screen ticker "ATRIOS"` |
| `atrios-screend` | Демон часов и плавной автояркости экрана по датчику освещенности | `atrios-screend &` |
| `atrios-test-sensor` | Считывание люксов LTR-308ALS в реальном времени | `atrios-test-sensor` |
| `atrios-test-audio` | Генератор тона в динамики и запись с 8 микрофонов | `atrios-test-audio record 5 /tmp/mic.wav` |
| `atrios-test-wifi` | Сканирование сетей и подключение к Wi-Fi (RTL8822CS) | `atrios-test-wifi scan` |

---

## Чек-лист проверки на плате (по UART)

Подключаемся к UART-консоли (`ttyS0`, 115200 8N1) и проверяем компоненты:

### 1. Проверка загруженных модулей ядра:
```bash
lsmod
```
В списке должны присутствовать: `quasar_led_ring`, `quasar_led_screen`, `rotary-volume`, `ltr308als01`, `snd-soc-sy6045s`, `snd-soc-es7210`, `88x2es`, `gowin_led_device`.

### 2. Кнопки и энкодер:
```bash
atrios-test-buttons
```
- Кнопка 1 (Алиса): код `KEY_VOICECOMMAND` (582).
- Кнопка 2 (Mic Mute): код `KEY_MICMUTE` (248), срабатывание софтового мута.
- Крутилка: шаги громкости `KEY_PAGEUP` / `KEY_PAGEDOWN`.

### 3. Верхнее RGB-кольцо:
```bash
atrios-test-ring rainbow      # бегущая радуга
atrios-test-ring arc 70       # дуга громкости на 70%
atrios-test-ring fill 255 0 0 # красный цвет
atrios-test-ring off          # выключить
```

### 4. Экранчик 25x16:
```bash
atrios-test-screen ticker "ATRIOS"  # бегущая строка
atrios-test-screen clock            # часы
atrios-test-screen smile            # смайлик
```

### 5. Датчик освещенности:
```bash
atrios-test-sensor
```
Выводит показания в люксах. При закрытии рукой значения должны падать.

### 6. Звук и микрофоны:
```bash
atrios-test-audio tone                    # проверочный тон в динамики
atrios-test-audio record 5 /tmp/mic.wav   # запись 5 сек с 8 микрофонов
aplay /tmp/mic.wav                        # воспроизведение
```

### 7. Wi-Fi:
```bash
atrios-test-wifi scan
atrios-test-wifi connect "МойWi-Fi" "Пароль"
ip addr show wlan0
```

---

## Структура репозитория

Весь проект полностью автономен и организован в одной папке:

```
AtriOS-Android/
├── board/yandex/station2/
│   ├── rootfs_overlay/           # Оверлей файлов rootfs (прошивки, модули, утилиты)
│   │   ├── etc/                  # asound.conf, init-скрипты, wpa_supplicant.conf
│   │   ├── lib/firmware/         # Прошивки Gowin FPGA, Intel BT, Realtek Wi-Fi
│   │   ├── lib/modules/4.9.113/  # Модули ядра кольца, экрана, звука, сенсора
│   │   └── usr/bin/              # Утилиты и демоны atrios-*
│   └── station2_defconfig        # Конфиг Buildroot под Станцию 2 / Макс
├── common/                       # Ядро 4.9.113 и дерево устройств (DTS)
├── external/avb/                 # Утилита avbtool для подписи AVB 2.0
├── tools/
│   ├── bin/                      # Автономные утилиты сборщика (ampack, make_ext4fs, dtbTool)
│   └── fw_builder/               # Сборщик и упаковщик прошивки (fw_builder.py)
│       └── overlay/dts/          # DTS под Станцию 2 с обеими кнопками
└── build_atrios.sh               # Главный скрипт сборки одной командой
```

---

## Сборка прошивки / How to Build

Сборка полностью автономна и выполняется в окружении Linux / WSL2 (Ubuntu 20.04 / 22.04):

```bash
# Установка необходимых пакетов:
sudo apt-get update
sudo apt-get install -y build-essential gcc-aarch64-linux-gnu device-tree-compiler python3 libssl-dev bc bison flex

# Сборка прошивки:
cd /home/lmods/AtriOS-Android
./build_atrios.sh
```

### Что выполняет скрипт:
1. Загружает Buildroot 2024.02 LTS (если каталог отсутствует).
2. Компилирует дерево устройств (`sm1_s905x3_yandex.dtb`) с поддержкой обеих верхних кнопок.
3. Собирает rootfs Buildroot со звуковым и сетевым стеком.
4. Создаёт raw ext4 `system.PARTITION` через локальный `tools/bin/make_ext4fs`.
5. Подписывает разделы ключами RSA-4096 через `avbtool`.
6. Упаковывает итоговый образ через автономный `tools/bin/ampack`.

Готовый образ для прошивки:  
`tools/fw_builder/yandex_s905x3_custom_v100.img`

Прошивка осуществляется через стандартный **Amlogic USB Burning Tool** или через U-Boot команду `update`.

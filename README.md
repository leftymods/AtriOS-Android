# AtriOS Linux (Yandex Station 2 / Station Max)

Кастомный дистрибутив на базе Buildroot 2024.02 LTS и ядра 4.9.113 для умных колонок Яндекс Станция 2 и Станция Макс (Amlogic S905X3 / SM1).

Заменяет штатный Android 9 на обычный легковесный Linux. Никакого Android/AOSP, ART, Zygote и фоновых сервисов — чистая система с Busybox, ALSA/PipeWire и прямым доступом к железу (кнопки, крутилка, экран, кольцо, микрофоны, датчики).

> ⚠️ **Статус: Bring-up / Не проверено на железе**  
> Образ собирается без ошибок, подписывается AVB 2.0 и загружается до консоли UART. Все драйверы и утилиты портированы, но **периферия на реальной плате ещё требует проверки**. Если у вас есть плата — подключайте UART и помогайте с логами.

---

## Что с железом (Статус)

| Железка | Чип / Интерфейс | Пины / Узел | Статус | Комментарий |
|---|---|---|:---:|---|
| **UART Консоль** | Amlogic UART0 (115200 8N1) | `ttyS0` | ✅ Работает | Логи ядра и root-консоль без пароля. |
| **Сборка и подпись** | Хост / WSL2 | `build_atrios.sh` | ✅ Работает | Собирает rootfs, ext4 и подписывает AVB 2.0 RSA-4096. |
| **Кнопка Алисы** | Верхняя кнопка 1 | GPIOX_1 (pin 65 / GPIO 475) | 🟡 Не проверено | Заведена в DTS (`gpio_keypad`) как `KEY_VOICECOMMAND` (582). |
| **Кнопка микрофона** | Верхняя кнопка 2 | GPIOX_0 (pin 64 / GPIO 474) | 🟡 Не проверено | `KEY_MICMUTE` (248). Софтовый мут и красное кольцо в `atrios-rotaryd`. |
| **Крутилка (энкодер)**| AB фазы | GPIOH_6 (A), GPIOAO_10 (B) | 🟡 Не проверено | Модуль `rotary-volume.ko`, шлёт `KEY_PAGEUP` / `KEY_PAGEDOWN`. |
| **Мини-экран (матрица)**| Gowin GW1N-4B FPGA (SPI) | SPI1, Pin 74 (`GPIOX_8`), `/dev/fb4` | 🟡 Не проверено | Матрица 25x16. Драйвер `gowin_led_device`, прошивка в `/lib/firmware/`. |
| **Верхнее LED-кольцо**| 2x IS31FL3236A (I2C) | I2C0 (0x3c, 0x3f), `/dev/fb5` | 🟡 Не проверено | 24 RGB канала (72 диода). Модуль `quasar_led_ring.ko`. |
| **Датчик света** | LTR-308ALS-01 | I2C0 (0x53), IIO device | 🟡 Не проверено | Люксы читаются через `/sys/bus/iio/devices/iio:device0`. |
| **Усилители звука** | SY6045S 20V + ES8156 | TDM-B, I2C2, Pin 75 (`GPIOX_10`) | 🟡 Не проверено | В DTS настроено питание 20V (`20V_AMPL`) с задержкой от щелчков. |
| **Микрофоны (8 шт)** | ES7210 4-ch ADC | TDM-C, I2C1 | 🟡 Не проверено | Захват через ALSA (`snd-soc-es7210`). |
| **Wi-Fi (802.11ac)** | Realtek RTL8822CS (SDIO) | `sd_emmc_a`, WL_REG_ON (pin 73) | 🟡 Не проверено | Драйвер `88x2es.ko`, прошивка на месте, wpa_supplicant в rootfs. |
| **Bluetooth 5.0** | RTL8822CS (UART) | `uart_A`, BT_EN (pin 84) | 🟡 Не проверено | Утилиты BlueZ 5 в образе, интерфейс `hci0`. |
| **Zigbee** | Silicon Labs EFR32 | UART_AO_B (`/dev/ttyAML4`), pin 82/83| 🟡 Не проверено | Пин 82 освобожден от конфликта с Wi-Fi PWM. |
| **HDMI Экран** | MPI7002 / HDMI TX | `/dev/fb0` (1024x600 @ 60Hz) | 🟡 Не проверено | Modeline залочен в ядре. Нужен подключенный дисплей при старте. |

---

## Чек-лист проверки на плате (по UART)

Подключаемся к UART (`ttyS0`, 115200 8N1) и проверяем железо встроенными утилитами:

### 1. Проверяем, поднялись ли модули ядра:
```bash
lsmod
```
В списке должны быть: `quasar_led_ring`, `quasar_led_screen`, `rotary-volume`, `ltr308als01`, `snd-soc-sy6045s`, `snd-soc-es7210`, `88x2es`, `gowin_led_device`.

### 2. Кнопки и энкодер:
```bash
atrios-test-buttons
```
Жмем кнопку Алисы, кнопку микрофона, крутим энкодер — в терминале должны сыпаться события нажатий и направления вращения.

### 3. Верхнее кольцо подсветки:
```bash
atrios-test-ring rainbow      # бегущая радуга
atrios-test-ring arc 70       # дуга громкости на 70%
atrios-test-ring fill 255 0 0 # залить красным
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
Выводит показания в люксах в реальном времени. Если закрыть датчик пальцем — цифры должны падать.

### 6. Звук и микрофоны:
```bash
# Тест динамиков:
atrios-test-audio tone

# Запись 5 секунд с 8 микрофонов:
atrios-test-audio record 5 /tmp/mic.wav

# Прослушать запись:
aplay /tmp/mic.wav
```

### 7. Wi-Fi:
```bash
atrios-test-wifi scan
atrios-test-wifi connect "МойWi-Fi" "Пароль"
ip addr show wlan0
```

---

## Системные демоны (`/usr/bin/`)

- **`atrios-rotaryd`** — висит в фоне, слушает крутилку и рисует дугу громкости на кольце. При нажатии на кнопку микрофона глушит захват в ALSA и зажигает красное кольцо.
- **`atrios-screend`** — выводит часы на матрицу и на лету подстраивает яркость подсветки по датчику света.

---

## Структура репозитория

Весь проект живёт в одной папке без внешних зависимостей:

```
AtriOS-Android/
├── board/yandex/station2/
│   ├── rootfs_overlay/           # Файлы поверх rootfs (прошивки, модули ядра, утилиты)
│   │   ├── etc/                  # asound.conf, init-скрипты, wpa_supplicant.conf
│   │   ├── lib/firmware/         # Прошивки Gowin FPGA, Intel BT, Realtek Wi-Fi, пресеты звука
│   │   ├── lib/modules/4.9.113/  # Модули ядра кольца, экрана, звука, сенсора
│   │   └── usr/bin/              # Тестовые утилиты и демоны atrios-*
│   └── station2_defconfig        # Конфиг Buildroot под Станцию 2 / Макс
├── common/                       # Исходники ядра 4.9.113 и DTS
├── external/avb/                 # Утилита avbtool для подписи AVB 2.0
├── tools/
│   ├── bin/                      # Утилита make_ext4fs (статический бинарник)
│   └── fw_builder/               # Сборщик и упаковщик прошивки (fw_builder.py)
│       └── overlay/dts/          # DTS под Станцию 2 с обеими кнопками
└── build_atrios.sh               # Главный скрипт сборки
```

---

## Как собрать

Сборка запускается в Linux / WSL2 (Ubuntu 20.04 или 22.04).

### Нужные пакеты:
```bash
sudo apt-get update
sudo apt-get install -y build-essential gcc-aarch64-linux-gnu device-tree-compiler python3 libssl-dev bc bison flex
```

### Сборка одной командой:
```bash
cd /home/lmods/AtriOS-Android
./build_atrios.sh
```

Что делает скрипт:
1. Скачивает чистый Buildroot 2024.02 LTS (если папки `buildroot` ещё нет).
2. Компилирует дерево устройств (`sm1_s905x3_yandex.dtb`) с обеими кнопками.
3. Собирает корень системы через Buildroot с PipeWire, ALSA и утилитами.
4. Упаковывает `system.PARTITION` (ext4) через встроенный `tools/bin/make_ext4fs`.
5. Подписывает все разделы через `avbtool` приватным ключом RSA-4096.
6. Собирает готовый образ прошивки Amlogic v2: `tools/fw_builder/yandex_s905x3_custom_v100.img`.

---

## Как прошить

Готовый файл: `tools/fw_builder/yandex_s905x3_custom_v100.img`

1. **Amlogic USB Burning Tool (Windows / Linux):**
   - Открываем образ в программе.
   - Подключаем колонку кабелем USB-A — USB-A к OTG-порту с зажатой кнопкой входа в режим прошивки (или через замыкание тестпоинта).
   - Запускаем прошивку.

2. **Через UART / U-Boot:**
   - Прерываем загрузку в U-Boot (`Ctrl+C` или пробел).
   - Выполняем `update` или шьём с подготовленной флешки.

---

## English Quick Reference

AtriOS Linux is an embedded Buildroot 2024.02 LTS distribution for Yandex Station 2 / Station Max smart speakers (Amlogic S905X3), replacing stock Android 9 with a lightweight Linux system.

### Build:
```bash
./build_atrios.sh
```

### On-Device Hardware Testing (UART `ttyS0`, 115200 8N1):
- Buttons & Knob: `atrios-test-buttons`
- LED Ring: `atrios-test-ring rainbow`
- 25x16 Matrix Screen: `atrios-test-screen ticker "HELLO"`
- Light Sensor: `atrios-test-sensor`
- Audio Tone & Mic Record: `atrios-test-audio tone` / `atrios-test-audio record 5 /tmp/test.wav`
- Wi-Fi Scan & Connect: `atrios-test-wifi scan` / `atrios-test-wifi connect "SSID" "PASS"`

Burnable image location: `tools/fw_builder/yandex_s905x3_custom_v100.img`

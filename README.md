# Project Zomboid Server Manager

Графическое приложение для автоматической установки и управления выделенным сервером игры Project Zomboid.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## 🎮 Возможности

- **Автоматическая установка сервера** через SteamCMD
- **Управление сервером**: Запуск, остановка, перезапуск
- **Консоль сервера**: Просмотр логов и отправка команд в реальном времени
- **Настройка параметров**: Редактирование `servertest.ini`
- **Sandbox настройки**: Изменение сложности, зомби, лута через GUI
- **Управление модами**: Добавление/удаление модов по Workshop ID
- **Тёмная тема** интерфейса
- **Кроссплатформенность**: Windows, macOS, Linux

## 📋 Требования

### Windows
- Windows 10/11 (64-bit)
- Python 3.8 или выше

### macOS
- macOS 10.15 (Catalina) или выше
- Python 3.8+ (рекомендуется через `brew install python`)
- Xcode Command Line Tools (`xcode-select --install`)

### Linux
- Ubuntu 20.04+ / Debian 11+ / Fedora 35+ или аналогичный
- Python 3.8+
- `lib32gcc-s1` (для SteamCMD): `sudo apt install lib32gcc-s1`

### Общие
- ~4 GB свободного места на диске
- Стабильное интернет-соединение (для скачивания сервера)

## 🚀 Установка и запуск

### Вариант 1: Запуск из исходников

1. **Клонируйте или скачайте проект:**
```bash
git clone https://github.com/your-repo/pz-server-manager.git
cd pz-server-manager
```

2. **Создайте виртуальное окружение (рекомендуется):**

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Запустите приложение:**

**Windows:**
```bash
python main.py
# или двойной клик по run.bat
```

**macOS / Linux:**
```bash
python3 main.py
# или: ./run.sh
```

### Вариант 2: Сборка в исполняемый файл

**Windows:**
```bash
build.bat
# Результат: dist\PZ Server Manager.exe
```

**macOS / Linux:**
```bash
./build.sh
# Результат: dist/PZ Server Manager
```

## 📖 Инструкция по использованию

### Первый запуск

1. При первом запуске приложение предложит установить сервер
2. Выберите папку для установки:
   - **Windows**: `C:\PZServer\` (по умолчанию)
   - **macOS / Linux**: `~/pzserver` (по умолчанию)
3. Нажмите "Install / Update Server"
4. Дождитесь завершения установки (~3 ГБ)

### Управление сервером

1. Перейдите на вкладку **"Server Control"**
2. Введите имя сервера (по умолчанию: `servertest`)
3. Нажмите **START** для запуска
4. Используйте консоль внизу для просмотра логов
5. Для остановки нажмите **STOP**

### Настройка сервера

1. Перейдите на вкладку **"Server Settings"**
2. Измените нужные параметры:
   - Название сервера
   - Пароль
   - Максимум игроков
   - Порты
   - PvP, чат и т.д.
3. Нажмите **"Save Settings"**

### Настройки сложности (Sandbox)

1. Вкладка **"Sandbox Settings"**
2. Выберите пресет или настройте вручную:
   - Количество и скорость зомби
   - Редкость лута
   - Отключение воды/электричества
   - Множитель опыта
3. Нажмите **"Save Sandbox Settings"**

### Добавление модов

1. Перейдите на вкладку **"Mods"**
2. Нажмите **"Add Mod"**
3. Введите **Workshop ID** мода (число из URL страницы мода в Steam)
   - Пример: `https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985`
   - Workshop ID: `2392709985`
4. Нажмите **"Save & Apply Mods"**
5. При следующем запуске сервер автоматически скачает моды

## 🔧 Структура проекта

```
pz_server_manager/
├── main.py              # Главный файл запуска
├── main_window.py       # Главное окно GUI
├── server_installer.py  # Установщик SteamCMD и сервера
├── server_process.py    # Управление процессом сервера
├── config_manager.py    # Работа с конфигами (.ini, .lua)
├── mod_manager.py       # Управление модами
├── translations.py      # Переводы (EN / RU)
├── requirements.txt     # Зависимости Python
├── run.bat / run.sh     # Скрипты запуска
├── build.bat / build.sh # Скрипты сборки
├── .gitignore           # Git ignore
└── README.md            # Этот файл
```

## 🌐 Сетевые порты

Для работы сервера откройте следующие порты в брандмауэре и на роутере:

| Порт | Протокол | Назначение |
|------|----------|------------|
| 16261 | UDP | Основной игровой порт |
| 16262 | UDP | Прямое подключение |
| 8766 | UDP | Steam порт |
| 8767 | UDP | Steam порт 2 |
| 27015 | TCP | RCON (удалённое управление) |

### Открытие портов

**Windows (PowerShell от администратора):**
```powershell
netsh advfirewall firewall add rule name="PZ Server UDP" dir=in action=allow protocol=UDP localport=16261-16262
netsh advfirewall firewall add rule name="PZ Server Steam" dir=in action=allow protocol=UDP localport=8766-8767
netsh advfirewall firewall add rule name="PZ Server RCON" dir=in action=allow protocol=TCP localport=27015
```

**Linux (UFW):**
```bash
sudo ufw allow 16261:16262/udp
sudo ufw allow 8766:8767/udp
sudo ufw allow 27015/tcp
```

**Linux (iptables):**
```bash
sudo iptables -A INPUT -p udp --dport 16261:16262 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 8766:8767 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 27015 -j ACCEPT
```

**macOS:**
```bash
# Добавьте правила в /etc/pf.conf, затем:
sudo pfctl -f /etc/pf.conf
```

## 📁 Расположение файлов

### Windows

| Тип | Путь |
|-----|------|
| Сервер | `C:\PZServer\` (по умолчанию) |
| SteamCMD | `C:\PZServer\steamcmd\` |
| Конфиги сервера | `%USERPROFILE%\Zomboid\Server\` |
| Сохранения | `%USERPROFILE%\Zomboid\Saves\` |
| Логи | `%USERPROFILE%\Zomboid\server-console.txt` |

### macOS / Linux

| Тип | Путь |
|-----|------|
| Сервер | `~/pzserver` (по умолчанию) |
| SteamCMD | `~/pzserver/steamcmd/` |
| Конфиги сервера | `~/Zomboid/Server/` |
| Сохранения | `~/Zomboid/Saves/` |
| Логи | `~/Zomboid/server-console.txt` |

## ⚠️ Важные замечания

1. **Первый запуск сервера** создаёт файлы конфигурации. Если настройки не сохраняются, запустите сервер хотя бы один раз.

2. **Моды**: При добавлении модов вам может понадобиться также указать **Mod ID** (не Workshop ID). Mod ID указан в файле `mod.info` внутри мода.

3. **Память**: Рекомендуется минимум 4 ГБ свободной RAM для комфортной работы сервера.

4. **Обновления**: Используйте кнопку "Update Server" для обновления до последней версии.

5. **Linux**: Для SteamCMD необходим пакет `lib32gcc-s1` (Ubuntu/Debian) или `glibc.i686` (Fedora).

## 🐛 Устранение проблем

### Сервер не запускается
- Проверьте, что Java установлена (OpenJDK 17+ или Oracle JDK)
- Убедитесь, что порты не заняты другим приложением
- Проверьте логи в `~/Zomboid/server-console.txt` (или `%USERPROFILE%\Zomboid\` на Windows)

### SteamCMD не скачивается
- Проверьте интернет-соединение
- Отключите VPN если используется
- Попробуйте скачать вручную с https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip (Windows) или `steamcmd_linux.tar.gz` / `steamcmd_osx.tar.gz`

### SteamCMD не запускается (Linux)
- Установите 32-битные библиотеки: `sudo apt install lib32gcc-s1`
- Для Fedora/RHEL: `sudo dnf install glibc.i686 libstdc++.i686`

### Моды не работают
- Убедитесь, что указан правильный Workshop ID
- Проверьте, что мод совместим с версией игры
- Перезапустите сервер после добавления модов

### Игроки не могут подключиться
- Проверьте открытие портов в брандмауэре
- Настройте проброс портов (port forwarding) на роутере
- Убедитесь, что сервер виден в списке (опция "Open" включена)

## 📄 Лицензия

MIT License

## 🤝 Вклад в проект

Pull requests приветствуются! Для крупных изменений сначала создайте issue для обсуждения.

---

**Автор**: PZ Server Manager  
**Версия**: 1.1.0  
**Совместимость**: Project Zomboid Build 41+  
**Платформы**: Windows, macOS, Linux

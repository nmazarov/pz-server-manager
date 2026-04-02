#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translations Module
Contains all UI text in supported languages.
"""

TRANSLATIONS = {
    'en': {
        # Window
        'app_title': 'Project Zomboid Server Manager',
        
        # Tabs
        'tab_server': '🎮 Server Control',
        'tab_settings': '⚙️ Server Settings',
        'tab_sandbox': '🎲 Sandbox Settings',
        'tab_mods': '🧩 Mods',
        'tab_install': '📥 Install',
        
        # Server Control Tab
        'server_status': 'Server Status',
        'server_running': 'Server Running',
        'server_stopped': 'Server Stopped',
        'server_name': 'Server Name:',
        'server_name_tooltip': 'Name of the server configuration (folder name in Zomboid/Server/)',
        'controls': 'Controls',
        'btn_start': '▶ START',
        'btn_stop': '■ STOP',
        'btn_restart': '↻ RESTART',
        'server_console': 'Server Console',
        'command_placeholder': 'Enter server command...',
        'btn_send': 'Send',
        'btn_clear': 'Clear',
        
        # Settings Tab
        'basic_settings': 'Basic Settings',
        'server_name_setting': 'Server Name:',
        'description': 'Description:',
        'password': 'Password:',
        'password_placeholder': 'Leave empty for no password',
        'max_players': 'Max Players:',
        'network_settings': 'Network Settings',
        'game_port': 'Game Port (UDP):',
        'steam_port': 'Steam Port:',
        'rcon_port': 'RCON Port:',
        'rcon_password': 'RCON Password:',
        'public_server': 'Public Server:',
        'public_server_checkbox': 'List on public server browser',
        'gameplay_settings': 'Gameplay Settings',
        'pvp': 'PvP:',
        'pvp_checkbox': 'Enable PvP',
        'pause_empty': 'Pause Empty:',
        'pause_empty_checkbox': 'Pause when server is empty',
        'global_chat': 'Global Chat:',
        'global_chat_checkbox': 'Enable global chat',
        'safety_system': 'Safety System:',
        'safety_system_checkbox': 'Enable safety system (spawn protection)',
        'show_safety': 'Show Safety:',
        'show_safety_checkbox': 'Show safety indicators',
        'spawn_point': 'Spawn Point (x,y,z):',
        'admin_settings': 'Admin Settings',
        'admin_password': 'Admin Password:',
        'auto_save': 'Auto-save Interval:',
        'btn_save_settings': '💾 Save Settings',
        'btn_reload_settings': '🔄 Reload Settings',
        
        # Sandbox Tab
        'preset': 'Preset:',
        'zombie_settings': 'Zombie Settings',
        'zombie_count': 'Zombie Count:',
        'distribution': 'Distribution:',
        'speed': 'Speed:',
        'strength': 'Strength:',
        'toughness': 'Toughness:',
        'transmission': 'Transmission:',
        'cognition': 'Cognition:',
        'loot_settings': 'Loot & Resources',
        'loot_rarity': 'Loot Rarity:',
        'loot_respawn': 'Loot Respawn:',
        'water_shutoff': 'Water Shutoff:',
        'electricity_shutoff': 'Electricity Shutoff:',
        'time_settings': 'Time & Environment',
        'start_month': 'Start Month:',
        'start_day': 'Start Day:',
        'day_length': 'Day Length:',
        'character_settings': 'Character & XP',
        'xp_multiplier': 'XP Multiplier:',
        'player_damage': 'Damage to Player:',
        'infection_mortality': 'Infection Mortality:',
        'btn_save_sandbox': '💾 Save Sandbox Settings',
        'btn_reload': '🔄 Reload',
        
        # Mods Tab
        'mods_info': '💡 Add mods using their Steam Workshop ID. You can find the ID in the workshop URL (e.g., steamcommunity.com/sharedfiles/filedetails/?id=<b>123456789</b>)',
        'installed_mods': 'Installed Mods',
        'btn_add_mod': '➕ Add Mod',
        'btn_remove_mod': '➖ Remove Selected',
        'btn_clear_mods': '🗑️ Clear All',
        'import_export': 'Import / Export',
        'btn_import': '📥 Import Mod List',
        'btn_export': '📤 Export Mod List',
        'btn_save_mods': '💾 Save & Apply Mods',
        'add_mod_title': 'Add Mod',
        'add_mod_prompt': 'Enter Steam Workshop ID:',
        'invalid_id': 'Invalid ID',
        'invalid_id_msg': 'Workshop ID must be a number.',
        
        # Install Tab
        'install_path': 'Installation Path',
        'btn_browse': 'Browse...',
        'install_status': 'Installation Status',
        'ready_to_install': 'Ready to install',
        'btn_install': '📥 Install / Update Server',
        'install_warning': '⚠️ Installation requires ~3GB of disk space.\nMake sure to open ports 16261 (UDP) and 27015 (TCP) in your firewall.',
        
        # Menu
        'menu_file': 'File',
        'menu_change_dir': 'Change Server Directory...',
        'menu_exit': 'Exit',
        'menu_tools': 'Tools',
        'menu_validate': 'Validate Server Files',
        'menu_update': 'Update Server',
        'menu_open_config': 'Open Config Folder',
        'menu_open_server': 'Open Server Folder',
        'menu_help': 'Help',
        'menu_about': 'About',
        'menu_firewall': 'Firewall Info',
        'menu_language': 'Language',
        
        # Dialogs
        'confirm': 'Confirm',
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'server_not_installed': 'Server Not Installed',
        'server_not_installed_msg': 'Please install the server first using the Install tab.',
        'settings_saved': 'Settings saved successfully!',
        'settings_loaded': 'Settings loaded',
        'no_config_found': 'No config found - using defaults',
        'mods_saved': 'Mods saved. The server will download mods on next start.',
        'confirm_clear_mods': 'Are you sure you want to remove all mods?',
        'confirm_install': 'Install Project Zomboid Server to:\n{path}\n\nThis will download ~3GB of files.\nContinue?',
        'install_complete': 'Installation Complete',
        'install_complete_msg': 'Project Zomboid Server has been installed successfully!\n\nRemember to open the following ports in your firewall:\n• 16261 (UDP) - Game port\n• 27015 (TCP) - RCON port\n\nYou can now configure and start your server.',
        'install_failed': 'Installation Failed',
        'server_running_close': 'Server Running',
        'server_running_close_msg': 'The server is still running.\nDo you want to stop it before closing?',
        'folder_not_found': 'Folder Not Found',
        'about_text': 'Project Zomboid Server Manager\nVersion 1.1.0\n\nA cross-platform tool for installing and managing\nProject Zomboid dedicated servers.\n\nSupports Windows, macOS, and Linux.\n\nMade with ❤️ using Python and PyQt5',
        'firewall_info': 'Firewall Configuration',
        'firewall_info_msg': 'To allow connections to your server, you need to open\nthe following ports in your firewall:\n\n• 16261 (UDP) - Main game port\n• 16262 (UDP) - Direct connect port\n• 8766 (UDP) - Steam port\n• 8767 (UDP) - Steam port 2\n• 27015 (TCP) - RCON port\n\nWindows: Use Windows Firewall or netsh\nmacOS: Use System Settings > Network > Firewall\nLinux: Use ufw or iptables\n\nYou may also need to configure port forwarding\non your router for external connections.',
        'admin_required': 'Administrator Rights Required',
        'admin_required_msg': 'Cannot write to: {path}\n\nThis folder requires administrator privileges.\n\nOptions:\n1. Run this application as Administrator\n2. Choose a different folder (e.g., C:\\Games\\PZServer)\n\nWould you like to choose a different folder?',
        'server_not_found': 'Server Not Found',
        'server_not_found_msg': 'Project Zomboid server is not installed.\n\nWould you like to install it now?\n\nThis will download SteamCMD and the dedicated server files (~3GB).',
        
        # Status
        'status_running': 'Server is running',
        'status_stopped': 'Server is stopped',
        'starting_server': 'Starting server',
        'stopping_server': 'Stopping server...',
        'restarting_server': 'Restarting server...',
        
        # Sandbox values
        'none': 'None',
        'insane': 'Insane',
        'very_high': 'Very High',
        'high': 'High',
        'normal': 'Normal',
        'low': 'Low',
        'very_low': 'Very Low',
        'urban_focused': 'Urban Focused',
        'uniform': 'Uniform',
        'random': 'Random',
        'sprinters': 'Sprinters',
        'fast_shamblers': 'Fast Shamblers',
        'shamblers': 'Shamblers',
        'superhuman': 'Superhuman',
        'weak': 'Weak',
        'tough': 'Tough',
        'fragile': 'Fragile',
        'blood_saliva': 'Blood + Saliva',
        'saliva_only': 'Saliva Only',
        'everyone_infected': "Everyone's Infected",
        'navigate_doors': 'Navigate + Use Doors',
        'navigate': 'Navigate',
        'basic_navigation': 'Basic Navigation',
        'extremely_rare': 'Extremely Rare',
        'rare': 'Rare',
        'common': 'Common',
        'abundant': 'Abundant',
        'every_day': 'Every Day',
        'every_week': 'Every Week',
        'every_month': 'Every Month',
        'every_2_months': 'Every 2 Months',
        'never': 'Never',
        'days': 'days',
        'instant': 'Instant',
        '0_30_sec': '0-30 sec',
        '0_1_min': '0-1 min',
        '0_12_hours': '0-12 hours',
        '1_2_days': '1-2 days',
        '2_3_days': '2-3 days',
        '1_week': '1 week',
        
        # Months
        'january': 'January',
        'february': 'February',
        'march': 'March',
        'april': 'April',
        'may': 'May',
        'june': 'June',
        'july': 'July',
        'august': 'August',
        'september': 'September',
        'october': 'October',
        'november': 'November',
        'december': 'December',
    },
    
    'ru': {
        # Window
        'app_title': 'Менеджер сервера Project Zomboid',
        
        # Tabs
        'tab_server': '🎮 Управление',
        'tab_settings': '⚙️ Настройки',
        'tab_sandbox': '🎲 Sandbox',
        'tab_mods': '🧩 Моды',
        'tab_install': '📥 Установка',
        
        # Server Control Tab
        'server_status': 'Статус сервера',
        'server_running': 'Сервер запущен',
        'server_stopped': 'Сервер остановлен',
        'server_name': 'Имя сервера:',
        'server_name_tooltip': 'Имя конфигурации сервера (название папки в Zomboid/Server/)',
        'controls': 'Управление',
        'btn_start': '▶ СТАРТ',
        'btn_stop': '■ СТОП',
        'btn_restart': '↻ РЕСТАРТ',
        'server_console': 'Консоль сервера',
        'command_placeholder': 'Введите команду...',
        'btn_send': 'Отправить',
        'btn_clear': 'Очистить',
        
        # Settings Tab
        'basic_settings': 'Основные настройки',
        'server_name_setting': 'Название сервера:',
        'description': 'Описание:',
        'password': 'Пароль:',
        'password_placeholder': 'Оставьте пустым для игры без пароля',
        'max_players': 'Макс. игроков:',
        'network_settings': 'Сетевые настройки',
        'game_port': 'Игровой порт (UDP):',
        'steam_port': 'Steam порт:',
        'rcon_port': 'RCON порт:',
        'rcon_password': 'RCON пароль:',
        'public_server': 'Публичный сервер:',
        'public_server_checkbox': 'Показывать в списке серверов',
        'gameplay_settings': 'Игровые настройки',
        'pvp': 'PvP:',
        'pvp_checkbox': 'Включить PvP',
        'pause_empty': 'Пауза:',
        'pause_empty_checkbox': 'Пауза когда сервер пуст',
        'global_chat': 'Глобальный чат:',
        'global_chat_checkbox': 'Включить глобальный чат',
        'safety_system': 'Защита:',
        'safety_system_checkbox': 'Система безопасности (защита спавна)',
        'show_safety': 'Показ защиты:',
        'show_safety_checkbox': 'Показывать индикаторы защиты',
        'spawn_point': 'Точка спавна (x,y,z):',
        'admin_settings': 'Настройки администратора',
        'admin_password': 'Пароль админа:',
        'auto_save': 'Интервал автосохранения:',
        'btn_save_settings': '💾 Сохранить настройки',
        'btn_reload_settings': '🔄 Перезагрузить',
        
        # Sandbox Tab
        'preset': 'Пресет:',
        'zombie_settings': 'Настройки зомби',
        'zombie_count': 'Количество зомби:',
        'distribution': 'Распределение:',
        'speed': 'Скорость:',
        'strength': 'Сила:',
        'toughness': 'Прочность:',
        'transmission': 'Заражение:',
        'cognition': 'Интеллект:',
        'loot_settings': 'Лут и ресурсы',
        'loot_rarity': 'Редкость лута:',
        'loot_respawn': 'Респаун лута:',
        'water_shutoff': 'Отключение воды:',
        'electricity_shutoff': 'Отключение электричества:',
        'time_settings': 'Время и окружение',
        'start_month': 'Начальный месяц:',
        'start_day': 'Начальный день:',
        'day_length': 'Длина дня:',
        'character_settings': 'Персонаж и опыт',
        'xp_multiplier': 'Множитель опыта:',
        'player_damage': 'Урон игроку:',
        'infection_mortality': 'Смертность от заражения:',
        'btn_save_sandbox': '💾 Сохранить Sandbox',
        'btn_reload': '🔄 Обновить',
        
        # Mods Tab
        'mods_info': '💡 Добавляйте моды по их Steam Workshop ID. ID можно найти в URL мода (например, steamcommunity.com/sharedfiles/filedetails/?id=<b>123456789</b>)',
        'installed_mods': 'Установленные моды',
        'btn_add_mod': '➕ Добавить мод',
        'btn_remove_mod': '➖ Удалить выбранный',
        'btn_clear_mods': '🗑️ Удалить все',
        'import_export': 'Импорт / Экспорт',
        'btn_import': '📥 Импорт списка',
        'btn_export': '📤 Экспорт списка',
        'btn_save_mods': '💾 Сохранить моды',
        'add_mod_title': 'Добавить мод',
        'add_mod_prompt': 'Введите Steam Workshop ID:',
        'invalid_id': 'Неверный ID',
        'invalid_id_msg': 'Workshop ID должен быть числом.',
        
        # Install Tab
        'install_path': 'Путь установки',
        'btn_browse': 'Обзор...',
        'install_status': 'Статус установки',
        'ready_to_install': 'Готов к установке',
        'btn_install': '📥 Установить / Обновить сервер',
        'install_warning': '⚠️ Для установки требуется ~3 ГБ свободного места.\nНе забудьте открыть порты 16261 (UDP) и 27015 (TCP) в брандмауэре.',
        
        # Menu
        'menu_file': 'Файл',
        'menu_change_dir': 'Изменить папку сервера...',
        'menu_exit': 'Выход',
        'menu_tools': 'Инструменты',
        'menu_validate': 'Проверить файлы сервера',
        'menu_update': 'Обновить сервер',
        'menu_open_config': 'Открыть папку конфигов',
        'menu_open_server': 'Открыть папку сервера',
        'menu_help': 'Помощь',
        'menu_about': 'О программе',
        'menu_firewall': 'Информация о портах',
        'menu_language': 'Язык',
        
        # Dialogs
        'confirm': 'Подтверждение',
        'success': 'Успех',
        'error': 'Ошибка',
        'warning': 'Предупреждение',
        'server_not_installed': 'Сервер не установлен',
        'server_not_installed_msg': 'Сначала установите сервер на вкладке "Установка".',
        'settings_saved': 'Настройки успешно сохранены!',
        'settings_loaded': 'Настройки загружены',
        'no_config_found': 'Конфиг не найден - используются значения по умолчанию',
        'mods_saved': 'Моды сохранены. Сервер скачает их при следующем запуске.',
        'confirm_clear_mods': 'Вы уверены, что хотите удалить все моды?',
        'confirm_install': 'Установить сервер Project Zomboid в:\n{path}\n\nБудет скачано ~3 ГБ данных.\nПродолжить?',
        'install_complete': 'Установка завершена',
        'install_complete_msg': 'Сервер Project Zomboid успешно установлен!\n\nНе забудьте открыть порты в брандмауэре:\n• 16261 (UDP) - Игровой порт\n• 27015 (TCP) - RCON порт\n\nТеперь можно настроить и запустить сервер.',
        'install_failed': 'Ошибка установки',
        'server_running_close': 'Сервер запущен',
        'server_running_close_msg': 'Сервер всё ещё работает.\nОстановить его перед закрытием?',
        'folder_not_found': 'Папка не найдена',
        'about_text': 'Менеджер сервера Project Zomboid\nВерсия 1.1.0\n\nКроссплатформенная программа для установки и управления\nвыделенным сервером Project Zomboid.\n\nПоддерживает Windows, macOS и Linux.\n\nСделано с ❤️ на Python и PyQt5',
        'firewall_info': 'Настройка брандмауэра',
        'firewall_info_msg': 'Для подключения к серверу откройте\nследующие порты в брандмауэре:\n\n• 16261 (UDP) - Основной игровой порт\n• 16262 (UDP) - Прямое подключение\n• 8766 (UDP) - Steam порт\n• 8767 (UDP) - Steam порт 2\n• 27015 (TCP) - RCON порт\n\nWindows: Брандмауэр Windows или netsh\nmacOS: Настройки > Сеть > Брандмауэр\nLinux: ufw или iptables\n\nТакже настройте проброс портов\nна роутере для внешних подключений.',
        'admin_required': 'Требуются права администратора',
        'admin_required_msg': 'Нет доступа к папке: {path}\n\nЭта папка требует прав администратора.\n\nВарианты:\n1. Запустите программу от имени администратора\n2. Выберите другую папку (например, C:\\Games\\PZServer)\n\nВыбрать другую папку?',
        'server_not_found': 'Сервер не найден',
        'server_not_found_msg': 'Сервер Project Zomboid не установлен.\n\nУстановить сейчас?\n\nБудут скачаны SteamCMD и файлы сервера (~3 ГБ).',
        
        # Status
        'status_running': 'Сервер работает',
        'status_stopped': 'Сервер остановлен',
        'starting_server': 'Запуск сервера',
        'stopping_server': 'Остановка сервера...',
        'restarting_server': 'Перезапуск сервера...',
        
        # Sandbox values
        'none': 'Нет',
        'insane': 'Безумное',
        'very_high': 'Очень высокое',
        'high': 'Высокое',
        'normal': 'Нормальное',
        'low': 'Низкое',
        'very_low': 'Очень низкое',
        'urban_focused': 'В городах',
        'uniform': 'Равномерное',
        'random': 'Случайное',
        'sprinters': 'Бегуны',
        'fast_shamblers': 'Быстрые шатуны',
        'shamblers': 'Шатуны',
        'superhuman': 'Сверхчеловеческая',
        'weak': 'Слабая',
        'tough': 'Крепкие',
        'fragile': 'Хрупкие',
        'blood_saliva': 'Кровь + Слюна',
        'saliva_only': 'Только слюна',
        'everyone_infected': 'Все заражены',
        'navigate_doors': 'Навигация + Двери',
        'navigate': 'Навигация',
        'basic_navigation': 'Базовая навигация',
        'extremely_rare': 'Крайне редкий',
        'rare': 'Редкий',
        'common': 'Обычный',
        'abundant': 'Изобильный',
        'every_day': 'Каждый день',
        'every_week': 'Каждую неделю',
        'every_month': 'Каждый месяц',
        'every_2_months': 'Каждые 2 месяца',
        'never': 'Никогда',
        'days': 'дней',
        'instant': 'Мгновенно',
        '0_30_sec': '0-30 сек',
        '0_1_min': '0-1 мин',
        '0_12_hours': '0-12 часов',
        '1_2_days': '1-2 дня',
        '2_3_days': '2-3 дня',
        '1_week': '1 неделя',
        
        # Months
        'january': 'Январь',
        'february': 'Февраль',
        'march': 'Март',
        'april': 'Апрель',
        'may': 'Май',
        'june': 'Июнь',
        'july': 'Июль',
        'august': 'Август',
        'september': 'Сентябрь',
        'october': 'Октябрь',
        'november': 'Ноябрь',
        'december': 'Декабрь',
    }
}


class Translator:
    """Simple translator class."""
    
    def __init__(self, language: str = 'en'):
        self.language = language
        self.translations = TRANSLATIONS
        
    def set_language(self, language: str):
        """Set the current language."""
        if language in self.translations:
            self.language = language
            
    def get(self, key: str, **kwargs) -> str:
        """Get translated string."""
        text = self.translations.get(self.language, {}).get(key, '')
        if not text:
            # Fallback to English
            text = self.translations.get('en', {}).get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
                
        return text
    
    def __call__(self, key: str, **kwargs) -> str:
        """Shortcut for get()."""
        return self.get(key, **kwargs)


# Global translator instance
_translator = Translator('ru')  # Default to Russian


def set_language(language: str):
    """Set the global language."""
    _translator.set_language(language)
    

def get_language() -> str:
    """Get current language."""
    return _translator.language


def tr(key: str, **kwargs) -> str:
    """Translate a key."""
    return _translator.get(key, **kwargs)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translations Module
Contains all UI text in supported languages (EN / RU).
"""

TRANSLATIONS = {
    'en': {
        # ── Window ──────────────────────────────────────────────
        'app_title': 'Project Zomboid Server Manager',

        # ── Tabs ────────────────────────────────────────────────
        'tab_server':   '🎮 Server Control',
        'tab_settings': '⚙️ Server Settings',
        'tab_sandbox':  '🎲 Sandbox Settings',
        'tab_mods':     '🧩 Mods',
        'tab_install':  '📥 Install',

        # ── Server Control Tab ───────────────────────────────────
        'server_status':         'Server Status',
        'server_running':        'Server Running',
        'server_stopped':        'Server Stopped',
        'server_name':           'Server Name:',
        'server_name_tooltip':   'Name of the server configuration (folder name in Zomboid/Server/)',
        'controls':              'Controls',
        'btn_start':             '▶ START',
        'btn_stop':              '■ STOP',
        'btn_restart':           '↻ RESTART',
        'server_console':        'Server Console',
        'command_placeholder':   'Enter server command...',
        'btn_send':              'Send',
        'btn_clear':             'Clear',

        # ── Group boxes ──────────────────────────────────────────
        'group_basic':          'Basic Settings',
        'group_network':        'Network',
        'group_gameplay':       'Gameplay',
        'group_safehouse':      'Safehouses',
        'group_chat_voice':     'Chat & Voice',
        'group_security':       'Security',
        'group_admin':          'Administration',
        'group_zombie':         'Zombies',
        'group_zombie_lore':    'Zombie Lore',
        'group_loot':           'Loot & Resources',
        'group_time':           'Time & Environment',
        'group_world':          'World State',
        'group_vehicles':       'Vehicles',
        'group_character':      'Character & XP',
        'group_mods':           'Installed Mods',
        'group_import_export':  'Import / Export',
        'group_install_path':   'Installation Path',
        'group_install_status': 'Installation Status',

        # ── Labels – Server Settings ──────────────────────────────
        'lbl_server_name':     'Server Name:',
        'lbl_description':     'Description:',
        'lbl_password':        'Password:',
        'lbl_max_players':     'Max Players:',
        'lbl_map':             'Map:',
        'lbl_welcome_msg':     'Welcome Message:',
        'lbl_game_port':       'Game Port (UDP):',
        'lbl_direct_port':     'Direct Connect Port:',
        'lbl_steam_port1':     'Steam Port 1:',
        'lbl_steam_port2':     'Steam Port 2:',
        'lbl_rcon_port':       'RCON Port:',
        'lbl_rcon_password':   'RCON Password:',
        'lbl_spawn_point':     'Spawn Point (x,y,z):',
        'lbl_admin_password':  'Admin Password:',
        'lbl_auto_save':       'Auto-save Interval:',
        'lbl_backups_count':   'Backup Count:',
        'lbl_backups_period':  'Backup Period:',
        'lbl_speed_limit':     'Speed Limit:',
        'lbl_max_accounts':    'Max Accounts/User:',
        'lbl_voice_min':       'Voice Min Distance:',
        'lbl_voice_max':       'Voice Max Distance:',
        'lbl_drop_on_death':   'Drop on Death:',

        # ── Placeholders ─────────────────────────────────────────
        'ph_empty_no_password': 'Leave empty for no password',
        'ph_welcome_msg':       'Welcome to our server!',
        'ph_map':               'Muldraugh, KY',

        # ── Checkboxes – Server Settings ──────────────────────────
        'chk_public':                 'List in public server browser',
        'chk_pvp':                    'Enable PvP',
        'chk_pause_empty':            'Pause when server is empty',
        'chk_global_chat':            'Enable global chat',
        'chk_safety_system':          'Enable safety system (spawn protection)',
        'chk_show_safety':            'Show safety indicators',
        'chk_announce_death':         'Announce player death in chat',
        'chk_sleep_allowed':          'Allow sleeping',
        'chk_sleep_needed':           'Sleep needed to pass time',
        'chk_allow_coop':             'Allow cooperative play',
        'chk_no_fire':                'Disable fire spread',
        'chk_allow_destruction':      'Allow sledgehammer destruction',
        'chk_player_safehouse':       'Allow player safehouses',
        'chk_admin_safehouse':        'Allow admin safehouses',
        'chk_safehouse_trespassing':  'Allow safehouse trespassing',
        'chk_safehouse_fire':         'Allow fire in safehouses',
        'chk_safehouse_loot':         'Allow looting safehouses',
        'chk_safehouse_respawn':      'Allow respawn in safehouses',
        'chk_voice_enable':           'Enable voice chat',
        'chk_voice_3d':               '3D positional voice',
        'chk_display_username':       'Display usernames above players',
        'chk_secure_join':            'Use secure join',
        'chk_non_ascii':              'Allow non-ASCII usernames',
        'chk_auto_whitelist':         'Auto-add players to whitelist',

        # ── Labels – Sandbox ─────────────────────────────────────
        'lbl_preset':              'Preset:',
        'lbl_zombie_count':        'Zombie Count:',
        'lbl_distribution':        'Distribution:',
        'lbl_speed':               'Speed:',
        'lbl_strength':            'Strength:',
        'lbl_toughness':           'Toughness:',
        'lbl_transmission':        'Transmission:',
        'lbl_cognition':           'Cognition:',
        'lbl_memory':              'Memory:',
        'lbl_decomp':              'Decomposition:',
        'lbl_hearing':             'Hearing:',
        'lbl_sight':               'Sight:',
        'lbl_smell':               'Smell:',
        'lbl_loot_rarity':         'Loot Rarity:',
        'lbl_loot_respawn':        'Loot Respawn:',
        'lbl_water_shutoff':       'Water Shutoff:',
        'lbl_electricity_shutoff': 'Electricity Shutoff:',
        'lbl_start_month':         'Start Month:',
        'lbl_start_day':           'Start Day:',
        'lbl_day_length':          'Day Length:',
        'lbl_night_darkness':      'Night Darkness:',
        'lbl_fire_spread':         'Fire Spread:',
        'lbl_nature_abundance':    'Nature Abundance:',
        'lbl_time_since_apo':      'Time Since Apocalypse:',
        'lbl_pop_multiplier':      'Population Multiplier:',
        'lbl_car_spawn':           'Car Spawn Rate:',
        'lbl_vehicle_easy_use':    'Easy Vehicle Use:',
        'lbl_xp_multiplier':       'XP Multiplier:',
        'lbl_player_damage':       'Damage to Player:',
        'lbl_infection_mortality': 'Infection Mortality:',
        'lbl_char_free_points':    'Starting Free Points:',
        'lbl_farming_speed':       'Farming Speed:',
        'lbl_generator_spawn':     'Generator Spawning:',
        'lbl_generator_fuel':      'Generator Fuel Use:',

        # ── Install tab ───────────────────────────────────────────
        'lbl_ready_install':  'Ready to install',
        'btn_install_server': '📥 Install / Update Server',
        'btn_import_mods':    '📥 Import Mod List',
        'btn_export_mods':    '📤 Export Mod List',

        # ── Buttons ───────────────────────────────────────────────
        'btn_save_settings':   '💾 Save Settings',
        'btn_reload_settings': '🔄 Reload Settings',
        'btn_save_sandbox':    '💾 Save Sandbox Settings',
        'btn_reload':          '🔄 Reload',
        'btn_save_mods':       '💾 Save & Apply Mods',
        'btn_add_mod':         '➕ Add Mod',
        'btn_remove_mod':      '➖ Remove Selected',
        'btn_clear_mods':      '🗑️ Clear All',
        'btn_browse':          'Browse…',

        # ── Menu ──────────────────────────────────────────────────
        'menu_file':        'File',
        'menu_change_dir':  'Change Server Directory…',
        'menu_exit':        'Exit',
        'menu_tools':       'Tools',
        'menu_validate':    'Validate Server Files',
        'menu_update':      'Update Server',
        'menu_open_config': 'Open Config Folder',
        'menu_open_server': 'Open Server Folder',
        'menu_help':        'Help',
        'menu_about':       'About',
        'menu_firewall':    'Firewall Info',
        'menu_language':    'Language',

        # ── Status bar ───────────────────────────────────────────
        'status_running':     'Server is running',
        'status_stopped':     'Server is stopped',
        'starting_server':    'Starting server…',
        'stopping_server':    'Stopping server…',
        'restarting_server':  'Restarting server…',

        # ── Dialogs ───────────────────────────────────────────────
        'confirm':                  'Confirm',
        'success':                  'Success',
        'error':                    'Error',
        'warning':                  'Warning',
        'server_not_installed':     'Server Not Installed',
        'server_not_installed_msg': 'Please install the server first using the Install tab.',
        'settings_saved':           'Settings saved successfully!',
        'settings_loaded':          'Settings loaded',
        'no_config_found':          'No config found — using defaults',
        'sandbox_saved':            'Sandbox settings saved. Restart server to apply.',
        'mods_saved':               'Mods saved. The server will download them on next start.',
        'confirm_clear_mods':       'Are you sure you want to remove all mods?',
        'confirm_install':          'Install Project Zomboid Server to:\n{path}\n\nThis will download ~3 GB of files.\nContinue?',
        'install_complete':         'Installation Complete',
        'install_complete_msg':     (
            'Project Zomboid Server installed successfully!\n\n'
            'Remember to open the following ports in your firewall:\n'
            '• 16261 (UDP) — Game port\n'
            '• 27015 (TCP) — RCON port\n\n'
            'You can now configure and start your server.'
        ),
        'install_failed':           'Installation Failed',
        'server_running_close':     'Server Running',
        'server_running_close_msg': 'The server is still running.\nStop it before closing?',
        'folder_not_found':         'Folder Not Found',
        'about_text': (
            'Project Zomboid Server Manager\n'
            'Version 1.1.0\n\n'
            'Cross-platform tool for installing and managing\n'
            'Project Zomboid dedicated servers.\n\n'
            'Supports Windows, macOS and Linux.\n\n'
            'Made with ❤️ using Python and PyQt5'
        ),
        'firewall_info':     'Firewall Configuration',
        'firewall_info_msg': (
            'Open the following ports in your firewall to allow connections:\n\n'
            '• 16261 (UDP) — Main game port\n'
            '• 16262 (UDP) — Direct connect port\n'
            '• 8766  (UDP) — Steam port 1\n'
            '• 8767  (UDP) — Steam port 2\n'
            '• 27015 (TCP) — RCON port\n\n'
            'Windows : Windows Firewall or netsh\n'
            'macOS   : System Settings › Network › Firewall\n'
            'Linux   : ufw or iptables\n\n'
            'Also configure port forwarding on your router\n'
            'for external connections.'
        ),
        'server_not_found':     'Server Not Found',
        'server_not_found_msg': (
            'Project Zomboid server is not installed.\n\n'
            'Would you like to install it now?\n\n'
            'This will download SteamCMD and the server files (~3 GB).'
        ),
        'admin_required':     'Administrator Rights Required',
        'admin_required_msg': (
            'Cannot write to: {path}\n\n'
            'Options:\n'
            '1. Run the application as Administrator\n'
            '2. Choose a different folder\n\n'
            'Choose a different folder?'
        ),

        # ── Combo values – shared ─────────────────────────────────
        'none':       'None',
        'insane':     'Insane',
        'very_high':  'Very High',
        'high':       'High',
        'normal':     'Normal',
        'low':        'Low',
        'very_low':   'Very Low',
        'very_fast':  'Very Fast',
        'fast':       'Fast',
        'slow':       'Slow',
        'very_slow':  'Very Slow',
        'long':       'Long',
        'short':      'Short',
        'disabled':   'Disabled',
        'random':     'Random',
        'never':      'Never',
        'unlimited':  'Unlimited',
        'days':       'days',

        # ── Zombie values ─────────────────────────────────────────
        'urban_focused':    'Urban Focused',
        'uniform':          'Uniform',
        'sprinters':        'Sprinters',
        'fast_shamblers':   'Fast Shamblers',
        'shamblers':        'Shamblers',
        'superhuman':       'Superhuman',
        'weak':             'Weak',
        'tough':            'Tough',
        'fragile':          'Fragile',
        'eagle':            'Eagle',
        'poor':             'Poor',
        'blood_saliva':     'Blood + Saliva',
        'saliva_only':      'Saliva Only',
        'everyone_infected': "Everyone's Infected",
        'navigate_doors':   'Navigate + Use Doors',
        'navigate':         'Navigate',
        'basic_navigation': 'Basic Navigation',

        # ── Loot/time values ──────────────────────────────────────
        'extremely_rare': 'Extremely Rare',
        'rare':           'Rare',
        'common':         'Common',
        'abundant':       'Abundant',
        'every_day':      'Every Day',
        'every_week':     'Every Week',
        'every_month':    'Every Month',
        'every_2_months': 'Every 2 Months',

        # ── Night / environment ───────────────────────────────────
        'pitch_black':    'Pitch Black',
        'dark':           'Dark',
        'bright':         'Bright',
        'very_abundant':  'Very Abundant',
        'fresh':          'Fresh',
        'scarce':         'Scarce',
        'very_scarce':    'Very Scarce',

        # ── World state ───────────────────────────────────────────
        'months_0_3':     '0–3 Months',
        'months_3_6':     '3–6 Months',
        'months_6_12':    '6–12 Months',
        'several_years':  'Several Years',
        'many_years':     'Many Years',

        # ── Drop on death ─────────────────────────────────────────
        'drop_nothing':   'Nothing',
        'drop_all':       'Everything',
        'drop_equipped':  'Equipped Items',
        'drop_backpack':  'Backpack',

        # ── Infection mortality ───────────────────────────────────
        'instant':     'Instant',
        '0_30_sec':    '0–30 sec',
        '0_1_min':     '0–1 min',
        '0_12_hours':  '0–12 hours',
        '1_2_days':    '1–2 days',
        '2_3_days':    '2–3 days',
        '1_week':      '1 week',

        # ── Months ────────────────────────────────────────────────
        'january':   'January',   'february': 'February',
        'march':     'March',     'april':    'April',
        'may':       'May',       'june':     'June',
        'july':      'July',      'august':   'August',
        'september': 'September', 'october':  'October',
        'november':  'November',  'december': 'December',
    },

    # ════════════════════════════════════════════════════════════════
    'ru': {
        # ── Window ──────────────────────────────────────────────
        'app_title': 'Менеджер сервера Project Zomboid',

        # ── Tabs ────────────────────────────────────────────────
        'tab_server':   '🎮 Управление',
        'tab_settings': '⚙️ Настройки сервера',
        'tab_sandbox':  '🎲 Sandbox',
        'tab_mods':     '🧩 Моды',
        'tab_install':  '📥 Установка',

        # ── Server Control Tab ───────────────────────────────────
        'server_status':       'Статус сервера',
        'server_running':      'Сервер запущен',
        'server_stopped':      'Сервер остановлен',
        'server_name':         'Имя сервера:',
        'server_name_tooltip': 'Имя конфигурации (имя папки в Zomboid/Server/)',
        'controls':            'Управление',
        'btn_start':           '▶ СТАРТ',
        'btn_stop':            '■ СТОП',
        'btn_restart':         '↻ РЕСТАРТ',
        'server_console':      'Консоль сервера',
        'command_placeholder': 'Введите команду сервера…',
        'btn_send':            'Отправить',
        'btn_clear':           'Очистить',

        # ── Group boxes ──────────────────────────────────────────
        'group_basic':          'Основные настройки',
        'group_network':        'Сеть',
        'group_gameplay':       'Игровой процесс',
        'group_safehouse':      'Убежища',
        'group_chat_voice':     'Чат и голос',
        'group_security':       'Безопасность',
        'group_admin':          'Администрирование',
        'group_zombie':         'Зомби',
        'group_zombie_lore':    'Параметры зомби',
        'group_loot':           'Лут и ресурсы',
        'group_time':           'Время и окружение',
        'group_world':          'Состояние мира',
        'group_vehicles':       'Транспорт',
        'group_character':      'Персонаж и опыт',
        'group_mods':           'Установленные моды',
        'group_import_export':  'Импорт / Экспорт',
        'group_install_path':   'Путь установки',
        'group_install_status': 'Статус установки',

        # ── Labels – Server Settings ──────────────────────────────
        'lbl_server_name':     'Название сервера:',
        'lbl_description':     'Описание:',
        'lbl_password':        'Пароль:',
        'lbl_max_players':     'Макс. игроков:',
        'lbl_map':             'Карта:',
        'lbl_welcome_msg':     'Приветствие:',
        'lbl_game_port':       'Игровой порт (UDP):',
        'lbl_direct_port':     'Порт прямого подключения:',
        'lbl_steam_port1':     'Steam порт 1:',
        'lbl_steam_port2':     'Steam порт 2:',
        'lbl_rcon_port':       'RCON порт:',
        'lbl_rcon_password':   'RCON пароль:',
        'lbl_spawn_point':     'Точка спавна (x,y,z):',
        'lbl_admin_password':  'Пароль администратора:',
        'lbl_auto_save':       'Интервал автосохранения:',
        'lbl_backups_count':   'Количество резервных копий:',
        'lbl_backups_period':  'Период резервного копирования:',
        'lbl_speed_limit':     'Лимит скорости:',
        'lbl_max_accounts':    'Макс. аккаунтов на игрока:',
        'lbl_voice_min':       'Мин. дистанция голоса:',
        'lbl_voice_max':       'Макс. дистанция голоса:',
        'lbl_drop_on_death':   'Выбросить при смерти:',

        # ── Placeholders ─────────────────────────────────────────
        'ph_empty_no_password': 'Оставьте пустым для игры без пароля',
        'ph_welcome_msg':       'Добро пожаловать на наш сервер!',
        'ph_map':               'Muldraugh, KY',

        # ── Checkboxes – Server Settings ──────────────────────────
        'chk_public':                 'Показывать в браузере серверов',
        'chk_pvp':                    'Включить PvP',
        'chk_pause_empty':            'Пауза при пустом сервере',
        'chk_global_chat':            'Включить глобальный чат',
        'chk_safety_system':          'Система безопасности (защита спавна)',
        'chk_show_safety':            'Показывать индикаторы защиты',
        'chk_announce_death':         'Объявлять о гибели игрока в чате',
        'chk_sleep_allowed':          'Разрешить сон',
        'chk_sleep_needed':           'Сон необходим для прохода времени',
        'chk_allow_coop':             'Разрешить совместную игру',
        'chk_no_fire':                'Отключить распространение огня',
        'chk_allow_destruction':      'Разрешить снос стен кувалдой',
        'chk_player_safehouse':       'Разрешить убежища игроков',
        'chk_admin_safehouse':        'Разрешить убежища администраторов',
        'chk_safehouse_trespassing':  'Разрешить вторжение в убежища',
        'chk_safehouse_fire':         'Разрешить огонь в убежищах',
        'chk_safehouse_loot':         'Разрешить лут в убежищах',
        'chk_safehouse_respawn':      'Разрешить респаун в убежищах',
        'chk_voice_enable':           'Включить голосовой чат',
        'chk_voice_3d':               '3D позиционный голос',
        'chk_display_username':       'Показывать имена над игроками',
        'chk_secure_join':            'Безопасное подключение',
        'chk_non_ascii':              'Разрешить не-ASCII имена пользователей',
        'chk_auto_whitelist':         'Авто-добавление в белый список',

        # ── Labels – Sandbox ─────────────────────────────────────
        'lbl_preset':              'Пресет:',
        'lbl_zombie_count':        'Количество зомби:',
        'lbl_distribution':        'Распределение:',
        'lbl_speed':               'Скорость:',
        'lbl_strength':            'Сила:',
        'lbl_toughness':           'Прочность:',
        'lbl_transmission':        'Передача заражения:',
        'lbl_cognition':           'Интеллект:',
        'lbl_memory':              'Память:',
        'lbl_decomp':              'Разложение:',
        'lbl_hearing':             'Слух:',
        'lbl_sight':               'Зрение:',
        'lbl_smell':               'Обоняние:',
        'lbl_loot_rarity':         'Редкость лута:',
        'lbl_loot_respawn':        'Респаун лута:',
        'lbl_water_shutoff':       'Отключение воды (дней):',
        'lbl_electricity_shutoff': 'Отключение электричества (дней):',
        'lbl_start_month':         'Начальный месяц:',
        'lbl_start_day':           'Начальный день:',
        'lbl_day_length':          'Длина дня:',
        'lbl_night_darkness':      'Тёмность ночи:',
        'lbl_fire_spread':         'Распространение огня:',
        'lbl_nature_abundance':    'Природные ресурсы:',
        'lbl_time_since_apo':      'Время с начала апокалипсиса:',
        'lbl_pop_multiplier':      'Множитель популяции:',
        'lbl_car_spawn':           'Частота появления машин:',
        'lbl_vehicle_easy_use':    'Упрощённое управление:',
        'lbl_xp_multiplier':       'Множитель опыта:',
        'lbl_player_damage':       'Урон по игроку:',
        'lbl_infection_mortality': 'Смертность от заражения:',
        'lbl_char_free_points':    'Начальные очки:',
        'lbl_farming_speed':       'Скорость фермерства:',
        'lbl_generator_spawn':     'Появление генераторов:',
        'lbl_generator_fuel':      'Расход топлива генераторами:',

        # ── Install tab ───────────────────────────────────────────
        'lbl_ready_install':  'Готов к установке',
        'btn_install_server': '📥 Установить / Обновить сервер',
        'btn_import_mods':    '📥 Импорт списка модов',
        'btn_export_mods':    '📤 Экспорт списка модов',

        # ── Buttons ───────────────────────────────────────────────
        'btn_save_settings':   '💾 Сохранить настройки',
        'btn_reload_settings': '🔄 Перезагрузить настройки',
        'btn_save_sandbox':    '💾 Сохранить Sandbox',
        'btn_reload':          '🔄 Обновить',
        'btn_save_mods':       '💾 Сохранить и применить моды',
        'btn_add_mod':         '➕ Добавить мод',
        'btn_remove_mod':      '➖ Удалить выбранный',
        'btn_clear_mods':      '🗑️ Удалить все',
        'btn_browse':          'Обзор…',

        # ── Menu ──────────────────────────────────────────────────
        'menu_file':        'Файл',
        'menu_change_dir':  'Изменить папку сервера…',
        'menu_exit':        'Выход',
        'menu_tools':       'Инструменты',
        'menu_validate':    'Проверить файлы сервера',
        'menu_update':      'Обновить сервер',
        'menu_open_config': 'Открыть папку конфигов',
        'menu_open_server': 'Открыть папку сервера',
        'menu_help':        'Помощь',
        'menu_about':       'О программе',
        'menu_firewall':    'Информация о портах',
        'menu_language':    'Язык',

        # ── Status bar ───────────────────────────────────────────
        'status_running':    'Сервер работает',
        'status_stopped':    'Сервер остановлен',
        'starting_server':   'Запуск сервера…',
        'stopping_server':   'Остановка сервера…',
        'restarting_server': 'Перезапуск сервера…',

        # ── Dialogs ───────────────────────────────────────────────
        'confirm':                  'Подтверждение',
        'success':                  'Успех',
        'error':                    'Ошибка',
        'warning':                  'Предупреждение',
        'server_not_installed':     'Сервер не установлен',
        'server_not_installed_msg': 'Сначала установите сервер на вкладке «Установка».',
        'settings_saved':           'Настройки успешно сохранены!',
        'settings_loaded':          'Настройки загружены',
        'no_config_found':          'Конфиг не найден — используются значения по умолчанию',
        'sandbox_saved':            'Настройки Sandbox сохранены. Перезапустите сервер для применения.',
        'mods_saved':               'Моды сохранены. Сервер скачает их при следующем запуске.',
        'confirm_clear_mods':       'Вы уверены, что хотите удалить все моды?',
        'confirm_install':          'Установить сервер Project Zomboid в:\n{path}\n\nБудет скачано ~3 ГБ данных.\nПродолжить?',
        'install_complete':         'Установка завершена',
        'install_complete_msg': (
            'Сервер Project Zomboid успешно установлен!\n\n'
            'Откройте следующие порты в брандмауэре:\n'
            '• 16261 (UDP) — Игровой порт\n'
            '• 27015 (TCP) — RCON порт\n\n'
            'Теперь можно настроить и запустить сервер.'
        ),
        'install_failed':           'Ошибка установки',
        'server_running_close':     'Сервер запущен',
        'server_running_close_msg': 'Сервер всё ещё работает.\nОстановить его перед закрытием?',
        'folder_not_found':         'Папка не найдена',
        'about_text': (
            'Менеджер сервера Project Zomboid\n'
            'Версия 1.1.0\n\n'
            'Кроссплатформенная программа для установки\n'
            'и управления выделенным сервером Project Zomboid.\n\n'
            'Поддерживает Windows, macOS и Linux.\n\n'
            'Сделано с ❤️ на Python и PyQt5'
        ),
        'firewall_info':     'Настройка брандмауэра',
        'firewall_info_msg': (
            'Откройте следующие порты в брандмауэре:\n\n'
            '• 16261 (UDP) — Основной игровой порт\n'
            '• 16262 (UDP) — Прямое подключение\n'
            '• 8766  (UDP) — Steam порт 1\n'
            '• 8767  (UDP) — Steam порт 2\n'
            '• 27015 (TCP) — RCON порт\n\n'
            'Windows : Брандмауэр Windows или netsh\n'
            'macOS   : Настройки › Сеть › Брандмауэр\n'
            'Linux   : ufw или iptables\n\n'
            'Также настройте проброс портов на роутере\n'
            'для внешних подключений.'
        ),
        'server_not_found':     'Сервер не найден',
        'server_not_found_msg': (
            'Сервер Project Zomboid не установлен.\n\n'
            'Установить сейчас?\n\n'
            'Будут скачаны SteamCMD и файлы сервера (~3 ГБ).'
        ),
        'admin_required':     'Требуются права администратора',
        'admin_required_msg': (
            'Нет доступа к папке: {path}\n\n'
            'Варианты:\n'
            '1. Запустите программу от имени администратора\n'
            '2. Выберите другую папку\n\n'
            'Выбрать другую папку?'
        ),

        # ── Combo values – shared ─────────────────────────────────
        'none':       'Нет',
        'insane':     'Безумное',
        'very_high':  'Очень высокое',
        'high':       'Высокое',
        'normal':     'Нормальное',
        'low':        'Низкое',
        'very_low':   'Очень низкое',
        'very_fast':  'Очень быстро',
        'fast':       'Быстро',
        'slow':       'Медленно',
        'very_slow':  'Очень медленно',
        'long':       'Долгая',
        'short':      'Короткая',
        'disabled':   'Отключено',
        'random':     'Случайно',
        'never':      'Никогда',
        'unlimited':  'Без ограничений',
        'days':       'дней',

        # ── Zombie values ─────────────────────────────────────────
        'urban_focused':    'В городах',
        'uniform':          'Равномерно',
        'sprinters':        'Бегуны',
        'fast_shamblers':   'Быстрые шатуны',
        'shamblers':        'Шатуны',
        'superhuman':       'Сверхчеловеческая',
        'weak':             'Слабая',
        'tough':            'Крепкие',
        'fragile':          'Хрупкие',
        'eagle':            'Орлиное',
        'poor':             'Плохое',
        'blood_saliva':     'Кровь + слюна',
        'saliva_only':      'Только слюна',
        'everyone_infected': 'Все заражены',
        'navigate_doors':   'Навигация + двери',
        'navigate':         'Навигация',
        'basic_navigation': 'Базовая навигация',

        # ── Loot/time values ──────────────────────────────────────
        'extremely_rare': 'Крайне редкий',
        'rare':           'Редкий',
        'common':         'Обычный',
        'abundant':       'Изобильный',
        'every_day':      'Каждый день',
        'every_week':     'Каждую неделю',
        'every_month':    'Каждый месяц',
        'every_2_months': 'Каждые 2 месяца',

        # ── Night / environment ───────────────────────────────────
        'pitch_black':   'Кромешная тьма',
        'dark':          'Тёмная',
        'bright':        'Светлая',
        'very_abundant': 'Очень богатые',
        'fresh':         'Свежие',
        'scarce':        'Скудные',
        'very_scarce':   'Очень скудные',

        # ── World state ───────────────────────────────────────────
        'months_0_3':    '0–3 месяца',
        'months_3_6':    '3–6 месяцев',
        'months_6_12':   '6–12 месяцев',
        'several_years': 'Несколько лет',
        'many_years':    'Много лет',

        # ── Drop on death ─────────────────────────────────────────
        'drop_nothing':  'Ничего',
        'drop_all':      'Всё',
        'drop_equipped': 'Надетые предметы',
        'drop_backpack': 'Рюкзак',

        # ── Infection mortality ───────────────────────────────────
        'instant':    'Мгновенно',
        '0_30_sec':   '0–30 сек',
        '0_1_min':    '0–1 мин',
        '0_12_hours': '0–12 часов',
        '1_2_days':   '1–2 дня',
        '2_3_days':   '2–3 дня',
        '1_week':     '1 неделя',

        # ── Months ────────────────────────────────────────────────
        'january':   'Январь',   'february': 'Февраль',
        'march':     'Март',     'april':    'Апрель',
        'may':       'Май',      'june':     'Июнь',
        'july':      'Июль',     'august':   'Август',
        'september': 'Сентябрь', 'october':  'Октябрь',
        'november':  'Ноябрь',   'december': 'Декабрь',
    },
}


class Translator:
    """Simple translator."""

    def __init__(self, language: str = 'en'):
        self.language = language
        self.translations = TRANSLATIONS

    def set_language(self, language: str):
        if language in self.translations:
            self.language = language

    def get(self, key: str, **kwargs) -> str:
        text = self.translations.get(self.language, {}).get(key, '')
        if not text:
            text = self.translations.get('en', {}).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    def __call__(self, key: str, **kwargs) -> str:
        return self.get(key, **kwargs)


_translator = Translator('ru')


def set_language(language: str):
    _translator.set_language(language)


def get_language() -> str:
    return _translator.language


def tr(key: str, **kwargs) -> str:
    return _translator.get(key, **kwargs)

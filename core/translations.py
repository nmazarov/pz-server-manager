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
        'server_launching':      'Starting & Loading Server...',
        'server_running':        'Server Running',
        'server_ready':          'Server Online & Ready to Play!',
        'server_stopped':        'Server Stopped',
        'tray_server_ready':     'Project Zomboid Server is online and ready to join!',
        'server_name':           'Server Name:',
        'server_name_tooltip':   'Name of the server configuration (folder name in Zomboid/Server/)',
        'controls':              'Controls',
        'group_server_control':  'Server Control',
        'group_console':         'Server Console',
        'btn_start':             '▶ START',
        'btn_stop':              '■ STOP',
        'btn_restart':           '↻ RESTART',
        'btn_start_server':      'Start Server',
        'btn_stop_server':       'Stop Server',
        'btn_restart_server':    'Restart Server',
        'server_console':        'Server Console',
        'command_placeholder':   'Enter server command...',
        'ph_command':            'Enter server command...',
        'btn_send':              'Send',
        'btn_clear':             'Clear',
        'btn_close':             'Close',

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

        # ── Sandbox Subtabs ──
        'subtab_zombies':          '🧟 Zombies & Population',
        'subtab_loot':             '📦 Loot & Resources',
        'subtab_world':            '⏱ World & Time',
        'subtab_vehicles':         '🚗 Vehicles',
        'subtab_character':        '👤 Character & Skills',
        'subtab_mods':             '🧩 Mod Options',

        # ── Detailed Sandbox Labels ──
        'group_zombie_advanced':   'Advanced Population (ZombieConfig)',
        'group_loot_categories':   '10 Loot Rarity Categories',
        'group_loot_respawn':      'Loot Respawn & Utilities',
        'lbl_loot_weapons':        'Melee Weapons:',
        'lbl_loot_ranged_weapons': 'Firearms:',
        'lbl_loot_ammo':           'Ammunition & Magazines:',
        'lbl_loot_food':           'Fresh Food:',
        'lbl_loot_canned_food':    'Canned & Packaged Food:',
        'lbl_loot_medical':        'Medical Supplies:',
        'lbl_loot_literature':     'Literature & Recipe Books:',
        'lbl_loot_survival':       'Survival Gear:',
        'lbl_loot_mechanics':      'Auto Parts & Tools:',
        'lbl_loot_other':          'Other Loot:',
        'lbl_max_items_respawn':   'Max Items in Container:',
        'lbl_construction_respawn':'Construction Prevents Respawn:',
        'lbl_pop_start_mult':      'Start Population Multiplier:',
        'lbl_pop_peak_mult':       'Peak Population Multiplier:',
        'lbl_pop_peak_day':        'Peak Population Day:',
        'lbl_respawn_hours':       'Respawn Hours:',
        'lbl_respawn_unseen_hours':'Unseen Hours Before Respawn:',
        'lbl_respawn_fraction':    'Respawn Fraction Multiplier:',
        'lbl_redistribute_hours':  'Redistribute/Migration Hours:',
        'lbl_rally_group_size':    'Zombie Rally Group Size:',
        'lbl_rally_group_radius':  'Rally Group Radius:',
        'lbl_helicopter':          'Helicopter Event:',
        'lbl_meta_event':          'Meta Events (Gunshots, Screams):',
        'lbl_sleeping_event':      'Night/Sleeping Events:',
        'lbl_erosion_speed':       'World Erosion Speed:',
        'lbl_erosion_days':        'Erosion Days (100% Growth):',
        'lbl_gas_chance':          'Gas Station / Car Gas Chance:',
        'lbl_initial_gas':         'Initial Gas Amount:',
        'lbl_gas_consumption':     'Fuel Consumption Multiplier:',
        'lbl_car_condition':       'General Vehicle Condition:',
        'lbl_traffic_jam':         'Traffic Jams on Roads:',
        'lbl_car_alarm':           'Car Alarms Frequency:',
        'lbl_crash_damage':        'Player Damaged in Car Crash:',
        'lbl_plant_resilience':    'Plant Resilience:',
        'lbl_plant_abundance':     'Farming Harvest Abundance:',
        'btn_mod_options_quick':   '⚙️ Mod Sandbox Settings',
        'group_map_order':         '🗺️ Map Load Order (Must load before Muldraugh, KY)',
        'btn_move_map_up':         '🔼 Up',
        'btn_move_map_down':       '🔽 Down',
        'btn_optimize_map_order':  '✨ Optimize Map Order',
        'lbl_mod_search':          'Search Mod Settings:',
        'ph_mod_search':           'Type setting name or description...',
        'no_mod_options_found':    'No mod-specific sandbox options found in SandboxVars.lua.\nMods that add sandbox options (e.g. Common Sense, More Traits, VFE) will appear here automatically after running the server or saving mods.',

        # ── Install tab ───────────────────────────────────────────
        'group_server_version': 'Betas & Versions',
        'lbl_selected_version_title': 'Selected version',
        'lbl_selected_version_note': 'These versions are provided by the game developer, and some of them may be unstable test builds or older versions. Please proceed with caution.',
        'col_branch_name_desc': 'NAME AND DESCRIPTION',
        'col_branch_last_update': 'LAST UPDATED',
        'lbl_hidden_betas': 'Private Betas',
        'lbl_hidden_betas_desc': 'Enter an access code to unlock a private beta branch:',
        'btn_check_beta_code': 'Check Code',
        'placeholder_beta_code': 'Access code or password',
        'placeholder_hidden_branch': 'Branch name (optional)',
        'beta_code_success': '✓ Code verified! Branch unlocked.',
        'beta_code_empty': 'Please enter an access code.',
        'lbl_server_version':   'Select Version:',
        'ver_stable':           'Stable (Build 41 - Public)',
        'ver_b42_unstable':     'Unstable (Build 42 - unstable)',
        'ver_custom':           'Custom Beta Branch…',
        'lbl_custom_branch':    'Branch Name:',
        'lbl_ready_install':  'Ready to install',
        'btn_install_server': '📥 Install Server',
        'btn_update_server':  '🔄 Update / Verify Server',
        'confirm_update':     'Update and verify Project Zomboid Dedicated Server in:\n{path}?\n\nSelected branch: {branch}',
        'update_complete':    'Server Updated',
        'update_complete_msg':'Project Zomboid dedicated server has been updated and validated successfully!',
        'btn_import_mods':    '📥 Import Mod List',
        'btn_export_mods':    '📤 Export Mod List',

        # ── Buttons ───────────────────────────────────────────────
        'btn_save_settings':   '💾 Save Settings',
        'btn_reload_settings': '🔄 Reload Settings',
        'btn_save_sandbox':    '💾 Save Sandbox Settings',
        'btn_reload':          '🔄 Reload',
        'btn_save_mods':       '💾 Save & Apply Mods',
        'btn_analyze_mods':    '🔍 Analyze & Resolve Mods',
        'btn_add_mod':         '➕ Add Mod',
        'btn_import_collection': '📦 Import Steam Collection / Pack',
        'btn_refresh_versions': '🔄 Refresh Steam Versions',
        'btn_remove_mod':      '➖ Remove Selected',
        'btn_clear_mods':      '🗑️ Clear All',
        'btn_browse':          'Browse…',
        'msg_mod_analysis_title': 'Mod Analyzer & Dependencies',
        'msg_mod_analysis_ok': 'All mod dependencies and load orders have been analyzed and verified successfully!',
        'msg_collection_prompt': 'Enter Steam Workshop Collection URL or ID:',
        'msg_collection_success': 'Collection imported successfully! Added/updated {added} mods.',

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
        'info':                     'Information',
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
            'Version 1.3.1 (MVP)\n\n'
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

        # Presets
        'preset_label': 'Preset / Difficulty:',
        'preset_select': '-- Select Preset --',
        'preset_beginner': 'Beginner',
        'preset_survival': 'Survival',
        'preset_hardcore': 'Hardcore',
        'preset_horde': 'Zombie Horde',
        'preset_builder': 'Builder',
        'preset_applied': 'Preset "{name}" applied successfully!',

        # Backups
        'btn_manage_backups': 'Manage Backups',
        'backup_title': 'Configuration Backups',
        'btn_restore': 'Restore Selected',
        'backup_restored': 'Configuration restored successfully!',
        'no_backups_found': 'No backups found for this server.',

        # Live Players
        'live_players': 'Online Players',
        'lbl_online_players': '👥 Online Players ({count})',
        'btn_kick': '👢 Kick',
        'btn_ban': '🚫 Ban',
        'btn_teleport': '🌀 Teleport',
        'btn_admin': '👑 Admin',
        'btn_whitelist': '📜 Whitelist',
        'btn_refresh_players': '🔄 Refresh',
        'no_players_online': 'No players online',
        'player_actions': 'Player Actions',
        'kick_reason_prompt': 'Enter kick reason:',
        'ban_reason_prompt': 'Enter ban reason:',
        'teleport_target_prompt': 'Teleport {player} to which player?',
        'player_kicked_success': 'Kicked player {player}',
        'player_banned_success': 'Banned player {player}',
        'player_whitelist_success': 'Added {player} to whitelist',
        'player_admin_success': 'Granted Admin permissions to {player}',

        # Watchdog
        'chk_watchdog': 'Auto-restart on crash (Watchdog)',
        'watchdog_tooltip': 'Supervises server process and automatically restarts it if it crashes unexpectedly',
        'watchdog_crashed': '⚠️ Watchdog detected crash. Restarting in {sec}s...',

        # Search
        'search_sandbox_ph': 'Search settings across all categories...',
        'search_mods_ph': 'Search installed mods...',
        'search_matches_found': 'Matches: {count}',

        # Backup Manager GUI
        'backup_mgr_title': 'World & Configuration Backup Manager',
        'btn_create_backup': 'Create Backup Now',
        'btn_restore_backup': 'Restore Selected Backup',
        'btn_delete_backup': 'Delete Backup',
        'btn_open_backup_folder': 'Open Backups Folder',
        'col_filename': 'Backup Archive',
        'col_size': 'Size (MB)',
        'col_date': 'Date Created',
        'prompt_backup_tag': 'Enter backup note / tag (e.g. before_wipe):',
        'backup_created_success': 'Backup created successfully:\n{path}',
        'backup_restore_confirm': 'Are you sure you want to restore backup "{name}"?\nCurrent world save and configurations will be overwritten!',
        'backup_restore_success': 'Backup restored successfully!\nPlease reload or restart the server.',
        'backup_delete_confirm': 'Delete backup archive "{name}"?',
        'backup_delete_success': 'Backup deleted successfully.',

        # Web Dashboard
        'btn_web_dashboard': 'Web Dashboard',
        'web_dashboard_title': 'Web Dashboard (VPS Remote Access)',
        'web_dashboard_running': 'Web Dashboard is running at:\n{url}\n\nOpen in your browser now?',
        'web_dashboard_running_btn': 'Web Dashboard (Online: 8080)',
        'web_dashboard_stopped': 'Web Dashboard stopped.',
        'web_dashboard_tooltip': 'Toggle local FastAPI Web Dashboard to manage the server via browser or mobile',
        'web_security_title': 'Web Dashboard Security Setup',
        'web_security_desc': 'For security against unauthorized bot scanners, select a custom port and admin password.',
        'web_port_label': 'Web Dashboard Port (1024 - 65535):',
        'web_pw_label': 'Admin Password:',
        'web_firewall_label': 'Automatically configure Windows Defender Firewall rule for this port',
        'btn_random_port': '🎲 Random Port',
        'btn_gen_pw': '🎲 Generate Password',
        'btn_save_start_web': 'Save & Launch Web Panel',

        # Tray
        'tray_show': 'Show Manager',
        'tray_hide': 'Hide to Tray',
        'tray_start': 'Start Server',
        'tray_stop': 'Stop Server',
        'tray_exit': 'Exit',
        'tray_server_started': 'Server has been started successfully.',
        'tray_server_stopped': 'Server has stopped.',
        'tray_minimized': 'App minimized to system tray.',

        # Diagnostics & Warnings
        'error_disk_space': 'Insufficient disk space! Needed at least {required} GB, available: {available:.2f} GB.',
        'warn_ports_in_use': 'The following ports are already in use by another application: {ports}.\nDo you still want to start the server?',
        'first_run_title': 'PZ Dedicated Server Not Found',
        'first_run_msg': 'Project Zomboid dedicated server was not found on your system.\n\nWould you like to automatically download and install SteamCMD and the server (~3GB) now?',
        'server_detected_title': 'Existing Server Detected',
        'server_detected_msg': 'Found existing Project Zomboid server at:\n{path}\n\nWould you like to use this directory as your server location?',
        # ── Additional Vehicle & Preset translations ──
        'lbl_enable_vehicles':      'Enable Vehicles in World:',
        'lbl_survivor_vehicles':    'Recent Survivor Vehicles:',
        'lbl_locked_cars':          'Locked Car Chance:',
        'lbl_zombie_attraction':    'Engine Noise Zombie Attraction:',
        'lbl_siren_shutoff':        'Siren Duration (Hours, 0=until dead):',
        'lbl_car_damage_impact':    'Vehicle Damage on Impact:',
        'lbl_player_hit_damage':    'Damage to Player Hit by Car:',
        'deadly':                   'Deadly',
        'full':                     'Full Tank',
        'btn_save_custom_preset':   '➕ Save Preset...',
        'btn_delete_custom_preset': '🗑️ Delete Preset',
        'lbl_custom_presets':       'Custom Presets',
        'prompt_custom_preset_name':'Enter a name for your custom sandbox preset:',
        'preset_saved':             'Preset "{name}" saved successfully!',
        'preset_deleted':           'Preset "{name}" deleted.',
        'confirm_delete_preset':    'Are you sure you want to delete preset "{name}"?',
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
        'server_launching':    'Запуск и загрузка сервера...',
        'server_running':      'Сервер запущен',
        'server_ready':        'Сервер запущен и готов к игре!',
        'server_stopped':      'Сервер остановлен',
        'tray_server_ready':   'Сервер Project Zomboid успешно запущен и готов к игре!',
        'server_name':         'Имя сервера:',
        'server_name_tooltip': 'Имя конфигурации (имя папки в Zomboid/Server/)',
        'controls':            'Управление',
        'group_server_control':'Управление сервером',
        'group_console':       'Консоль сервера',
        'btn_start':           '▶ ЗАПУСТИТЬ',
        'btn_stop':            '■ ОСТАНОВИТЬ',
        'btn_restart':         '↻ ПЕРЕЗАПУСТИТЬ',
        'btn_start_server':    'Запустить сервер',
        'btn_stop_server':     'Остановить сервер',
        'btn_restart_server':  'Перезапустить сервер',
        'server_console':      'Консоль сервера',
        'command_placeholder': 'Введите команду сервера…',
        'ph_command':          'Введите команду сервера…',
        'btn_send':            'Отправить',
        'btn_clear':           'Очистить',
        'btn_close':           'Закрыть',

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

        # ── Sandbox Subtabs ──
        'subtab_zombies':          '🧟 Зомби и популяция',
        'subtab_loot':             '📦 Редкость лута',
        'subtab_world':            '⏱ Мир и время',
        'subtab_vehicles':         '🚗 Транспорт',
        'subtab_character':        '👤 Персонаж и навыки',
        'subtab_mods':             '🧩 Настройки модов',

        # ── Detailed Sandbox Labels ──
        'group_zombie_advanced':   'Расширенная популяция (ZombieConfig)',
        'group_loot_categories':   '10 категорий редкости лута',
        'group_loot_respawn':      'Респаун лута и коммуникации',
        'lbl_loot_weapons':        'Оружие ближнего боя:',
        'lbl_loot_ranged_weapons': 'Огнестрельное оружие:',
        'lbl_loot_ammo':           'Патроны и магазины:',
        'lbl_loot_food':           'Свежая еда:',
        'lbl_loot_canned_food':    'Консервы и долгохранящаяся еда:',
        'lbl_loot_medical':        'Медикаменты:',
        'lbl_loot_literature':     'Книги, журналы и рецепты:',
        'lbl_loot_survival':       'Снаряжение для выживания:',
        'lbl_loot_mechanics':      'Автозапчасти и механика:',
        'lbl_loot_other':          'Прочий лут:',
        'lbl_max_items_respawn':   'Макс. предметов в ящике для респауна:',
        'lbl_construction_respawn':'Постройки блокируют респаун лута:',
        'lbl_pop_start_mult':      'Начальный множитель популяции:',
        'lbl_pop_peak_mult':       'Пиковый множитель популяции:',
        'lbl_pop_peak_day':        'День пика популяции:',
        'lbl_respawn_hours':       'Период респауна зомби (часов):',
        'lbl_respawn_unseen_hours':'Часов без игроков для респауна:',
        'lbl_respawn_fraction':    'Доля возрождаемых зомби:',
        'lbl_redistribute_hours':  'Период миграции зомби (часов):',
        'lbl_rally_group_size':    'Размер орды зомби:',
        'lbl_rally_group_radius':  'Радиус орды:',
        'lbl_helicopter':          'Событие с вертолётом:',
        'lbl_meta_event':          'События (выстрелы, крики):',
        'lbl_sleeping_event':      'События во время сна:',
        'lbl_erosion_speed':       'Скорость эрозии (природы):',
        'lbl_erosion_days':        'Дней до максимального зарастания:',
        'lbl_gas_chance':          'Шанс бензина на заправках и в авто:',
        'lbl_initial_gas':         'Начальный уровень топлива в баке:',
        'lbl_gas_consumption':     'Множитель расхода топлива:',
        'lbl_car_condition':       'Общее состояние транспорта:',
        'lbl_traffic_jam':         'Пробки и заторы на дорогах:',
        'lbl_car_alarm':           'Сигнализации в авто:',
        'lbl_crash_damage':        'Урон игроку при автокатастрофе:',
        'lbl_plant_resilience':    'Выносливость растений:',
        'lbl_plant_abundance':     'Урожайность растений:',
        'btn_mod_options_quick':   '⚙️ Настройки модов в песочнице',
        'group_map_order':         '🗺️ Порядок карт (моды ДО Muldraugh, KY)',
        'btn_move_map_up':         '🔼 Вверх',
        'btn_move_map_down':       '🔽 Вниз',
        'btn_optimize_map_order':  '✨ Оптимизировать порядок карт',
        'lbl_mod_search':          'Поиск настроек модов:',
        'ph_mod_search':           'Введите название или описание параметра...',
        'no_mod_options_found':    'В SandboxVars.lua пока нет секций модов.\nМоды с собственными настройками (Common Sense, More Traits, VFE и др.) появятся здесь автоматически после первого запуска сервера или применения конфигурации.',

        # ── Install tab ───────────────────────────────────────────
        'group_server_version': 'Версии и бета-версии',
        'lbl_selected_version_title': 'Выбранная версия',
        'lbl_selected_version_note': 'Эти версии предоставлены разработчиком игры, и некоторые из них могут быть нестабильными тестовыми сборками или старыми версиями. Будьте осторожны.',
        'col_branch_name_desc': 'НАЗВАНИЕ И ОПИСАНИЕ',
        'col_branch_last_update': 'ПОСЛЕДНЕЕ ОБНОВЛЕНИЕ',
        'lbl_hidden_betas': 'Скрытые версии',
        'lbl_hidden_betas_desc': 'Введите код доступа, чтобы разблокировать скрытую версию игры или бета-версию:',
        'btn_check_beta_code': 'Проверить код',
        'placeholder_beta_code': 'Код доступа или пароль ветки',
        'placeholder_hidden_branch': 'Название ветки (необязательно)',
        'beta_code_success': '✓ Код доступа принят! Ветка разблокирована.',
        'beta_code_empty': 'Пожалуйста, введите код доступа.',
        'lbl_server_version':   'Выберите версию:',
        'ver_stable':           'Стандартная общедоступная версия',
        'ver_b42_unstable':     'unstable',
        'ver_custom':           'Другая ветка (Custom Beta Branch)…',
        'lbl_custom_branch':    'Название ветки:',
        'lbl_ready_install':  'Готов к установке',
        'btn_install_server': '📥 Установить сервер',
        'btn_update_server':  '🔄 Обновить сервер',
        'confirm_update':     'Обновить и проверить файлы сервера Project Zomboid в:\n{path}?\n\nВыбранная версия / ветка: {branch}',
        'update_complete':    'Сервер обновлён',
        'update_complete_msg':'Файлы выделенного сервера Project Zomboid успешно обновлены и проверены!',
        'btn_import_mods':    '📥 Импорт списка модов',
        'btn_export_mods':    '📤 Экспорт списка модов',

        # ── Buttons ───────────────────────────────────────────────
        'btn_save_settings':   '💾 Сохранить настройки',
        'btn_reload_settings': '🔄 Перезагрузить настройки',
        'btn_save_sandbox':    '💾 Сохранить Sandbox',
        'btn_reload':          '🔄 Обновить',
        'btn_save_mods':       '💾 Сохранить и применить моды',
        'btn_analyze_mods':    '🔍 Анализ и зависимости модов',
        'btn_add_mod':         '➕ Добавить мод',
        'btn_import_collection': '📦 Импорт коллекции / пака Steam',
        'btn_refresh_versions': '🔄 Обновить версии из Steam',
        'btn_remove_mod':      '➖ Удалить выбранный',
        'btn_clear_mods':      '🗑️ Удалить все',
        'btn_browse':          'Обзор…',
        'msg_mod_analysis_title': 'Анализ модов и зависимостей',
        'msg_mod_analysis_ok': 'Все зависимости модов проверены, порядок загрузки оптимизирован!',
        'msg_collection_prompt': 'Введите ссылку или ID коллекции Steam Workshop (например, https://steamcommunity.com/sharedfiles/filedetails/?id=3818199903):',
        'msg_collection_success': 'Коллекция успешно импортирована! Добавлено/обновлено {added} модов.',

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
        'info':                     'Информация',
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
            'Версия 1.3.1 (MVP)\n\n'
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

        # Presets
        'preset_label': 'Предустановка сложности:',
        'preset_select': '-- Выберите пресет --',
        'preset_beginner': 'Начинающий (Легкий)',
        # Presets
        'preset_label': 'Пресет / Сложность:',
        'preset_select': '-- Выберите пресет --',
        'preset_beginner': 'Начинающий (Легкий)',
        'preset_survival': 'Выживание (Стандарт)',
        'preset_hardcore': 'Хардкор (Сложный)',
        'preset_horde': 'Орда Zomboid',
        'preset_builder': 'Строитель (Мирные зомби)',
        'preset_applied': 'Пресет "{name}" успешно применен!',

        # Backups
        'btn_manage_backups': 'Управление бэкапами',
        'backup_title': 'Резервные копии конфигураций',
        'btn_restore': 'Восстановить выбранную',
        'backup_restored': 'Конфигурация успешно восстановлена!',
        'no_backups_found': 'Резервных копий для этого сервера не найдено.',

        # Live Players
        'live_players': 'Онлайн-игроки',
        'lbl_online_players': '👥 Игроки онлайн ({count})',
        'btn_kick': '👢 Кик',
        'btn_ban': '🚫 Бан',
        'btn_teleport': '🌀 Телепорт',
        'btn_admin': '👑 Админ',
        'btn_whitelist': '📜 В вайтлист',
        'btn_refresh_players': '🔄 Обновить',
        'no_players_online': 'Нет игроков онлайн',
        'player_actions': 'Действия с игроком',
        'kick_reason_prompt': 'Укажите причину кика:',
        'ban_reason_prompt': 'Укажите причину бана:',
        'teleport_target_prompt': 'Телепортировать {player} к какому игроку?',
        'player_kicked_success': 'Игрок {player} кикнут с сервера',
        'player_banned_success': 'Игрок {player} заблокирован (бан)',
        'player_whitelist_success': 'Игрок {player} добавлен в вайтлист',
        'player_admin_success': 'Игроку {player} выданы права администратора',

        # Watchdog
        'chk_watchdog': 'Авто-перезапуск при краше (Watchdog)',
        'watchdog_tooltip': 'Следит за процессом сервера и автоматически перезапускает его при аварийном завершении/сбое',
        'watchdog_crashed': '⚠️ Watchdog обнаружил сбой сервера. Перезапуск через {sec}с...',

        # Search
        'search_sandbox_ph': 'Поиск по всем категориям настроек...',
        'search_mods_ph': 'Поиск по установленным модам...',
        'search_matches_found': 'Найдено: {count}',

        # Backup Manager GUI
        'backup_mgr_title': 'Менеджер бэкапов мира и конфигурации',
        'btn_create_backup': 'Создать бэкап сейчас',
        'btn_restore_backup': 'Восстановить выбранный бэкап',
        'btn_delete_backup': 'Удалить бэкап',
        'btn_open_backup_folder': 'Открыть папку бэкапов',
        'col_filename': 'Архив бэкапа',
        'col_size': 'Размер (МБ)',
        'col_date': 'Дата создания',
        'prompt_backup_tag': 'Введите метку / заметку к бэкапу (напр. перед_вайпом):',
        'backup_created_success': 'Бэкап успешно создан:\n{path}',
        'backup_restore_confirm': 'Вы уверены, что хотите восстановить бэкап "{name}"?\nТекущее сохранение мира и конфигурация будут перезаписаны!',
        'backup_restore_success': 'Бэкап успешно восстановлен!\nПожалуйста, перезагрузите настройки или перезапустите сервер.',
        'backup_delete_confirm': 'Удалить архив бэкапа "{name}"?',
        'backup_delete_success': 'Бэкап успешно удален.',

        # Web Dashboard
        'btn_web_dashboard': 'Веб-панель',
        'web_dashboard_title': 'Веб-панель (Удаленный доступ VPS)',
        'web_dashboard_running': 'Веб-панель запущена по адресу:\n{url}\n\nОткрыть в браузере?',
        'web_dashboard_running_btn': 'Веб-панель (Онлайн: 8080)',
        'web_dashboard_stopped': 'Веб-панель остановлена.',
        'web_dashboard_tooltip': 'Включить локальный веб-сервер FastAPI для управления сервером через браузер или со смартфона',
        'web_security_title': 'Безопасность веб-панели',
        'web_security_desc': 'Для защиты от сетевых сканеров и попыток взлома выберите нестандартный порт и пароль администратора для веб-панели.',
        'web_port_label': 'Порт веб-панели (1024 - 65535):',
        'web_pw_label': 'Пароль администратора:',
        'web_firewall_label': 'Автоматически открыть этот порт в Брандмауэре Windows',
        'btn_random_port': '🎲 Случайный порт',
        'btn_gen_pw': '🎲 Сгенерировать пароль',
        'btn_save_start_web': 'Сохранить и запустить',

        # Tray
        'tray_show': 'Показать приложение',
        'tray_hide': 'Свернуть в трей',
        'tray_start': 'Запустить сервер',
        'tray_stop': 'Остановить сервер',
        'tray_exit': 'Выход',
        'tray_server_started': 'Сервер успешно запущен.',
        'tray_server_stopped': 'Сервер остановлен.',
        'tray_minimized': 'Приложение свернуто в системный трей.',

        # Diagnostics & Warnings
        'error_disk_space': 'Недостаточно свободного места на диске! Требуется минимум {required} ГБ, свободно: {available:.2f} ГБ.',
        'warn_ports_in_use': 'Следующие сетевые порты уже заняты другим приложением: {ports}.\nВы уверены, что хотите запустить сервер?',
        'first_run_title': 'Сервер PZ не найден',
        'first_run_msg': 'Сервер Project Zomboid не обнаружен на компьютере.\n\nХотите автоматически скачать и установить SteamCMD и сервер (~3 ГБ) в папку по умолчанию?',
        'server_detected_title': 'Обнаружен существующий сервер',
        'server_detected_msg': 'Обнаружен установленный сервер Project Zomboid по адресу:\n{path}\n\nИспользовать эту папку для работы?',
        # ── Additional Vehicle & Preset translations ──
        'lbl_enable_vehicles':      'Включить транспорт в мире:',
        'lbl_survivor_vehicles':    'Машины недавних выживших:',
        'lbl_locked_cars':          'Шанс закрытых дверей авто:',
        'lbl_zombie_attraction':    'Привлечение зомби шумом двигателя:',
        'lbl_siren_shutoff':        'Время звучания сирен (ч, 0=до разряда):',
        'lbl_car_damage_impact':    'Урон автомобилю при столкновении:',
        'lbl_player_hit_damage':    'Урон пешеходу при наезде авто:',
        'deadly':                   'Смертельный',
        'full':                     'Полный бак',
        'btn_save_custom_preset':   '➕ Сохранить пресет...',
        'btn_delete_custom_preset': '🗑️ Удалить пресет',
        'lbl_custom_presets':       'Пользовательские пресеты',
        'prompt_custom_preset_name':'Введите название для вашего пресета:',
        'preset_saved':             'Пресет "{name}" успешно сохранен!',
        'preset_deleted':           'Пресет "{name}" удален.',
        'confirm_delete_preset':    'Вы действительно хотите удалить пресет "{name}"?',
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

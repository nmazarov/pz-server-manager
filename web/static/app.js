
// ── Custom Named Sandbox Presets Management ──────────────────────────────
let customSandboxPresets = {};
try {
  customSandboxPresets = JSON.parse(localStorage.getItem('pz_custom_sandbox_presets') || '{}');
} catch (e) {
  customSandboxPresets = {};
}

function populatePresetDropdown() {
  const sel = document.getElementById('sandbox-preset');
  if (!sel) return;
  const currentVal = sel.value;

  sel.innerHTML = `
    <option value="">${t('preset_default')}</option>
    <optgroup label="${currentLang === 'ru' ? '📦 Стандартные пресеты' : '📦 Built-in Presets'}">
      <option value="apocalypse">${t('preset_apocalypse')}</option>
      <option value="survivor">${t('preset_survivor')}</option>
      <option value="builder">${t('preset_builder')}</option>
    </optgroup>
  `;

  const customNames = Object.keys(customSandboxPresets);
  if (customNames.length > 0) {
    const grp = document.createElement('optgroup');
    grp.label = currentLang === 'ru' ? '⭐ Пользовательские пресеты' : '⭐ Custom Presets';
    customNames.forEach(name => {
      const opt = document.createElement('option');
      opt.value = 'custom:' + name;
      opt.textContent = '⭐ ' + name;
      grp.appendChild(opt);
    });
    sel.appendChild(grp);
  }

  if (currentVal && Array.from(sel.options).some(o => o.value === currentVal)) {
    sel.value = currentVal;
  }
  updatePresetDeleteBtn();
}

function updatePresetDeleteBtn() {
  const sel = document.getElementById('sandbox-preset');
  const btn = document.getElementById('btn-del-preset');
  if (!btn) return;
  if (sel && sel.value.startsWith('custom:')) {
    btn.style.display = 'inline-flex';
  } else {
    btn.style.display = 'none';
  }
}

function saveCustomPresetPrompt() {
  const promptMsg = (currentLang === 'ru')
    ? 'Введите название для вашего пресета настроек (например: Мой Хардкор, PvP Мир, Лутер):'
    : 'Enter a name for your custom sandbox preset (e.g. My Hardcore, PvP World, Easy Loot):';
  const name = prompt(promptMsg);
  if (!name || !name.trim()) return;
  const trimmed = name.trim();

  // Gather current sandbox UI state
  const presetData = gatherSandboxState();
  customSandboxPresets[trimmed] = presetData;
  localStorage.setItem('pz_custom_sandbox_presets', JSON.stringify(customSandboxPresets));

  // Save to server preferences
  fetch('/api/preferences', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ custom_sandbox_presets: customSandboxPresets })
  }).catch(() => {});

  populatePresetDropdown();
  const sel = document.getElementById('sandbox-preset');
  if (sel) sel.value = 'custom:' + trimmed;
  updatePresetDeleteBtn();

  showToast((currentLang === 'ru')
    ? `⭐ Пресет «${trimmed}» успешно сохранен!`
    : `⭐ Preset "${trimmed}" successfully saved!`
  );
}

function deleteCustomPreset() {
  const sel = document.getElementById('sandbox-preset');
  if (!sel || !sel.value.startsWith('custom:')) return;
  const presetName = sel.value.replace('custom:', '');
  const confirmMsg = (currentLang === 'ru')
    ? `Вы действительно хотите удалить пресет «${presetName}»?`
    : `Are you sure you want to delete preset "${presetName}"?`;

  if (confirm(confirmMsg)) {
    delete customSandboxPresets[presetName];
    localStorage.setItem('pz_custom_sandbox_presets', JSON.stringify(customSandboxPresets));
    fetch('/api/preferences', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ custom_sandbox_presets: customSandboxPresets })
    }).catch(() => {});

    populatePresetDropdown();
    sel.value = '';
    updatePresetDeleteBtn();
    showToast((currentLang === 'ru')
      ? `🗑️ Пресет «${presetName}» удален`
      : `🗑️ Preset "${presetName}" deleted`
    );
  }
}

function setSpeedLimitPreset(val) {
  const el = document.getElementById('sb-SpeedLimit');
  if (el) el.value = val;
  const iniEl = document.getElementById('ini-SpeedLimit');
  if (iniEl) iniEl.value = val;
  showToast((currentLang === 'ru')
    ? `🚗 Лимит скорости: ${val === 0 ? 'Без ограничений' : val + ' км/ч'}`
    : `🚗 Speed limit: ${val === 0 ? 'No limit' : val + ' km/h'}`
  );
}

function gatherSandboxState() {
  const getInt = (id, fallback) => {
    const el = document.getElementById(id);
    return el ? (parseInt(el.value) || fallback) : fallback;
  };
  const getFloat = (id, fallback) => {
    const el = document.getElementById(id);
    return el ? (parseFloat(el.value) || fallback) : fallback;
  };
  const getBool = (id, fallback) => {
    const el = document.getElementById(id);
    return el ? el.checked : fallback;
  };

  const data = {
    ZombieLore: {
      Speed: getInt('sb-ZombieLore-Speed', 2),
      Strength: getInt('sb-ZombieLore-Strength', 2),
      Toughness: getInt('sb-ZombieLore-Toughness', 2),
      Transmission: getInt('sb-ZombieLore-Transmission', 1),
      Mortality: getInt('sb-ZombieLore-Mortality', 5),
      Reanimate: getInt('sb-ZombieLore-Reanimate', 3),
      Cognition: getInt('sb-ZombieLore-Cognition', 3),
      Memory: getInt('sb-ZombieLore-Memory', 2),
      Sight: getInt('sb-ZombieLore-Sight', 2),
      Hearing: getInt('sb-ZombieLore-Hearing', 2),
      Smell: getInt('sb-ZombieLore-Smell', 2),
      ActiveOnly: getInt('sb-ZombieLore-ActiveOnly', 1),
      Decomposition: getInt('sb-ZombieLore-Decomposition', 2),
      TriggerHouseAlarm: getBool('sb-ZombieLore-TriggerHouseAlarm', false),
      ThumpOnConstruction: getBool('sb-ZombieLore-ThumpOnConstruction', true),
      ThumpNoChasing: getBool('sb-ZombieLore-ThumpNoChasing', false),
      ZombiesDragDown: getBool('sb-ZombieLore-ZombiesDragDown', true),
      ZombiesFenceLunge: getBool('sb-ZombieLore-ZombiesFenceLunge', true)
    },
    ZombieConfig: {
      PopulationMultiplier: getFloat('sb-ZombieConfig-PopulationMultiplier', 1.0),
      PopulationPeakMultiplier: getFloat('sb-ZombieConfig-PopulationPeakMultiplier', 1.5),
      PopulationPeakDay: getInt('sb-ZombieConfig-PopulationPeakDay', 28),
      RespawnHours: getInt('sb-ZombieConfig-RespawnHours', 72),
      RespawnMultiplier: getFloat('sb-ZombieConfig-RespawnMultiplier', 0.1),
      RallyGroupSize: getInt('sb-ZombieConfig-RallyGroupSize', 20),
      RallyGroupRadius: getInt('sb-ZombieConfig-RallyGroupRadius', 3),
      RedistributeHours: getInt('sb-ZombieConfig-RedistributeHours', 12)
    },
    Loot: {
      Weapon: getInt('sb-Loot-Weapon', 3),
      RangedWeapon: getInt('sb-Loot-RangedWeapon', 3),
      Ammo: getInt('sb-Loot-Ammo', 3),
      Food: getInt('sb-Loot-Food', 3),
      CannedFood: getInt('sb-Loot-CannedFood', 3),
      Medical: getInt('sb-Loot-Medical', 3),
      Literature: getInt('sb-Loot-Literature', 3),
      SurvivalGears: getInt('sb-Loot-SurvivalGears', 3),
      Mechanics: getInt('sb-Loot-Mechanics', 3),
      Other: getInt('sb-Loot-Other', 3)
    },
    LootRespawn: getInt('sb-LootRespawn', 1),
    MaxItemsForRespawn: getInt('sb-MaxItemsForRespawn', 4),
    ConstructionPreventsLootRespawn: getBool('sb-ConstructionPreventsLootRespawn', true),
    WaterShut: getInt('sb-WaterShut', 2),
    ElecShut: getInt('sb-ElecShut', 2),

    DayLength: getInt('sb-DayLength', 3),
    StartYear: getInt('sb-StartYear', 1),
    StartMonth: getInt('sb-StartMonth', 7),
    StartDay: getInt('sb-StartDay', 9),
    StartTime: getInt('sb-StartTime', 2),
    Temperature: getInt('sb-Temperature', 3),
    Rain: getInt('sb-Rain', 3),
    ErosionSpeed: getInt('sb-ErosionSpeed', 3),
    ErosionDays: getInt('sb-ErosionDays', 100),
    Helicopter: getInt('sb-Helicopter', 2),
    MetaEvent: getInt('sb-MetaEvent', 2),
    NightDarkness: getInt('sb-NightDarkness', 3),
    TimeSinceApo: getInt('sb-TimeSinceApo', 1),
    NatureAbundance: getInt('sb-NatureAbundance', 3),
    FireSpread: getBool('sb-FireSpread', true),

    // Vehicles
    EnableVehicles: getBool('sb-EnableVehicles', true),
    CarSpawnRate: getInt('sb-CarSpawnRate', 3),
    CarCondition: getInt('sb-CarCondition', 3),
    RecentlySurvivorVehicles: getInt('sb-RecentlySurvivorVehicles', 3),
    LockedCar: getInt('sb-LockedCar', 4),
    VehicleEasyUse: getBool('sb-VehicleEasyUse', false),
    TrafficJam: getBool('sb-TrafficJam', true),
    SpeedLimit: getInt('sb-SpeedLimit', 70),
    ZombieAttractionMultiplier: getFloat('sb-ZombieAttractionMultiplier', 1.0),
    ChanceHasGas: getInt('sb-ChanceHasGas', 3),
    InitialGas: getInt('sb-InitialGas', 2),
    CarGasConsumption: getFloat('sb-CarGasConsumption', 1.0),
    CarAlarm: getInt('sb-CarAlarm', 3),
    SirenShutoffHours: getFloat('sb-SirenShutoffHours', 0.0),
    CarDamageOnImpact: getInt('sb-CarDamageOnImpact', 3),
    DamageToPlayerFromHitByCar: getInt('sb-DamageToPlayerFromHitByCar', 3),
    PlayerDamageFromCarCrash: getBool('sb-PlayerDamageFromCarCrash', true),

    // Character & Farming
    XpMultiplier: getFloat('sb-XpMultiplier', 1.0),
    CharacterFreePoints: getInt('sb-CharacterFreePoints', 0),
    StatsDecrease: getInt('sb-StatsDecrease', 3),
    Nutrition: getBool('sb-Nutrition', true),
    FarmingSpeed: getInt('sb-FarmingSpeed', 3),
    PlantResilience: getInt('sb-PlantResilience', 3),
    PlantAbundance: getInt('sb-PlantAbundance', 3),
    GeneratorSpawning: getInt('sb-GeneratorSpawning', 3),
    GeneratorFuelConsumption: getFloat('sb-GeneratorFuelConsumption', 1.0)
  };
  return data;
}

function restoreSandboxState(data) {
  const setVal = (id, v) => {
    const el = document.getElementById(id);
    if (el && v !== undefined && v !== null) {
      if (el.type === 'checkbox') el.checked = Boolean(v);
      else el.value = v;
    }
  };

  if (data.ZombieLore) {
    for (const [k, v] of Object.entries(data.ZombieLore)) {
      setVal('sb-ZombieLore-' + k, v);
    }
  }
  if (data.ZombieConfig) {
    for (const [k, v] of Object.entries(data.ZombieConfig)) {
      setVal('sb-ZombieConfig-' + k, v);
    }
  }
  if (data.Loot) {
    for (const [k, v] of Object.entries(data.Loot)) {
      setVal('sb-Loot-' + k, v);
    }
  }

  for (const [k, v] of Object.entries(data)) {
    if (typeof v !== 'object') {
      setVal('sb-' + k, v);
    }
  }
}


// ── Internationalization (Bilingual RU / EN System) ───────────────
let currentLang = localStorage.getItem('pz_lang') || 'ru';

const TRANSLATIONS_WEB = {
  ru: {
    app_title: "Project Zomboid Server Manager",
    app_subtitle: "Тактическая веб-панель • Готова к Build 41 & 42",
    btn_share: "📋 Поделиться",
    btn_backups: "📦 Бэкапы",
    btn_logout: "🚪 Выйти",
    tab_server: "🎮 Управление",
    tab_settings: "⚙️ Настройки (INI)",
    tab_sandbox: "🧟 Sandbox",
    tab_mods: "🧩 Моды",
    tab_install: "📦 Установка & Обновления",
    tab_backups: "💾 Бэкапы",

    status_offline: "СЕРВЕР ОСТАНОВЛЕН",
    status_offline_sub: "Нажмите «Запустить сервер» для старта",
    status_launching: "ЗАПУСК И ЗАГРУЗКА...",
    status_launching_sub: "Инициализация мира и загрузка модов Steam",
    status_ready: "СЕРВЕР ОНЛАЙН И ГОТОВ К ИГРЕ",
    status_ready_sub: "Игроки могут подключаться по IP и портам сервера",
    status_unknown: "СТАТУС НЕИЗВЕСТЕН",
    status_unknown_sub: "Ожидание ответа от серверного процесса",
    copy_conn: "📋 Скопировать",
    copied_toast: "Адрес подключения скопирован в буфер обмена!",

    group_server_control: "⚡ Управление сервером",
    lbl_server_name: "Имя сервера:",
    lbl_srv_ram: "Выделение ОЗУ (RAM):",
    btn_start: "▶ Запустить сервер",
    btn_stop: "⏹ Остановить",
    btn_restart: "🔄 Перезапустить",
    chk_auto_backup: "📦 Авто-бэкап мира перед запуском",
    chk_watchdog: "🛡️ Watchdog: авто-перезапуск при падении",
    quick_actions: "⚡ Быстрые команды:",
    qa_save: "💾 Сохранить",
    qa_rain: "🌧️ Дождь",
    qa_chopper: "🚁 Вертолет",
    qa_broadcast: "📢 Объявление",

    terminal_title: "📟 Интерактивная консоль сервера",
    chk_autoscroll: "Автопрокрутка",
    btn_clear: "Очистить",
    ph_command: "Введите команду (например: save, chopper, players, servermsg 'текст')...",
    btn_send: "Отправить",
    players_title: "👥 Игроки онлайн",
    empty_players: "Нет игроков на сервере",
    btn_kick: "Кикнуть",
    btn_ban: "Забанить",

    settings_title: "⚙️ Настройки сервера (servertest.ini)",
    btn_save_settings: "💾 Сохранить настройки",
    group_basic: "📌 Основные параметры",
    lbl_public_name: "Название сервера (PublicName):",
    lbl_public_desc: "Описание сервера (PublicDescription):",
    lbl_password: "Пароль сервера (Password):",
    lbl_max_players: "Максимум игроков (MaxPlayers):",
    lbl_map: "Карта мира (Map):",
    lbl_welcome_msg: "Приветствие сервера (ServerWelcomeMessage):",
    group_network: "🌐 Сеть и RCON",
    lbl_game_port: "Игровой порт (DefaultPort - UDP):",
    lbl_direct_port: "Прямой порт (UDPPort):",
    lbl_steam_port1: "Steam порт 1 (SteamPort1):",
    lbl_steam_port2: "Steam порт 2 (SteamPort2):",
    lbl_rcon_port: "RCON порт (RCONPort - TCP):",
    lbl_rcon_password: "Пароль RCON / Администратора:",
    chk_open: "Публичный сервер (Open)",
    chk_public: "Отображать в публичном списке Steam (Public)",
    group_gameplay: "⚔️ Игровой процесс",
    chk_pvp: "Разрешить PvP (PVP)",
    chk_pause_empty: "Пауза когда сервер пуст (PauseEmpty)",
    chk_allow_coop: "Разрешить кооператив (AllowCoop)",
    chk_sleep_allowed: "Сон разрешен (SleepAllowed)",
    chk_sleep_needed: "Сон необходим (SleepNeeded)",
    chk_announce_death: "Оповещать в чате о смерти (AnnounceDeath)",
    chk_no_fire: "Отключить распространение огня (NoFire)",
    chk_allow_destruction: "Разрушение стен кувалдой",
    lbl_drop_on_death: "Потеря вещей при смерти (DropOnDeath):",
    lbl_spawn_point: "Координаты спавна (SpawnPoint):",
    group_safehouses: "🏠 Убежища и Безопасность",
    chk_player_safehouse: "Разрешить игрокам создавать убежища (PlayerSafehouse)",
    chk_admin_safehouse: "Только админские убежища (AdminSafehouse)",
    chk_safehouse_trespassing: "Разрешить вход посторонним в убежище",
    chk_safehouse_fire: "Разрешить огонь в убежищах",
    chk_safehouse_loot: "Разрешить лутать чужие убежища",
    chk_safehouse_respawn: "Разрешить респавн в убежище",
    chk_voice_enable: "Включить голосовой VOIP чат (VoiceEnable)",
    chk_voice_3d: "Позиционный 3D звук голоса",
    chk_global_chat: "Глобальный чат (GlobalChat)",
    lbl_auto_save: "Автосохранение (мин):",
    lbl_speed_limit: "Лимит скорости авто (км/ч):",
    group_security: "🛡️ Безопасность и Авторизация",
    chk_auto_whitelist: "Авто-добавление в белый список (AutoCreateUserInWhiteList)",
    chk_safety_system: "Система безопасности / защита спавна (SafetySystem)",
    chk_show_safety: "Показывать индикаторы защиты (ShowSafety)",
    chk_display_username: "Отображать никнеймы игроков над головой (DisplayUserName)",
    chk_lua_checksum: "Проверка контрольных сумм Lua (DoLuaChecksum)",
    chk_deny_same_id: "Запрет одновременного входа с одного Steam ID",
    lbl_max_accounts: "Макс. аккаунтов на игрока (0 = без ограничений):",
    group_admin: "🎛️ Администрирование и Лимиты",
    lbl_voice_min: "Мин. дистанция голоса:",
    lbl_voice_max: "Макс. дистанция голоса:",
    lbl_backups_count: "Количество резервных копий:",
    lbl_backups_period: "Период бэкапов (ч, 0=при старте):",
    lbl_fast_forward: "Ускорение времени (x):",
    lbl_corpse_removal: "Часов до удаления трупов:",

    sandbox_title: "🧟 Параметры песочницы (SandboxVars.lua)",
    btn_save_sandbox: "💾 Сохранить Sandbox",
    preset_default: "-- Пресеты сложности --",
    preset_apocalypse: "💀 Апокалипсис",
    preset_survivor: "🏕️ Выживание",
    preset_builder: "🏗️ Строитель",
    subtab_zombies: "🧟 Зомби и Популяция",
    subtab_loot: "📦 Ресурсы и Лут",
    subtab_world: "🌍 Мир и Время",
    subtab_vehicles: "🚗 Транспорт",
    subtab_character: "👤 Персонаж и Навыки",
    subtab_mods: "🧩 Настройки модов",

    sprinters: "Спринтеры (Sprinters)",
    fast_shamblers: "Быстрые ходячие (Fast Shamblers)",
    shamblers: "Медленные ходячие (Shamblers)",
    random: "Случайно (Random)",
    superhuman: "Сверхчеловеческая",
    normal: "Обычная / Нормально",
    weak: "Слабая",
    tough: "Высокая",
    fragile: "Хрупкая",
    blood_saliva: "Кровь и слюна (Blood + Saliva)",
    saliva_only: "Только слюна / укус (Saliva Only)",
    everyone_infected: "Все заражены (Everyone's Infected)",
    none: "Отключена / Нет",
    instant: "Мгновенно",
    slow: "Медленное",
    fast: "Быстрое",
    disabled: "Отключено",
    extremely_rare: "Крайне редко",
    rare: "Редко",
    common: "Часто",
    abundant: "Изобилие",
    never: "Никогда",
    sometimes: "Иногда",
    often: "Часто",
    pitch_black: "Кромешная тьма",
    dark: "Тёмная",
    bright: "Светлая",
    very_abundant: "Очень богатые",
    scarce: "Скудные",
    very_scarce: "Очень скудные",
    months_0_3: "0–3 месяца",
    months_3_6: "3–6 месяцев",
    months_6_12: "6–12 месяцев",
    several_years: "Несколько лет",
    many_years: "Много лет",

    mods_title: "🧩 Мастер модификаций Workshop",
    btn_check_mods: "🔍 Проверить актуальность",
    btn_analyze_mods: "⚡ Анализ зависимостей",
    btn_save_mods: "💾 Сохранить список",
    ph_mod_input: "Введите Workshop ID или ссылку на мод/коллекцию Steam...",
    btn_add_mod: "➕ Добавить мод",
    mod_packs_label: "🎁 Готовые наборы:",
    pack_vehicles: "🚗 Автопарк KI5",
    pack_weapons: "⚔️ Оружие Brita",
    pack_qol: "🖥️ Удобный QoL",
    pack_hardcore: "🧟 Хардкор",
    btn_clear_mods: "🧹 Очистить все",

    install_title: "📦 Установка и обновление игрового сервера (SteamCMD)",
    btn_check_update: "🔍 Проверить обновления в Steam",
    install_desc: "Выберите желаемую ветку обновления Project Zomboid Dedicated Server (Steam AppID 380870).",
    col_branch_name: "НАЗВАНИЕ И ОПИСАНИЕ",
    col_branch_update: "ПОСЛЕДНЕЕ ОБНОВЛЕНИЕ",
    lbl_hidden_branch: "🔑 Скрытая версия:",
    ph_hidden_branch: "Название ветки (необязательно)",
    ph_access_code: "Код доступа или пароль",
    btn_check_code: "Проверить код",
    btn_do_install: "🚀 Установить / Обновить сервер",

    backups_title: "💾 Резервные копии мира и конфигураций",
    btn_create_backup: "📦 Создать бэкап сейчас",

    toast_settings_saved: "💾 Настройки сервера успешно сохранены!",
    toast_sandbox_saved: "💾 Параметры Sandbox успешно сохранены!",
    toast_mods_saved: "💾 Список модов сохранен!",
    // Vehicles Extended
    group_vehicle_spawn: "🚗 Появление и Состояние транспорта",
    group_vehicle_physics: "⛽ Скорость, Топливо и Физика",
    chk_enable_vehicles: "Включить транспорт в игровом мире (EnableVehicles)",
    lbl_survivor_vehicles: "Машины недавних выживших с лутом (RecentlySurvivorVehicles):",
    lbl_locked_cars: "Шанс запертых дверей авто (LockedCar):",
    chk_vehicle_easy_use: "Легкое управление (без ключа зажигания и навыка взлома)",
    chk_traffic_jam: "Заторы и пробки из разбитых машин на дорогах",
    lbl_zombie_attraction: "Привлечение зомби шумом двигателя (ZombieAttractionMultiplier):",
    lbl_siren_shutoff: "Время звучания сирен в часах (SirenShutoffHours, 0=до разряда):",
    lbl_car_damage_impact: "Урон автомобилю при столкновении (CarDamageOnImpact):",
    lbl_player_hit_damage: "Урон пешеходу при наезде автомобилем (DamageToPlayerFromHitByCar):",
    chk_crash_damage: "Урон игроку при аварии на машине",
    full: "Полный бак",
    deadly: "Смертельный",
    toast_backup_created: "📦 Резервная копия успешно создана!"
  },
  en: {
    app_title: "Project Zomboid Server Manager",
    app_subtitle: "Tactical Web Dashboard • Build 41 & 42 Ready",
    btn_share: "📋 Share",
    btn_backups: "📦 Backups",
    btn_logout: "🚪 Logout",
    tab_server: "🎮 Server Control",
    tab_settings: "⚙️ Server Settings (INI)",
    tab_sandbox: "🧟 Sandbox",
    tab_mods: "🧩 Mods",
    tab_install: "📦 Install & Updates",
    tab_backups: "💾 Backups",

    status_offline: "SERVER STOPPED",
    status_offline_sub: "Click 'Start Server' to launch",
    status_launching: "STARTING & LOADING...",
    status_launching_sub: "Initializing world and downloading Steam workshop items",
    status_ready: "SERVER ONLINE & READY TO PLAY",
    status_ready_sub: "Players can connect using server IP and game ports",
    status_unknown: "STATUS UNKNOWN",
    status_unknown_sub: "Waiting for server process feedback",
    copy_conn: "📋 Copy Address",
    copied_toast: "Connection address copied to clipboard!",

    group_server_control: "⚡ Server Controls",
    lbl_server_name: "Server Name:",
    lbl_srv_ram: "RAM Allocation:",
    btn_start: "▶ Start Server",
    btn_stop: "⏹ Stop",
    btn_restart: "🔄 Restart",
    chk_auto_backup: "📦 Auto-backup world before launch",
    chk_watchdog: "🛡️ Watchdog: auto-restart on crash",
    quick_actions: "⚡ Quick Commands:",
    qa_save: "💾 Save World",
    qa_rain: "🌧️ Toggle Rain",
    qa_chopper: "🚁 Spawn Helicopter",
    qa_broadcast: "📢 Broadcast Msg",

    terminal_title: "📟 Interactive Server Console",
    chk_autoscroll: "Auto-scroll",
    btn_clear: "Clear",
    ph_command: "Enter command (e.g. save, chopper, players, servermsg 'text')...",
    btn_send: "Send",
    players_title: "👥 Players Online",
    empty_players: "No players connected to the server",
    btn_kick: "Kick",
    btn_ban: "Ban",

    settings_title: "⚙️ Server Settings (servertest.ini)",
    btn_save_settings: "💾 Save Settings",
    group_basic: "📌 Basic Parameters",
    lbl_public_name: "Server Name (PublicName):",
    lbl_public_desc: "Description (PublicDescription):",
    lbl_password: "Server Password (Password):",
    lbl_max_players: "Max Players (MaxPlayers):",
    lbl_map: "World Map (Map):",
    lbl_welcome_msg: "Welcome Message (ServerWelcomeMessage):",
    group_network: "🌐 Network & RCON",
    lbl_game_port: "Game Port (DefaultPort - UDP):",
    lbl_direct_port: "Direct Connect Port (UDPPort):",
    lbl_steam_port1: "Steam Port 1 (SteamPort1):",
    lbl_steam_port2: "Steam Port 2 (SteamPort2):",
    lbl_rcon_port: "RCON Port (RCONPort - TCP):",
    lbl_rcon_password: "RCON / Admin Password:",
    chk_open: "Public Server (Open)",
    chk_public: "Display in Steam Public Server Browser (Public)",
    group_gameplay: "⚔️ Gameplay",
    chk_pvp: "Enable PvP (PVP)",
    chk_pause_empty: "Pause when server is empty (PauseEmpty)",
    chk_allow_coop: "Allow Co-op (AllowCoop)",
    chk_sleep_allowed: "Sleep Allowed (SleepAllowed)",
    chk_sleep_needed: "Sleep Needed for Time Passing (SleepNeeded)",
    chk_announce_death: "Announce Player Deaths in Chat (AnnounceDeath)",
    chk_no_fire: "Disable Fire Spread (NoFire)",
    chk_allow_destruction: "Allow Sledgehammer Wall Destruction",
    lbl_drop_on_death: "Drop on Death (DropOnDeath):",
    lbl_spawn_point: "Spawn Point Coordinates (SpawnPoint):",
    group_safehouses: "🏠 Safehouses & Voice",
    chk_player_safehouse: "Allow Player Safehouses (PlayerSafehouse)",
    chk_admin_safehouse: "Admin Safehouses Only (AdminSafehouse)",
    chk_safehouse_trespassing: "Allow Non-members to Enter Safehouse",
    chk_safehouse_fire: "Allow Fire inside Safehouses",
    chk_safehouse_loot: "Allow Looting other Safehouses",
    chk_safehouse_respawn: "Allow Respawn in Safehouse",
    chk_voice_enable: "Enable VOIP Voice Chat (VoiceEnable)",
    chk_voice_3d: "Directional 3D Voice Audio",
    chk_global_chat: "Enable Global Chat (GlobalChat)",
    lbl_auto_save: "Auto-save Interval (minutes):",
    lbl_speed_limit: "Vehicle Speed Limit (km/h):",
    group_security: "🛡️ Security & Authentication",
    chk_auto_whitelist: "Auto-add Players to Whitelist on Connect",
    chk_safety_system: "Enable Safety System (Spawn Protection)",
    chk_show_safety: "Show Safety Indicator on Screen",
    chk_display_username: "Display Usernames Overhead",
    chk_lua_checksum: "Verify Lua File Checksums (DoLuaChecksum)",
    chk_deny_same_id: "Deny Multiple Logins with Same Steam ID",
    lbl_max_accounts: "Max Accounts per Player (0 = unlimited):",
    group_admin: "🎛️ Administration & Limits",
    lbl_voice_min: "VOIP Voice Min Distance:",
    lbl_voice_max: "VOIP Voice Max Distance:",
    lbl_backups_count: "Backup History Count:",
    lbl_backups_period: "Backup Interval (hours, 0=on start):",
    lbl_fast_forward: "Time Fast Forward Multiplier (x):",
    lbl_corpse_removal: "Hours Before Corpse Removal:",

    sandbox_title: "🧟 Sandbox Settings (SandboxVars.lua)",
    btn_save_sandbox: "💾 Save Sandbox",
    preset_default: "-- Difficulty Presets --",
    preset_apocalypse: "💀 Apocalypse",
    preset_survivor: "🏕️ Survivor",
    preset_builder: "🏗️ Builder",
    subtab_zombies: "🧟 Zombies & Population",
    subtab_loot: "📦 Loot & Resources",
    subtab_world: "🌍 World & Time",
    subtab_vehicles: "🚗 Vehicles",
    subtab_character: "👤 Character & Skills",
    subtab_mods: "🧩 Mod Options",

    sprinters: "Sprinters",
    fast_shamblers: "Fast Shamblers",
    shamblers: "Shamblers",
    random: "Random",
    superhuman: "Superhuman",
    normal: "Normal",
    weak: "Weak",
    tough: "Tough",
    fragile: "Fragile",
    blood_saliva: "Blood + Saliva",
    saliva_only: "Saliva Only (Bites)",
    everyone_infected: "Everyone's Infected",
    none: "None / Disabled",
    instant: "Instant",
    slow: "Slow",
    fast: "Fast",
    disabled: "Disabled",
    extremely_rare: "Extremely Rare",
    rare: "Rare",
    common: "Common",
    abundant: "Abundant",
    never: "Never",
    sometimes: "Sometimes",
    often: "Often",
    pitch_black: "Pitch Black",
    dark: "Dark",
    bright: "Bright",
    very_abundant: "Very Abundant",
    scarce: "Scarce",
    very_scarce: "Very Scarce",
    months_0_3: "0–3 Months",
    months_3_6: "3–6 Months",
    months_6_12: "6–12 Months",
    several_years: "Several Years",
    many_years: "Many Years",

    mods_title: "🧩 Workshop Mod Manager",
    btn_check_mods: "🔍 Check Updates",
    btn_analyze_mods: "⚡ Dependency Analysis",
    btn_save_mods: "💾 Save Mod List",
    ph_mod_input: "Enter Workshop ID or Steam Collection URL...",
    btn_add_mod: "➕ Add Mod",
    mod_packs_label: "🎁 Curated Mod Packs:",
    pack_vehicles: "🚗 KI5 Vehicle Pack",
    pack_weapons: "⚔️ Brita Weapon Pack",
    pack_qol: "🖥️ QoL Essentials",
    pack_hardcore: "🧟 Hardcore Survival",
    btn_clear_mods: "🧹 Clear All",

    install_title: "📦 Install & Update Dedicated Server (SteamCMD)",
    btn_check_update: "🔍 Check Updates on Steam",
    install_desc: "Select the desired branch for Project Zomboid Dedicated Server (Steam AppID 380870).",
    col_branch_name: "NAME AND DESCRIPTION",
    col_branch_update: "LAST UPDATED",
    lbl_hidden_branch: "🔑 Private Beta:",
    ph_hidden_branch: "Branch name (optional)",
    ph_access_code: "Access code or password",
    btn_check_code: "Check Code",
    btn_do_install: "🚀 Install / Update Server",

    backups_title: "💾 World & Configuration Backups",
    btn_create_backup: "📦 Create Backup Now",

    toast_settings_saved: "💾 Server settings successfully saved!",
    toast_sandbox_saved: "💾 Sandbox parameters successfully saved!",
    toast_mods_saved: "💾 Mod list saved!",
    // Vehicles Extended
    group_vehicle_spawn: "🚗 Vehicle Spawn & Condition",
    group_vehicle_physics: "⛽ Speed, Fuel & Physics",
    chk_enable_vehicles: "Enable vehicles in world (EnableVehicles)",
    lbl_survivor_vehicles: "Recently survivor vehicles with loot (RecentlySurvivorVehicles):",
    lbl_locked_cars: "Locked car doors chance (LockedCar):",
    chk_vehicle_easy_use: "Easy vehicle use (no key / hotwiring required)",
    chk_traffic_jam: "Highway traffic jams and wrecks",
    lbl_zombie_attraction: "Zombie engine noise attraction multiplier:",
    lbl_siren_shutoff: "Emergency siren shutoff time in hours (0=until battery dead):",
    lbl_car_damage_impact: "Vehicle damage multiplier on impact:",
    lbl_player_hit_damage: "Pedestrian damage when hit by vehicle:",
    chk_crash_damage: "Player damaged in vehicle crashes",
    full: "Full Tank",
    deadly: "Deadly",
    toast_backup_created: "📦 World backup created successfully!"
  }
};

function t(key) {
  const dict = TRANSLATIONS_WEB[currentLang] || TRANSLATIONS_WEB['ru'];
  return dict[key] !== undefined ? dict[key] : (TRANSLATIONS_WEB['ru'][key] || key);
}

function toggleLanguage() {
  currentLang = (currentLang === 'ru') ? 'en' : 'ru';
  localStorage.setItem('pz_lang', currentLang);
  applyTranslations();
  showToast(currentLang === 'ru' ? '🌐 Язык переключен: Русский' : '🌐 Language switched: English');
}

function applyTranslations() {
  const btnLang = document.getElementById('btn-lang');
  if (btnLang) {
    btnLang.textContent = (currentLang === 'ru') ? '🌐 RU' : '🌐 EN';
  }

  // Update elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const val = t(key);
    if (val) el.textContent = val;
  });

  // Update inputs with data-i18n-ph
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    const val = t(key);
    if (val) el.placeholder = val;
  });

  // Update select options with data-i18n-opt
  document.querySelectorAll('option[data-i18n-opt]').forEach(opt => {
    const key = opt.getAttribute('data-i18n-opt');
    const val = t(key);
    if (val) opt.textContent = val;
  });

  // Update elements with data-i18n-title
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    const val = t(key);
    if (val) el.title = val;
  });

  // Update active status card if server stopped/running
  if (!isServerRunning) {
    const stTitle = document.getElementById('status-title');
    const stSub = document.getElementById('status-sub');
    if (stTitle && stSub) {
      stTitle.textContent = t('status_offline');
      stSub.textContent = t('status_offline_sub');
    }
  }
}

// 🧟 Project Zomboid Server Manager - Web Panel Client

let authToken = localStorage.getItem('pz_token') || '';
let ws = null;
let currentTab = 'server';
let isServerRunning = false;
let currentPublicIp = '';
let currentLocalIp = '';
let currentGamePort = 16261;
let selectedPlayerName = null;

function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + currentToken
  };
}

// ── Initialization ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (currentToken) {
    checkAuth();
  } else {
    showLogin();
  }
});

async function checkAuth() {
  try {
    const res = await fetch('/api/status', { headers: getHeaders() });
    if (res.status === 401 || res.status === 403) {
      showLogin();
    } else {
      hideLogin();
      initDashboard();
    }
  } catch (e) {
    showLogin();
  }
}

function showLogin() {
  document.getElementById('login-modal').style.display = 'flex';
  const inp = document.getElementById('login-password');
  if (inp) {
    inp.value = '';
    inp.focus();
  }
}

function hideLogin() {
  document.getElementById('login-modal').style.display = 'none';
}

async function handleLogin() {
  const pwd = document.getElementById('login-password').value;
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      currentToken = data.token;
      localStorage.setItem('pz_token', currentToken);
      hideLogin();
      initDashboard();
    } else {
      errEl.textContent = data.detail || 'Неверный пароль администратора';
      errEl.style.display = 'block';
    }
  } catch (e) {
    errEl.textContent = 'Ошибка подключения к серверу';
    errEl.style.display = 'block';
  }
}

function logout() {
  fetch('/api/logout', { method: 'POST', headers: getHeaders() }).catch(() => {});
  localStorage.removeItem('pz_token');
  currentToken = '';
  if (ws) {
    ws.close();
    ws = null;
  }
  showLogin();
}

// ── Tab Navigation ────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick')?.includes(name));
  const activePanel = document.getElementById('tab-' + name);

  if (activeBtn) activeBtn.classList.add('active');
  if (activePanel) activePanel.classList.add('active');

  if (name === 'server') {
    refreshPlayers();
    loadWatchdog();
  }
  if (name === 'settings') loadSettings();
  if (name === 'sandbox') loadSandbox();
  if (name === 'mods') loadMods();
  if (name === 'install') loadInstallInfo();
  if (name === 'backups') loadBackups();
  if (name === 'map' && window.initPzMap) window.initPzMap();
}

function switchSandboxSubtab(subtab) {
  document.querySelectorAll('.subtab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('#tab-sandbox .subtab-panel').forEach(p => p.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.subtab-btn')).find(b => b.getAttribute('onclick')?.includes(subtab));
  const activePanel = document.getElementById('sb-subtab-' + subtab);

  if (activeBtn) activeBtn.classList.add('active');
  if (activePanel) activePanel.classList.add('active');
}

// ── Dashboard Core ────────────────────────────────────────────────
function initDashboard() {
  connectWebSocket();
  loadConsoleHistory();
  pollStatus();
  setInterval(pollStatus, 3000);
  setInterval(pollMetrics, 3000);
  setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      loadConsoleHistory();
    }
  }, 3000);
  setInterval(() => {
    const srvPanel = document.getElementById('tab-server');
    if (srvPanel && srvPanel.classList.contains('active')) {
      refreshPlayers(true);
    }
  }, 5000);
  loadWatchdog();
}

async function loadConsoleHistory() {
  try {
    const res = await fetch('/api/console/history', { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const out = document.getElementById('console-output');
    if (out && data.lines && data.lines.length > 0) {
      out.innerHTML = '';
      data.lines.forEach(l => {
        const div = document.createElement('div');
        div.className = 'terminal-line';
        div.textContent = l;
        out.appendChild(div);
      });
      const chk = document.getElementById('autoscroll-chk');
      if (chk && chk.checked) {
        out.scrollTop = out.scrollHeight;
      }
    }
  } catch (e) {}
}

// ── WebSocket Live Console ────────────────────────────────────────
function connectWebSocket() {
  if (ws) return;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${window.location.host}/ws/console?token=${encodeURIComponent(currentToken)}`;

  ws = new WebSocket(url);

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'console') {
        appendConsoleLine(msg.line);
      } else if (msg.type === 'metrics') {
        updateMetrics(msg.data);
      }
    } catch (e) {
      appendConsoleLine(event.data);
    }
  };

  ws.onclose = () => {
    ws = null;
    if (currentToken) {
      setTimeout(connectWebSocket, 3000);
    }
  };
}

function appendConsoleLine(line) {
  const out = document.getElementById('console-output');
  if (!out) return;
  const div = document.createElement('div');
  div.className = 'terminal-line';
  div.textContent = line;
  out.appendChild(div);

  const chk = document.getElementById('autoscroll-chk');
  if (chk && chk.checked) {
    out.scrollTop = out.scrollHeight;
  }
}

function clearConsole() {
  const out = document.getElementById('console-output');
  if (out) out.innerHTML = '';
}

function sendConsoleCommand() {
  const inp = document.getElementById('console-cmd');
  if (!inp) return;
  const cmd = inp.value.trim();
  if (!cmd) return;

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'command', text: cmd }));
  } else {
    fetch('/api/server/command', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ command: cmd })
    });
  }
  inp.value = '';
}


function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3500);
}

function copyConnectAddress() {
  const port = currentGamePort || 16261;
  const ip = currentPublicIp || currentLocalIp || '127.0.0.1';
  const text = `${ip}:${port}`;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(`📋 Адрес скопирован: ${text}`);
    }).catch(() => {
      showToast(`Адрес сервера: ${text}`);
    });
  } else {
    showToast(`Адрес сервера: ${text}`);
  }
}

async function savePrefsOnChange() {
  const name = document.getElementById('srv-name')?.value.trim() || 'servertest';
  const ram = parseInt(document.getElementById('srv-ram')?.value) || 6;
  const autoBkp = document.getElementById('chk-auto-backup')?.checked ?? true;
  const watchdog = document.getElementById('chk-watchdog')?.checked ?? true;

  localStorage.setItem('pz_srv_name', name);
  localStorage.setItem('pz_srv_ram', ram);

  try {
    await fetch('/api/preferences', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        last_server_name: name,
        last_ram_gb: ram,
        auto_backup: autoBkp,
        watchdog_enabled: watchdog
      })
    });
  } catch (e) {
    console.error('Failed to save preferences:', e);
  }
}

// ── Server Lifecycle & Controls ───────────────────────────────────
async function fetchStatus() {
  try {
    const res = await fetch('/api/status', { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    isServerRunning = data.running;

    if (data.public_ip) currentPublicIp = data.public_ip;
    if (data.local_ip) currentLocalIp = data.local_ip;
    if (data.game_port) currentGamePort = data.game_port;

    // Apply persistent RAM from server if user has not modified it in session
    if (data.ram_gb) {
      const srvRam = document.getElementById('srv-ram');
      if (srvRam && !srvRam.dataset.userChanged) {
        srvRam.value = data.ram_gb;
        localStorage.setItem('pz_srv_ram', data.ram_gb);
      }
    }
    if (data.server_name) {
      const srvName = document.getElementById('srv-name');
      if (srvName && !srvName.dataset.userChanged) {
        srvName.value = data.server_name;
        localStorage.setItem('pz_srv_name', data.server_name);
      }
    }

    updateStatusCard(data.running);
    if (data.metrics) updateMetricsUI(data.metrics);
    if (data.target_version) {
      document.getElementById('badge-version').textContent = `🎯 Build ${data.target_version}`;
    }

    const badgeVer = document.getElementById('badge-version');
    if (badgeVer) {
      badgeVer.textContent = '🎯 Build ' + (data.target_version || '42');
    }
  } catch (e) {
    console.error('pollStatus error:', e);
  }
}

function updateStatusCard(running) {
  const pulseLed = document.getElementById('pulse-led');
  const title = document.getElementById('status-title');
  const sub = document.getElementById('status-sub');
  const connText = document.getElementById('conn-text');
  const btnStart = document.getElementById('btn-start');
  const btnStop = document.getElementById('btn-stop');
  const btnRestart = document.getElementById('btn-restart');

  const port = currentGamePort || 16261;
  const ip = currentPublicIp || currentLocalIp || '127.0.0.1';

  if (running) {
    if (pulseLed) pulseLed.className = 'pulse-led online';
    if (title) {
      title.className = 'status-title ready';
      title.textContent = '🟢 СЕРВЕР ОНЛАЙН';
    }
    if (sub) sub.textContent = 'Сервер запущен и готов к подключению игроков';
    if (connText) connText.textContent = `IP: ${ip}:${port}`;
    if (btnStart) btnStart.disabled = true;
    if (btnStop) btnStop.disabled = false;
    if (btnRestart) btnRestart.disabled = false;
  } else {
    if (pulseLed && pulseLed.className !== 'pulse-led launching') {
      pulseLed.className = 'pulse-led offline';
    }
    if (title && title.className !== 'status-title launching') {
      title.className = 'status-title stopped';
      title.textContent = '🔴 СЕРВЕР ОСТАНОВЛЕН';
    }
    if (sub && pulseLed && pulseLed.className !== 'pulse-led launching') {
      sub.textContent = 'Нажмите «Запустить сервер» для старта';
    }
    if (connText) connText.textContent = `Порт: ${port} (Готов к запуску)`;
    if (btnStart) btnStart.disabled = false;
    if (btnStop) btnStop.disabled = true;
    if (btnRestart) btnRestart.disabled = true;
  }

function updateServerButtons(running) {
  updateStatusCard(running);
}

function updateMetricsUI(m) {
  if (m.vps_ram_used_gb !== undefined) {
    document.getElementById('badge-vps-ram').textContent =
      `🖥️ VPS RAM: ${m.vps_ram_used_gb}/${m.vps_ram_total_gb} GB (${m.vps_ram_percent}%)`;
  }
  if (m.server_ram_mb !== undefined) {
    const srvStr = m.server_ram_mb > 1024
      ? (m.server_ram_mb / 1024).toFixed(2) + ' GB'
      : m.server_ram_mb + ' MB';
    document.getElementById('badge-srv-ram').textContent = `🎮 Server RAM: ${srvStr}`;
  }
}

async function startServer() {
  const pulseLed = document.getElementById('pulse-led');
  const title = document.getElementById('status-title');
  const sub = document.getElementById('status-sub');
  if (pulseLed) pulseLed.className = 'pulse-led launching';
  if (title) {
    title.className = 'status-title launching';
    title.textContent = '🟡 ЗАПУСК СЕРВЕРА...';
  }
  if (sub) sub.textContent = 'Загрузка модов и генерация мира...';

  const btnStart = document.getElementById('btn-start');
  if (btnStart) btnStart.disabled = true;
  const name = document.getElementById('srv-name').value.trim() || 'servertest';
  const ram = parseInt(document.getElementById('srv-ram').value) || 6;

  // Persist immediately
  localStorage.setItem('pz_srv_name', name);
  localStorage.setItem('pz_srv_ram', ram);

  const res = await fetch('/api/server/start', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ server_name: name, ram_gb: ram })
  });
  const data = await res.json();
  if (!data.success) {
    alert('Ошибка запуска сервера: ' + data.message);
  } else {
    showToast('🚀 Сервер запускается...');
  }
  fetchStatus();
}

async function stopServer() {
  if (!confirm('Вы уверены, что хотите корректно остановить сервер?')) return;
  try {
    await fetch('/api/server/stop', { method: 'POST', headers: getHeaders() });
    setTimeout(pollStatus, 1000);
  } catch (e) {
    alert('Ошибка остановки');
  }
}

async function restartServer() {
  if (!confirm('Перезапустить сервер Project Zomboid?')) return;
  try {
    await fetch('/api/server/restart', { method: 'POST', headers: getHeaders() });
    setTimeout(pollStatus, 1500);
  } catch (e) {
    alert('Ошибка перезапуска');
  }
}

async function sendQuickAction(action) {
  try {
    const res = await fetch('/api/server/quick-action', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ action: action })
    });
    const d = await res.json();
    if (d.message) appendConsoleLine('> ' + d.message);
  } catch (e) {}
}

function promptBroadcast() {
  const msg = prompt('Введите текст объявления всем игрокам:');
  if (msg && msg.trim()) {
    fetch('/api/server/quick-action', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ action: 'broadcast', extra: msg.trim() })
    });
  }
}


// ── Live Players Management ───────────────────────────────────────
async function fetchPlayers() {
  try {
    const res = await fetch('/api/players', { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const countLbl = document.getElementById('players-count-lbl');
    if (countLbl) countLbl.textContent = `👥 Игроки онлайн (${data.count || 0})`;

    const box = document.getElementById('players-list-box');
    if (!box) return;

    if (!data.players || data.players.length === 0) {
      box.innerHTML = '<div class="empty-players-msg">Нет игроков на сервере</div>';
      selectedPlayerName = null;
      return;
    }

    box.innerHTML = '';
    data.players.forEach(p => {
      const item = document.createElement('div');
      item.className = 'player-item' + (p.name === selectedPlayerName ? ' selected' : '');
      const name = document.createElement('span');
      name.textContent = `👤 ${p.name}`;
      const ping = document.createElement('span');
      ping.style.color = '#79c0ff';
      ping.style.fontSize = '11px';
      ping.textContent = p.ping ? `${p.ping}ms` : '';
      item.appendChild(name);
      item.appendChild(ping);
      item.onclick = () => {
        document.querySelectorAll('.player-item').forEach(el => el.classList.remove('selected'));
        item.classList.add('selected');
        selectedPlayerName = p.name;
      };
      box.appendChild(item);
    });
  } catch (e) {
    console.error('Fetch players error:', e);
  }
}

async function kickSelectedPlayer() {
  if (!selectedPlayerName) {
    alert('Сначала выберите игрока из списка!');
    return;
  }
  if (!confirm(`Выгнать игрока ${selectedPlayerName} с сервера?`)) return;
  await fetch('/api/server/command', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ command: `kickuser "${selectedPlayerName}"` })
  });
  showToast(`Игрок ${selectedPlayerName} выгнан.`);
  setTimeout(fetchPlayers, 1000);
}

async function banSelectedPlayer() {
  if (!selectedPlayerName) {
    alert('Сначала выберите игрока из списка!');
    return;
  }
  if (!confirm(`Заблокировать (забанить) игрока ${selectedPlayerName} на сервере?`)) return;
  await fetch('/api/server/command', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ command: `banuser "${selectedPlayerName}"` })
  });
  showToast(`Игрок ${selectedPlayerName} заблокирован.`);
  setTimeout(fetchPlayers, 1000);
}

// ── Settings (INI) ────────────────────────────────────────────────
async function loadSettings() {
  try {
    const res = await fetch('/api/settings', { headers: getHeaders() });
    if (!res.ok) return;
    const c = await res.json();

    for (const [key, val] of Object.entries(c)) {
      const el = document.getElementById('ini-' + key);
      if (el) {
        if (el.type === 'checkbox') {
          el.checked = (String(val).toLowerCase() === 'true');
        } else {
          el.value = val;
        }
      }
    }
  } catch (e) {
    console.error('Load settings error:', e);
  }
}

async function saveSettings() {
  const data = {};
  document.querySelectorAll('[id^="ini-"]').forEach(el => {
    const key = el.id.replace('ini-', '');
    if (el.type === 'checkbox') {
      data[key] = el.checked ? 'true' : 'false';
    } else {
      data[key] = el.value;
    }
  });

  const res = await fetch('/api/settings', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data)
  });
  const resData = await res.json();
  if (resData.success) {
    showToast('💾 Настройки сервера успешно сохранены!');
  } else {
    alert('Ошибка сохранения: ' + resData.message);
  }
}

// ── SandboxVars Subtabs & Management ──────────────────────────────
let cachedSandboxData = {};
let currentSandboxSubtab = 'zombies';

function switchSandboxSubtab(name) {
  currentSandboxSubtab = name;
  document.querySelectorAll('.subtab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.subtab-panel').forEach(panel => panel.classList.remove('active'));

  const btn = document.getElementById(`subtab-btn-${name}`);
  if (btn) btn.classList.add('active');

  const panel = document.getElementById(`sandbox-subtab-${name}`);
  if (panel) panel.classList.add('active');
}

function setXpPreset(val) {
  const el = document.getElementById('sb-XpMultiplier');
  if (el) el.value = val;
  showToast(`⚡ Множитель опыта установлен: ${val}x`);
}

async function loadSandbox() {
  try {
    const res = await fetch('/api/sandbox', { headers: getHeaders() });
    const sb = await res.json();
    cachedSandboxData = sb || {};

    const setVal = (id, v) => {
      const el = document.getElementById(id);
      if (el && v !== undefined && v !== null) {
        if (el.type === 'checkbox') {
          el.checked = Boolean(v);
        } else {
          el.value = v;
        }
      }
    };

    // Subtab 1: ZombieLore
    if (sb.ZombieLore) {
      setVal('sb-ZombieLore-Speed', sb.ZombieLore.Speed);
      setVal('sb-ZombieLore-Strength', sb.ZombieLore.Strength);
      setVal('sb-ZombieLore-Toughness', sb.ZombieLore.Toughness);
      setVal('sb-ZombieLore-Transmission', sb.ZombieLore.Transmission);
      setVal('sb-ZombieLore-Mortality', sb.ZombieLore.Mortality);
      setVal('sb-ZombieLore-Reanimate', sb.ZombieLore.Reanimate);
      setVal('sb-ZombieLore-Cognition', sb.ZombieLore.Cognition);
      setVal('sb-ZombieLore-Memory', sb.ZombieLore.Memory);
      setVal('sb-ZombieLore-Sight', sb.ZombieLore.Sight);
      setVal('sb-ZombieLore-Hearing', sb.ZombieLore.Hearing);
      setVal('sb-ZombieLore-Smell', sb.ZombieLore.Smell);
      setVal('sb-ZombieLore-ActiveOnly', sb.ZombieLore.ActiveOnly);
      setVal('sb-ZombieLore-Decomposition', sb.ZombieLore.Decomposition);
      setVal('sb-ZombieLore-TriggerHouseAlarm', sb.ZombieLore.TriggerHouseAlarm);
      setVal('sb-ZombieLore-ThumpOnConstruction', sb.ZombieLore.ThumpOnConstruction);
      setVal('sb-ZombieLore-ThumpNoChasing', sb.ZombieLore.ThumpNoChasing);
      setVal('sb-ZombieLore-ZombiesDragDown', sb.ZombieLore.ZombiesDragDown);
      setVal('sb-ZombieLore-ZombiesFenceLunge', sb.ZombieLore.ZombiesFenceLunge);
    }

    // Subtab 1: ZombieConfig
    if (sb.ZombieConfig) {
      setVal('sb-ZombieConfig-PopulationMultiplier', sb.ZombieConfig.PopulationMultiplier);
      setVal('sb-ZombieConfig-PopulationPeakMultiplier', sb.ZombieConfig.PopulationPeakMultiplier);
      setVal('sb-ZombieConfig-PopulationPeakDay', sb.ZombieConfig.PopulationPeakDay);
      setVal('sb-ZombieConfig-RespawnHours', sb.ZombieConfig.RespawnHours);
      setVal('sb-ZombieConfig-RespawnMultiplier', sb.ZombieConfig.RespawnMultiplier);
      setVal('sb-ZombieConfig-RallyGroupSize', sb.ZombieConfig.RallyGroupSize);
      setVal('sb-ZombieConfig-RallyGroupRadius', sb.ZombieConfig.RallyGroupRadius);
      setVal('sb-ZombieConfig-RedistributeHours', sb.ZombieConfig.RedistributeHours);
    }

    // Subtab 2: Loot
    if (sb.Loot) {
      setVal('sb-Loot-Weapon', sb.Loot.Weapon);
      setVal('sb-Loot-RangedWeapon', sb.Loot.RangedWeapon);
      setVal('sb-Loot-Ammo', sb.Loot.Ammo);
      setVal('sb-Loot-Food', sb.Loot.Food);
      setVal('sb-Loot-CannedFood', sb.Loot.CannedFood);
      setVal('sb-Loot-Medical', sb.Loot.Medical);
      setVal('sb-Loot-Literature', sb.Loot.Literature);
      setVal('sb-Loot-SurvivalGears', sb.Loot.SurvivalGears);
      setVal('sb-Loot-Mechanics', sb.Loot.Mechanics);
      setVal('sb-Loot-Other', sb.Loot.Other);
    }
    setVal('sb-LootRespawn', sb.LootRespawn);
    setVal('sb-MaxItemsForRespawn', sb.MaxItemsForRespawn);
    setVal('sb-ConstructionPreventsLootRespawn', sb.ConstructionPreventsLootRespawn);
    setVal('sb-WaterShut', sb.WaterShut);
    setVal('sb-ElecShut', sb.ElecShut);

    // Subtab 3: World & Time
    setVal('sb-DayLength', sb.DayLength);
    setVal('sb-StartYear', sb.StartYear);
    setVal('sb-StartMonth', sb.StartMonth);
    setVal('sb-StartDay', sb.StartDay);
    setVal('sb-StartTime', sb.StartTime);
    setVal('sb-Temperature', sb.Temperature);
    setVal('sb-Rain', sb.Rain);
    setVal('sb-ErosionSpeed', sb.ErosionSpeed);
    setVal('sb-ErosionDays', sb.ErosionDays);
    setVal('sb-Helicopter', sb.Helicopter);
    setVal('sb-MetaEvent', sb.MetaEvent);
    setVal('sb-TimeSinceApo', sb.TimeSinceApo);
    setVal('sb-NightDarkness', sb.NightDarkness);
    setVal('sb-NatureAbundance', sb.NatureAbundance);
    setVal('sb-FireSpread', sb.FireSpread);

    // Subtab 4: Vehicles (Complete Project Zomboid settings)
    setVal('sb-EnableVehicles', sb.EnableVehicles !== false);
    setVal('sb-CarSpawnRate', sb.CarSpawnRate || 3);
    setVal('sb-CarCondition', sb.CarCondition || 3);
    setVal('sb-RecentlySurvivorVehicles', sb.RecentlySurvivorVehicles || 3);
    setVal('sb-LockedCar', sb.LockedCar || 4);
    setVal('sb-VehicleEasyUse', Boolean(sb.VehicleEasyUse));
    setVal('sb-TrafficJam', sb.TrafficJam !== false);
    setVal('sb-SpeedLimit', sb.SpeedLimit || 70);
    setVal('sb-ZombieAttractionMultiplier', sb.ZombieAttractionMultiplier !== undefined ? sb.ZombieAttractionMultiplier : 1.0);
    setVal('sb-ChanceHasGas', sb.ChanceHasGas || 3);
    setVal('sb-InitialGas', sb.InitialGas || 2);
    setVal('sb-CarGasConsumption', sb.CarGasConsumption !== undefined ? sb.CarGasConsumption : 1.0);
    setVal('sb-CarAlarm', sb.CarAlarm || 3);
    setVal('sb-SirenShutoffHours', sb.SirenShutoffHours !== undefined ? sb.SirenShutoffHours : 0.0);
    setVal('sb-CarDamageOnImpact', sb.CarDamageOnImpact || 3);
    setVal('sb-DamageToPlayerFromHitByCar', sb.DamageToPlayerFromHitByCar || 3);
    setVal('sb-PlayerDamageFromCarCrash', sb.PlayerDamageFromCarCrash !== false);

    // Subtab 5: Character & Skills
    setVal('sb-XpMultiplier', sb.XpMultiplier);
    setVal('sb-CharacterFreePoints', sb.CharacterFreePoints);
    setVal('sb-StatsDecrease', sb.StatsDecrease);
    setVal('sb-Nutrition', sb.Nutrition);
    setVal('sb-FarmingSpeed', sb.FarmingSpeed);
    setVal('sb-PlantResilience', sb.PlantResilience);
    setVal('sb-PlantAbundance', sb.PlantAbundance);
    setVal('sb-GeneratorSpawning', sb.GeneratorSpawning);
    setVal('sb-GeneratorFuelConsumption', sb.GeneratorFuelConsumption);

    // Subtab 6: Mod Sandbox Options
    renderModSandboxOptions(sb);
  } catch (e) {
    console.error('loadSandbox error:', e);
  }
}

function renderModSandboxOptions(sb) {
  const container = document.getElementById('sandbox-mods-dynamic-container');
  const countLbl = document.getElementById('sandbox-mod-count');
  if (!container) return;

  const vanillaTables = new Set(['ZombieLore', 'ZombieConfig', 'MultiplierConfig', 'Map', 'Basement', 'SandboxVars', 'Loot']);
  const modTables = Object.entries(sb).filter(([k, v]) => typeof v === 'object' && v !== null && !Array.isArray(v) && !vanillaTables.has(k));

  if (modTables.length === 0) {
    container.innerHTML = `
      <div style="color: var(--text-muted); padding: 24px 16px; text-align: center; border: 1px dashed var(--border); border-radius: 8px;">
        <div style="font-size: 24px; margin-bottom: 8px;">🧩</div>
        <div style="font-weight: 600; color: #cbd5e1;">Таблицы модов не обнаружены в текущем SandboxVars.lua</div>
        <div style="font-size: 12px; margin-top: 4px;">При установке модов с опциями песочницы (например Brita, KI5) их параметры автоматически появятся здесь.</div>
      </div>
    `;
    if (countLbl) countLbl.textContent = 'Опций модов: 0';
    return;
  }

  let totalOptions = 0;
  container.innerHTML = '';

  modTables.forEach(([tableName, options]) => {
    const card = document.createElement('div');
    card.className = 'mod-option-card';
    card.dataset.modTable = tableName;

    const title = document.createElement('div');
    title.style.cssText = 'font-weight: 700; font-size: 13.5px; color: #4ea8de; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;';
    title.innerHTML = `<span>⚙️</span> <span>Мод: ${tableName}</span>`;
    card.appendChild(title);

    const grid = document.createElement('div');
    grid.className = 'row';
    grid.style.rowGap = '10px';

    Object.entries(options).forEach(([optKey, optVal]) => {
      totalOptions++;
      const col = document.createElement('div');
      col.className = 'col';
      col.style.minWidth = '220px';
      col.dataset.optSearch = `${tableName} ${optKey}`.toLowerCase();

      const fg = document.createElement('div');
      fg.className = 'form-group';
      fg.style.marginBottom = '6px';

      const lbl = document.createElement('label');
      lbl.textContent = optKey + ':';
      fg.appendChild(lbl);

      if (typeof optVal === 'boolean') {
        const chkLbl = document.createElement('label');
        chkLbl.className = 'custom-checkbox-label';
        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.checked = optVal;
        chk.dataset.modTable = tableName;
        chk.dataset.modKey = optKey;
        chkLbl.appendChild(chk);
        const span = document.createElement('span');
        span.textContent = optVal ? 'Включено (True)' : 'Отключено (False)';
        chk.onchange = () => { span.textContent = chk.checked ? 'Включено (True)' : 'Отключено (False)'; };
        chkLbl.appendChild(span);
        fg.appendChild(chkLbl);
      } else if (typeof optVal === 'number') {
        const inp = document.createElement('input');
        inp.type = 'number';
        inp.className = 'form-control';
        inp.value = optVal;
        inp.dataset.modTable = tableName;
        inp.dataset.modKey = optKey;
        if (Number.isInteger(optVal)) {
          inp.step = '1';
        } else {
          inp.step = '0.1';
        }
        fg.appendChild(inp);
      } else {
        const inp = document.createElement('input');
        inp.type = 'text';
        inp.className = 'form-control';
        inp.value = String(optVal);
        inp.dataset.modTable = tableName;
        inp.dataset.modKey = optKey;
        fg.appendChild(inp);
      }

      col.appendChild(fg);
      grid.appendChild(col);
    });

    card.appendChild(grid);
    container.appendChild(card);
  });

  if (countLbl) countLbl.textContent = `Таблиц модов: ${modTables.length} (${totalOptions} параметров)`;
}

function filterModSandboxOptions(query) {
  const q = (query || '').toLowerCase().trim();
  document.querySelectorAll('.mod-option-card').forEach(card => {
    let hasVisibleCol = false;
    card.querySelectorAll('[data-opt-search]').forEach(col => {
      const match = !q || col.dataset.optSearch.includes(q);
      col.style.display = match ? '' : 'none';
      if (match) hasVisibleCol = true;
    });
    card.style.display = hasVisibleCol ? '' : 'none';
  });
}

async function saveSandbox() {
  const getInt = (id, fallback) => {
    const el = document.getElementById(id);
    return el ? (parseInt(el.value) || fallback) : fallback;
  };
  const getFloat = (id, fallback) => {
    const el = document.getElementById(id);
    return el ? (parseFloat(el.value) || fallback) : fallback;
  };
  const getBool = (id, fallback) => {
    const el = document.getElementById(id);
    return el ? el.checked : fallback;
  };

  const sb = { ...cachedSandboxData };

  // Subtab 1: ZombieLore & ZombieConfig
  sb.ZombieLore = {
    ...(sb.ZombieLore || {}),
    Speed: getInt('sb-ZombieLore-Speed', 2),
    Strength: getInt('sb-ZombieLore-Strength', 2),
    Toughness: getInt('sb-ZombieLore-Toughness', 2),
    Transmission: getInt('sb-ZombieLore-Transmission', 1),
    Mortality: getInt('sb-ZombieLore-Mortality', 5),
    Reanimate: getInt('sb-ZombieLore-Reanimate', 3),
    Cognition: getInt('sb-ZombieLore-Cognition', 3),
    Memory: getInt('sb-ZombieLore-Memory', 2),
    Sight: getInt('sb-ZombieLore-Sight', 2),
    Hearing: getInt('sb-ZombieLore-Hearing', 2),
    Smell: getInt('sb-ZombieLore-Smell', 2),
    ActiveOnly: getInt('sb-ZombieLore-ActiveOnly', 1),
    TriggerHouseAlarm: getBool('sb-ZombieLore-TriggerHouseAlarm', false),
    ThumpOnConstruction: getBool('sb-ZombieLore-ThumpOnConstruction', true),
    ThumpNoChasing: getBool('sb-ZombieLore-ThumpNoChasing', false),
    ZombiesDragDown: getBool('sb-ZombieLore-ZombiesDragDown', true),
    ZombiesFenceLunge: getBool('sb-ZombieLore-ZombiesFenceLunge', true),
    Decomposition: getInt('sb-ZombieLore-Decomposition', 2),
  };

  sb.ZombieConfig = {
    ...(sb.ZombieConfig || {}),
    PopulationMultiplier: getFloat('sb-ZombieConfig-PopulationMultiplier', 1.0),
    PopulationPeakMultiplier: getFloat('sb-ZombieConfig-PopulationPeakMultiplier', 1.5),
    PopulationPeakDay: getInt('sb-ZombieConfig-PopulationPeakDay', 28),
    RespawnHours: getInt('sb-ZombieConfig-RespawnHours', 72),
    RespawnMultiplier: getFloat('sb-ZombieConfig-RespawnMultiplier', 0.1),
    RallyGroupSize: getInt('sb-ZombieConfig-RallyGroupSize', 20),
    RallyGroupRadius: getInt('sb-ZombieConfig-RallyGroupRadius', 3),
    RedistributeHours: getInt('sb-ZombieConfig-RedistributeHours', 12),
  };

  // Subtab 2: Loot
  sb.Loot = {
    ...(sb.Loot || {}),
    Weapon: getInt('sb-Loot-Weapon', 3),
    RangedWeapon: getInt('sb-Loot-RangedWeapon', 3),
    Ammo: getInt('sb-Loot-Ammo', 3),
    Food: getInt('sb-Loot-Food', 3),
    CannedFood: getInt('sb-Loot-CannedFood', 3),
    Medical: getInt('sb-Loot-Medical', 3),
    Literature: getInt('sb-Loot-Literature', 3),
    SurvivalGears: getInt('sb-Loot-SurvivalGears', 3),
    Mechanics: getInt('sb-Loot-Mechanics', 3),
    Other: getInt('sb-Loot-Other', 3),
  };
  sb.LootRespawn = getInt('sb-LootRespawn', 1);
  sb.MaxItemsForRespawn = getInt('sb-MaxItemsForRespawn', 4);
  sb.ConstructionPreventsLootRespawn = getBool('sb-ConstructionPreventsLootRespawn', true);
  sb.WaterShut = getInt('sb-WaterShut', 2);
  sb.ElecShut = getInt('sb-ElecShut', 2);

  // Subtab 3: World & Time
  sb.DayLength = getInt('sb-DayLength', 3);
  sb.StartYear = getInt('sb-StartYear', 1);
  sb.StartMonth = getInt('sb-StartMonth', 7);
  sb.StartDay = getInt('sb-StartDay', 9);
  sb.StartTime = getInt('sb-StartTime', 2);
  sb.Temperature = getInt('sb-Temperature', 3);
  sb.Rain = getInt('sb-Rain', 3);
  sb.ErosionSpeed = getInt('sb-ErosionSpeed', 3);
  sb.ErosionDays = getInt('sb-ErosionDays', 100);
  sb.Helicopter = getInt('sb-Helicopter', 2);
  sb.MetaEvent = getInt('sb-MetaEvent', 2);
  sb.TimeSinceApo = getInt('sb-TimeSinceApo', 1);
  sb.NightDarkness = getInt('sb-NightDarkness', 3);
  sb.NatureAbundance = getInt('sb-NatureAbundance', 3);
  sb.FireSpread = getBool('sb-FireSpread', true);

  // Subtab 4: Vehicles (Complete settings)
  sb.EnableVehicles = getBool('sb-EnableVehicles', true);
  sb.CarSpawnRate = getInt('sb-CarSpawnRate', 3);
  sb.CarCondition = getInt('sb-CarCondition', 3);
  sb.RecentlySurvivorVehicles = getInt('sb-RecentlySurvivorVehicles', 3);
  sb.LockedCar = getInt('sb-LockedCar', 4);
  sb.VehicleEasyUse = getBool('sb-VehicleEasyUse', false);
  sb.TrafficJam = getBool('sb-TrafficJam', true);
  sb.SpeedLimit = getInt('sb-SpeedLimit', 70);
  sb.ZombieAttractionMultiplier = getFloat('sb-ZombieAttractionMultiplier', 1.0);
  sb.ChanceHasGas = getInt('sb-ChanceHasGas', 3);
  sb.InitialGas = getInt('sb-InitialGas', 2);
  sb.CarGasConsumption = getFloat('sb-CarGasConsumption', 1.0);
  sb.CarAlarm = getInt('sb-CarAlarm', 3);
  sb.SirenShutoffHours = getFloat('sb-SirenShutoffHours', 0.0);
  sb.CarDamageOnImpact = getInt('sb-CarDamageOnImpact', 3);
  sb.DamageToPlayerFromHitByCar = getInt('sb-DamageToPlayerFromHitByCar', 3);
  sb.PlayerDamageFromCarCrash = getBool('sb-PlayerDamageFromCarCrash', true);

  // Synchronize SpeedLimit with Server INI
  const iniSpeed = document.getElementById('ini-SpeedLimit');
  if (iniSpeed) iniSpeed.value = sb.SpeedLimit;

  // Subtab 5: Character & Skills
  sb.XpMultiplier = getFloat('sb-XpMultiplier', 1.0);
  sb.CharacterFreePoints = getInt('sb-CharacterFreePoints', 0);
  sb.StatsDecrease = getInt('sb-StatsDecrease', 3);
  sb.Nutrition = getBool('sb-Nutrition', true);
  sb.FarmingSpeed = getInt('sb-FarmingSpeed', 3);
  sb.PlantResilience = getInt('sb-PlantResilience', 3);
  sb.PlantAbundance = getInt('sb-PlantAbundance', 3);
  sb.GeneratorSpawning = getInt('sb-GeneratorSpawning', 3);
  sb.GeneratorFuelConsumption = getFloat('sb-GeneratorFuelConsumption', 1.0);

  // Subtab 6: Mod Sandbox Options
  document.querySelectorAll('[data-mod-table][data-mod-key]').forEach(el => {
    const t = el.dataset.modTable;
    const k = el.dataset.modKey;
    if (!sb[t]) sb[t] = {};
    if (el.type === 'checkbox') {
      sb[t][k] = el.checked;
    } else if (el.type === 'number') {
      sb[t][k] = el.step === '1' ? parseInt(el.value) || 0 : parseFloat(el.value) || 0;
    } else {
      sb[t][k] = el.value;
    }
  });

  // Collect mod options
  document.querySelectorAll('.modopt-input').forEach(inp => {
    const tbl = inp.getAttribute('data-table');
    const k = inp.getAttribute('data-key');
    if (!tbl || !k) return;

    if (!sb[tbl]) sb[tbl] = {};

    if (inp.type === 'checkbox') {
      sb[tbl][k] = inp.checked;
    } else if (inp.type === 'number') {
      sb[tbl][k] = inp.step === '0.1' ? parseFloat(inp.value) : parseInt(inp.value);
    } else {
      sb[tbl][k] = inp.value;
    }
  });
  const resData = await res.json();
  if (resData.success) {
    cachedSandboxData = sb;
    showToast('💾 Параметры Sandbox успешно сохранены!');
  } else {
    alert('Ошибка сохранения Sandbox: ' + resData.message);
  }
}

function applySandboxPreset(preset) {
  const setVal = (id, v) => {
    const el = document.getElementById(id);
    if (el) el.value = v;
  };

  if (preset === 'apocalypse') {
    setVal('sb-ZombieLore-Speed', '2');
    setVal('sb-ZombieLore-Strength', '2');
    setVal('sb-ZombieLore-Toughness', '2');
    setVal('sb-ZombieLore-Transmission', '1');
    setVal('sb-Loot-Food', '2');
    setVal('sb-Loot-Weapon', '2');
    setVal('sb-Loot-Literature', '2');
    setVal('sb-Loot-Medical', '2');
    setVal('sb-Loot-SurvivalGears', '2');
    setVal('sb-Loot-Mechanics', '2');
    setVal('sb-Loot-Other', '2');
    setVal('sb-XpMultiplier', '1.0');
    setVal('sb-CarSpawnRate', '2');
  } else if (preset === 'survivor') {
    setVal('sb-ZombieLore-Speed', '2');
    setVal('sb-ZombieLore-Strength', '2');
    setVal('sb-ZombieLore-Toughness', '2');
    setVal('sb-ZombieLore-Transmission', '1');
    setVal('sb-Loot-Food', '3');
    setVal('sb-Loot-Weapon', '3');
    setVal('sb-Loot-Literature', '3');
    setVal('sb-Loot-Medical', '3');
    setVal('sb-Loot-SurvivalGears', '3');
    setVal('sb-Loot-Mechanics', '3');
    setVal('sb-Loot-Other', '3');
    setVal('sb-XpMultiplier', '1.0');
    setVal('sb-CarSpawnRate', '3');
  } else if (preset === 'builder') {
    setVal('sb-ZombieLore-Speed', '3');
    setVal('sb-ZombieLore-Strength', '3');
    setVal('sb-ZombieLore-Toughness', '3');
    setVal('sb-ZombieLore-Transmission', '4');
    setVal('sb-Loot-Food', '4');
    setVal('sb-Loot-Weapon', '4');
    setVal('sb-Loot-Literature', '4');
    setVal('sb-Loot-Medical', '4');
    setVal('sb-Loot-SurvivalGears', '4');
    setVal('sb-Loot-Mechanics', '4');
    setVal('sb-Loot-Other', '4');
    setVal('sb-XpMultiplier', '1.5');
    setVal('sb-CarSpawnRate', '4');
  }
  if (preset) showToast(`Применен пресет: ${preset}`);
}

// ── Search & Filter in Sandbox ────────────────────────────────────
function filterSandbox(query) {
  const q = (query || '').trim().toLowerCase();
  const subtabs = ['zombies', 'loot', 'world', 'vehicles', 'character', 'mods'];
  let firstMatchSubtab = null;
  let totalMatches = 0;

  subtabs.forEach(sub => {
    const panel = document.getElementById('sb-subtab-' + sub);
    const badge = document.getElementById('match-' + sub);
    if (!panel) return;

    let subMatches = 0;
    const groups = panel.querySelectorAll('.sb-group');

    groups.forEach(group => {
      const gTitle = (group.getAttribute('data-title') || '').toLowerCase();
      const fields = group.querySelectorAll('.sb-field');
      let groupHasMatch = false;

      fields.forEach(field => {
        const text = field.textContent.toLowerCase();
        const isMatch = !q || text.includes(q) || gTitle.includes(q);
        field.style.display = isMatch ? '' : 'none';
        if (isMatch) {
          subMatches++;
          groupHasMatch = true;
        }
      });

      group.style.display = (!q || groupHasMatch) ? '' : 'none';
    });

    if (badge) {
      if (q) {
        badge.textContent = subMatches;
        badge.style.display = 'inline-block';
      } else {
        badge.textContent = '';
        badge.style.display = 'none';
      }
    }

    if (subMatches > 0 && !firstMatchSubtab) {
      firstMatchSubtab = sub;
    }
    totalMatches += subMatches;
  });

  const stats = document.getElementById('sandbox-search-stats');
  if (stats) {
    stats.textContent = q ? `Найдено совпадений: ${totalMatches}` : '';
  }

  if (q && firstMatchSubtab) {
    const activeSub = document.querySelector('#tab-sandbox .subtab-panel.active');
    if (activeSub && activeSub.querySelectorAll('.sb-field:not([style*="display: none"])').length === 0) {
      switchSandboxSubtab(firstMatchSubtab);
    }
  }
}

// ── Backups Management ────────────────────────────────────────────
async function loadBackups() {
  const container = document.getElementById('backups-container');
  if (!container) return;

  try {
    const res = await fetch('/api/backups', { headers: getHeaders() });
    if (!res.ok) return;
    const backups = await res.json();

    if (!Array.isArray(backups) || backups.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; padding: 24px; text-align: center;">Архивы резервных копий пока не созданы. Нажмите кнопку "Создать бэкап сейчас".</div>';
      return;
    }

    let html = `<table class="data-table">
      <thead>
        <tr>
          <th>ИМЯ АРХИВА</th>
          <th>РАЗМЕР</th>
          <th>ДАТА СОЗДАНИЯ</th>
          <th style="text-align: right;">ДЕЙСТВИЯ</th>
        </tr>
      </thead>
      <tbody>`;

    backups.forEach(b => {
      const name = b.filename || b.name || '';
      const size = b.size_mb !== undefined ? `${b.size_mb} MB` : '--';
      const date = b.modified || '--';

      html += `<tr>
        <td style="font-family: var(--font-mono); font-size: 12px; color: #64b5f6;">📦 ${name}</td>
        <td><b>${size}</b></td>
        <td style="color: var(--text-muted);">${date}</td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="btn btn-secondary" onclick="restoreBackup('${name}')" style="padding: 4px 10px; font-size: 11px; margin-right: 6px;">📥 Восстановить</button>
          <button class="btn btn-danger" onclick="deleteBackup('${name}')" style="padding: 4px 10px; font-size: 11px;">🗑️ Удалить</button>
        </td>
      </tr>`;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div style="color: #ff6b6b; padding: 14px;">Ошибка загрузки списка бэкапов</div>';
  }
}

async function createBackupWithTag() {
  const tag = prompt('Введите тег или описание для резервной копии (например: before_wipe, test, safe):', 'manual');
  if (tag === null) return;

  try {
    const res = await fetch('/api/backups/create', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ tag: tag.trim() || 'manual' })
    });
    const d = await res.json();
    if (d.success) {
      alert(`✅ Бэкап успешно создан: ${d.file}`);
      loadBackups();
    } else {
      alert('Ошибка создания бэкапа: ' + (d.message || ''));
    }
  } catch (e) {
    alert('Сетевая ошибка создания бэкапа');
  }
}

async function restoreBackup(filename) {
  if (!confirm(`⚠️ ВНИМАНИЕ!\nВы действительно хотите восстановить сервер из резервной копии:\n"${filename}"?\n\nТекущее сохранение мира будет заменено!`)) {
    return;
  }

  try {
    const res = await fetch('/api/backups/restore', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ filename: filename })
    });
    const d = await res.json();
    if (d.success) {
      alert('✅ Мир успешно восстановлен из резервной копии!');
    } else {
      alert('Ошибка восстановления: ' + (d.message || ''));
    }
  } catch (e) {
    alert('Сетевая ошибка восстановления');
  }
}

// ── Startup ───────────────────────────────────────────────────────
function initDashboard() {
  fetchStatus();
  initWebSocket();
  fetchPlayers();
  setInterval(fetchStatus, 4000);
  setInterval(fetchPlayers, 6000);
}

document.addEventListener('DOMContentLoaded', () => {
  // Restore persistent preferences from localStorage immediately
  const savedRam = localStorage.getItem('pz_srv_ram');
  if (savedRam) {
    const el = document.getElementById('srv-ram');
    if (el) el.value = savedRam;
  }
  const savedName = localStorage.getItem('pz_srv_name');
  if (savedName) {
    const el = document.getElementById('srv-name');
    if (el) el.value = savedName;
  }

  const srvRamEl = document.getElementById('srv-ram');
  if (srvRamEl) {
    srvRamEl.addEventListener('change', () => {
      srvRamEl.dataset.userChanged = 'true';
      savePrefsOnChange();
    });
  }
  const srvNameEl = document.getElementById('srv-name');
  if (srvNameEl) {
    srvNameEl.addEventListener('input', () => {
      srvNameEl.dataset.userChanged = 'true';
      savePrefsOnChange();
    });
  }

  checkAuth();
});

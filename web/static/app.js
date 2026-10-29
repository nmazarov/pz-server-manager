// 🧟 Project Zomboid Server Manager - Web Panel Client

let authToken = localStorage.getItem('pz_token') || '';
let ws = null;
let currentTab = 'server';
let isServerRunning = false;
let currentPublicIp = '';
let currentLocalIp = '';
let currentGamePort = 16261;
let selectedPlayerName = null;

// ── Auth & Headers ────────────────────────────────────────────────
function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + authToken
  };
}

function checkAuth() {
  const modal = document.getElementById('login-modal');
  if (!authToken) {
    modal.style.display = 'flex';
  } else {
    modal.style.display = 'none';
    initDashboard();
  }
}

async function handleLogin() {
  const pw = document.getElementById('login-password').value;
  const errDiv = document.getElementById('login-error');
  errDiv.style.display = 'none';

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pw })
    });
    const data = await res.json();
    if (res.ok && data.token) {
      authToken = data.token;
      localStorage.setItem('pz_token', authToken);
      document.getElementById('login-modal').style.display = 'none';
      initDashboard();
    } else {
      errDiv.textContent = data.detail || 'Неверный пароль администратора!';
      errDiv.style.display = 'block';
    }
  } catch (err) {
    errDiv.textContent = 'Ошибка подключения к серверу: ' + err;
    errDiv.style.display = 'block';
  }
}

function logout() {
  if (confirm('Вы действительно хотите выйти из панели?')) {
    fetch('/api/logout', { method: 'POST', headers: getHeaders() });
    localStorage.removeItem('pz_token');
    authToken = '';
    if (ws) ws.close();
    location.reload();
  }
}

// ── Tab Navigation ────────────────────────────────────────────────
function switchTab(name) {
  currentTab = name;
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick')?.includes(name));
  if (activeBtn) activeBtn.classList.add('active');

  const activePanel = document.getElementById('tab-' + name);
  if (activePanel) activePanel.classList.add('active');

  if (name === 'settings') loadSettings();
  if (name === 'sandbox') loadSandbox();
  if (name === 'mods') loadMods();
  if (name === 'install') loadInstallInfo();
  if (name === 'backups') loadBackups();
}

// ── WebSocket Live Console ────────────────────────────────────────
function initWebSocket() {
  if (ws) ws.close();
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${protocol}//${location.host}/ws/console?token=${authToken}`;

  ws = new WebSocket(url);

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'console') {
        appendConsoleLine(msg.line);
      } else if (msg.type === 'metrics') {
        updateMetricsUI(msg.data);
      }
    } catch (e) {
      console.error('WS parse error:', e);
    }
  };

  ws.onclose = () => {
    setTimeout(() => {
      if (authToken) initWebSocket();
    }, 3000);
  };
}

function appendConsoleLine(text) {
  const out = document.getElementById('console-output');
  if (!out) return;

  const div = document.createElement('div');
  const lower = text.toLowerCase();

  if (lower.includes('error') || lower.includes('failed') || lower.includes('exception')) {
    div.className = 'log-red';
  } else if (lower.includes('server started') || lower.includes('ready') || lower.includes('listening')) {
    div.className = 'log-green';
  } else if (lower.includes('connected') || lower.includes('join')) {
    div.className = 'log-cyan';
  } else if (lower.includes('warning') || lower.includes('warn')) {
    div.className = 'log-orange';
  } else if (text.startsWith('>')) {
    div.className = 'log-cyan';
  }

  div.textContent = text;
  out.appendChild(div);

  const autoscroll = document.getElementById('autoscroll-chk')?.checked;
  if (autoscroll) {
    out.scrollTop = out.scrollHeight;
  }
}

function clearConsole() {
  const out = document.getElementById('console-output');
  if (out) out.innerHTML = '';
}

function sendConsoleCommand() {
  const input = document.getElementById('console-cmd');
  const cmd = input.value.trim();
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
  input.value = '';
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
    if (res.status === 401) {
      localStorage.removeItem('pz_token');
      authToken = '';
      checkAuth();
      return;
    }
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
  } catch (err) {
    console.error('Fetch status error:', err);
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
  if (!confirm('Остановить сервер Project Zomboid?')) return;
  await fetch('/api/server/stop', { method: 'POST', headers: getHeaders() });
  fetchStatus();
}

async function restartServer() {
  if (!confirm('Перезапустить сервер?')) return;
  await fetch('/api/server/restart', { method: 'POST', headers: getHeaders() });
  fetchStatus();
}

async function sendQuickAction(action, extra = '') {
  const res = await fetch('/api/server/quick-action', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ action: action, extra: extra })
  });
  const data = await res.json();
  if (data.message) {
    appendConsoleLine(`[Admin]: ${data.message}`);
  }
}

function promptBroadcast() {
  const msg = prompt('Введите объявление для отправки в игровой чат всем игрокам:');
  if (msg && msg.trim()) {
    sendQuickAction('broadcast', msg.trim());
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

    // Subtab 4: Vehicles
    setVal('sb-CarSpawnRate', sb.CarSpawnRate);
    setVal('sb-CarCondition', sb.CarCondition);
    setVal('sb-VehicleEasyUse', sb.VehicleEasyUse);
    setVal('sb-TrafficJam', sb.TrafficJam);
    setVal('sb-PlayerDamageFromCarCrash', sb.PlayerDamageFromCarCrash);
    setVal('sb-ChanceHasGas', sb.ChanceHasGas);
    setVal('sb-InitialGas', sb.InitialGas);
    setVal('sb-CarGasConsumption', sb.CarGasConsumption);
    setVal('sb-CarAlarm', sb.CarAlarm);

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
    console.error('Load sandbox error:', e);
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
  };

  sb.ZombieConfig = {
    ...(sb.ZombieConfig || {}),
    PopulationMultiplier: getFloat('sb-ZombieConfig-PopulationMultiplier', 1.0),
    PopulationPeakMultiplier: getFloat('sb-ZombieConfig-PopulationPeakMultiplier', 1.5),
    PopulationPeakDay: getInt('sb-ZombieConfig-PopulationPeakDay', 28),
    RespawnHours: getInt('sb-ZombieConfig-RespawnHours', 72),
    RespawnMultiplier: getFloat('sb-ZombieConfig-RespawnMultiplier', 0.1),
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

  // Subtab 4: Vehicles
  sb.CarSpawnRate = getInt('sb-CarSpawnRate', 3);
  sb.CarCondition = getInt('sb-CarCondition', 3);
  sb.VehicleEasyUse = getBool('sb-VehicleEasyUse', false);
  sb.TrafficJam = getBool('sb-TrafficJam', true);
  sb.PlayerDamageFromCarCrash = getBool('sb-PlayerDamageFromCarCrash', true);
  sb.ChanceHasGas = getInt('sb-ChanceHasGas', 3);
  sb.InitialGas = getInt('sb-InitialGas', 2);
  sb.CarGasConsumption = getFloat('sb-CarGasConsumption', 1.0);
  sb.CarAlarm = getInt('sb-CarAlarm', 3);

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

  const res = await fetch('/api/sandbox', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(sb)
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

// ── Mod Manager ───────────────────────────────────────────────────
async function loadMods() {
  const container = document.getElementById('mods-container');
  container.innerHTML = '<div style="color: var(--text-muted); padding: 10px;">Загрузка списка модов...</div>';

  try {
    const res = await fetch('/api/mods', { headers: getHeaders() });
    const data = await res.json();
    const mods = data.mods || [];
    const targetVer = data.target_version || 42;

    if (mods.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 10px;">Моды еще не добавлены.</div>';
      return;
    }

    container.innerHTML = '';
    mods.forEach(m => {
      const item = document.createElement('div');
      item.className = 'mod-item';

      let badgeClass = 'compat-yellow';
      let badgeText = '🟡 ' + m.reason;

      if (m.status === 'compatible') {
        badgeClass = 'compat-green';
        badgeText = `🟢 [✓ B${targetVer} Совместим]`;
      } else if (m.status === 'incompatible') {
        badgeClass = 'compat-red';
        badgeText = `🔴 [✗ ${m.reason}]`;
      }

      // Safe DOM creation
      const div1 = document.createElement('div');
      const titleDiv = document.createElement('div');
      titleDiv.className = 'mod-title';
      titleDiv.textContent = m.name;
      const idSpan = document.createElement('span');
      idSpan.style.cssText = "color: var(--text-muted); font-size: 11px;";
      idSpan.textContent = ` (ID: ${m.workshop_id})`;
      titleDiv.appendChild(idSpan);
      const idsDiv = document.createElement('div');
      idsDiv.style.cssText = "font-size: 11px; color: var(--text-muted); margin-top: 3px;";
      idsDiv.textContent = `Mod IDs: ${m.mod_ids.join(', ') || 'none'}`;
      div1.appendChild(titleDiv);
      div1.appendChild(idsDiv);
      const div2 = document.createElement('div');
      div2.style.cssText = "display: flex; align-items: center; gap: 10px;";
      const badgeSpan = document.createElement('span');
      badgeSpan.className = `mod-badge ${badgeClass}`;
      badgeSpan.textContent = badgeText;
      const btn = document.createElement('button');
      btn.className = 'btn btn-danger';
      btn.style.cssText = "padding: 4px 8px; font-size: 11px;";
      btn.textContent = '✕';
      btn.onclick = () => removeMod(m.workshop_id);
      div2.appendChild(badgeSpan);
      div2.appendChild(btn);
      item.appendChild(div1);
      item.appendChild(div2);
      container.appendChild(item);
    });
  } catch (e) {
    container.innerHTML = '<div style="color: #ff6b6b; padding: 10px;">Ошибка загрузки модов: ' + e + '</div>';
  }
}

async function addMod() {
  const input = document.getElementById('mod-input-id');
  const val = input.value.trim();
  if (!val) return;

  const res = await fetch('/api/mods/add', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ id_or_url: val })
  });
  const data = await res.json();
  if (data.success) {
    input.value = '';
    loadMods();
    if (data.status === 'incompatible') {
      alert(`⚠️ Внимание! Мод '${data.mod?.name}' определен как НЕСОВМЕСТИМЫЙ:\n${data.reason}`);
    }
  } else {
    alert('Ошибка добавления мода: ' + data.message);
  }
}

async function removeMod(wid) {
  await fetch('/api/mods/remove', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ id_or_url: wid })
  });
  loadMods();
}

async function clearMods() {
  if (confirm('Очистить весь список модов?')) {
    await fetch('/api/mods/clear', { method: 'POST', headers: getHeaders() });
    loadMods();
  }
}

async function checkAllModsCompatibility() {
  const res = await fetch('/api/mods/check', { method: 'POST', headers: getHeaders() });
  const data = await res.json();
  loadMods();
  alert(
    `Результаты проверки совместимости для Build ${data.target_version}:\n\n` +
    `• Всего модов: ${data.total}\n` +
    `• 🟢 Совместимы: ${data.compatible}\n` +
    `• 🔴 Несовместимы: ${data.incompatible}\n` +
    `• 🟡 Универсальные: ${data.warning}`
  );
}

async function applyModPack(packName) {
  const res = await fetch('/api/mods/preset', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ action: packName })
  });
  const data = await res.json();
  loadMods();
  alert(`Набор модов добавлен! Обработано модов: ${data.added}`);
}

async function analyzeMods() {
  const res = await fetch('/api/mods/analyze', { method: 'POST', headers: getHeaders() });
  const data = await res.json();
  if (data.success) {
    const rep = data.report;
    let msg = 'Анализ зависимостей завершен!\n\n';
    if (rep.missing_workshop_ids && rep.missing_workshop_ids.length > 0) {
      msg += `⚠️ Недостающие моды: ${rep.missing_workshop_ids.map(i => i.workshop_id).join(', ')}\n`;
    }
    if (rep.map_folders && rep.map_folders.length > 0) {
      msg += `🗺️ Обнаружены карты: ${rep.map_folders.join(', ')}\n`;
    }
    alert(msg || 'Все зависимости в порядке!');
    loadMods();
  }
}

async function saveMods() {
  const res = await fetch('/api/mods/save', { method: 'POST', headers: getHeaders() });
  const data = await res.json();
  if (data.success) {
    alert('Список модов успешно сохранен в конфигурацию сервера!');
  } else {
    alert('Ошибка сохранения: ' + data.message);
  }
}

// ── Install & Updates ─────────────────────────────────────────────
let currentBetaPassword = "";

async function loadInstallInfo() {
  try {
    const res = await fetch('/api/install/branches', { headers: getHeaders() });
    const branches = await res.json();
    const container = document.getElementById('steam-branch-rows');
    if (!container) return;

    container.innerHTML = '';
    branches.forEach((b, idx) => {
      const row = document.createElement('div');
      row.className = 'steam-branch-row' + (idx === 0 ? ' selected' : '');
      row.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 9px 16px; border-bottom: 1px solid #212b38; cursor: pointer; transition: background 0.15s;';
      if (idx === 0) {
        row.style.background = '#1c2e42';
        document.getElementById('install-branch').value = b.branch;
      }

      // Safe DOM creation
      const divWrapper = document.createElement('div');
      divWrapper.style.cssText = 'display: flex; align-items: center; gap: 10px;';
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'steam-branch-radio';
      radio.value = b.branch;
      radio.checked = (idx === 0);
      radio.style.cssText = 'cursor: pointer; width: 16px; height: 16px; accent-color: #67c1f5;';
      const nameDiv = document.createElement('div');
      nameDiv.style.cssText = 'font-weight: bold; font-size: 13px; color: #fff;';
      nameDiv.textContent = b.name_ru || b.name;
      const descDiv = document.createElement('div');
      descDiv.style.cssText = 'font-size: 12px; color: #8f98a0;';
      descDiv.textContent = '— ' + (b.desc_ru || b.description);
      divWrapper.appendChild(radio);
      divWrapper.appendChild(nameDiv);
      divWrapper.appendChild(descDiv);
      const dateDiv = document.createElement('div');
      dateDiv.style.cssText = 'font-size: 12px; color: #8f98a0; font-weight: normal; text-align: right;';
      dateDiv.textContent = b.date_ru || b.date_str || '';
      row.appendChild(divWrapper);
      row.appendChild(dateDiv);

      row.addEventListener('click', () => {
        const radio = row.querySelector('input[type="radio"]');
        radio.checked = true;
        document.querySelectorAll('.steam-branch-row').forEach(r => {
          r.classList.remove('selected');
          r.style.background = '#171d25';
        });
        row.classList.add('selected');
        row.style.background = '#1c2e42';
        document.getElementById('install-branch').value = b.branch;
      });

      row.addEventListener('mouseenter', () => {
        if (!row.classList.contains('selected')) row.style.background = '#202b3a';
      });
      row.addEventListener('mouseleave', () => {
        if (!row.classList.contains('selected')) row.style.background = '#171d25';
      });

      container.appendChild(row);
    });
  } catch (e) {
    console.error('Branches load error:', e);
  }
}

function checkBetaCode() {
  const code = document.getElementById('beta-access-code').value.trim();
  const hiddenBranch = document.getElementById('beta-hidden-branch').value.trim();
  const msg = document.getElementById('beta-code-msg');

  if (!code) {
    alert('Пожалуйста, введите код доступа или пароль ветки');
    return;
  }

  currentBetaPassword = code;
  const branchName = hiddenBranch || 'private_beta';
  document.getElementById('install-branch').value = branchName;

  msg.textContent = `✓ Код доступа принят! Ветка: ${branchName}`;
  msg.style.display = 'inline';
}

async function startInstallation() {
  const branch = document.getElementById('install-branch').value;
  if (!confirm(`Начать установку/обновление сервера ветки '${branch || "public"}'?`)) return;

  document.getElementById('btn-do-install').disabled = true;
  await fetch('/api/install/start', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ branch: branch, password: currentBetaPassword })
  });

  pollInstallStatus();
}

function pollInstallStatus() {
  const interval = setInterval(async () => {
    try {
      const res = await fetch('/api/install/status', { headers: getHeaders() });
      const data = await res.json();

      document.getElementById('install-status-msg').textContent = data.message;
      document.getElementById('install-status-pct').textContent = data.progress + '%';
      document.getElementById('install-progress-fill').style.width = data.progress + '%';

      if (data.logs && data.logs.length > 0) {
        document.getElementById('install-log-output').textContent = data.logs.slice(-30).join('\n');
      }

      if (!data.running) {
        clearInterval(interval);
        document.getElementById('btn-do-install').disabled = false;
        fetchStatus();
      }
    } catch (e) {
      clearInterval(interval);
      document.getElementById('btn-do-install').disabled = false;
    }
  }, 1000);
}

async function checkSteamUpdate() {
  const res = await fetch('/api/install/check-update', { headers: getHeaders() });
  const data = await res.json();
  if (data.update_available) {
    if (confirm(`🚀 В Steam вышла новая версия сервера!\n\nУстановлена: ${data.installed_version}\nДоступна: ${data.latest_version}\n\nОбновить сервер прямо сейчас?`)) {
      startInstallation();
    }
  } else {
    alert(`Версия сервера актуальна (${data.installed_version}). Обновлений нет.`);
  }
}

// ── Backups ───────────────────────────────────────────────────────
async function loadBackups() {
  const container = document.getElementById('backups-container');
  container.innerHTML = '<div style="color: var(--text-muted); padding: 10px;">Загрузка бэкапов...</div>';

  try {
    const res = await fetch('/api/backups', { headers: getHeaders() });
    const list = await res.json();

    if (list.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 10px;">Резервные копии еще не создавались.</div>';
      return;
    }

    container.innerHTML = '';
    list.forEach(b => {
      const item = document.createElement('div');
      item.className = 'mod-item';
      // Safe DOM creation
      const div1 = document.createElement('div');
      const nameDiv = document.createElement('div');
      nameDiv.style.cssText = 'font-weight: bold; font-size: 13px;';
      nameDiv.textContent = '📦 ' + b.name;
      const sizeDiv = document.createElement('div');
      sizeDiv.style.cssText = 'font-size: 11px; color: var(--text-muted); margin-top: 2px;';
      sizeDiv.textContent = 'Размер архива: ' + b.size_mb + ' MB';
      div1.appendChild(nameDiv);
      div1.appendChild(sizeDiv);
      const btn = document.createElement('button');
      btn.className = 'btn btn-secondary';
      btn.style.fontSize = '12px';
      btn.textContent = 'Восстановить';
      btn.onclick = () => restoreBackup(b.name);
      item.appendChild(div1);
      item.appendChild(btn);
      container.appendChild(item);
    });
  } catch (e) {
    container.innerHTML = '<div style="color: #ff6b6b; padding: 10px;">Ошибка загрузки бэкапов: ' + e + '</div>';
  }
}

async function createBackup() {
  const res = await fetch('/api/backups/create', { method: 'POST', headers: getHeaders() });
  const data = await res.json();
  if (data.success) {
    alert(`Бэкап успешно создан: ${data.file}`);
    loadBackups();
  } else {
    alert('Ошибка создания бэкапа: ' + data.message);
  }
}

async function restoreBackup(filename) {
  if (!confirm(`Восстановить мир из бэкапа '${filename}'? Текущие несохраненные изменения будут перезаписаны.`)) return;
  const res = await fetch('/api/backups/restore', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ action: filename })
  });
  const data = await res.json();
  if (data.success) {
    alert('Бэкап успешно восстановлен!');
  } else {
    alert('Ошибка восстановления: ' + data.message);
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

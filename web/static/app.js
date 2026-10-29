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

// ── SandboxVars ───────────────────────────────────────────────────
let cachedSandboxData = {};

async function loadSandbox() {
  try {
    const res = await fetch('/api/sandbox', { headers: getHeaders() });
    const sb = await res.json();
    cachedSandboxData = sb || {};

    const setVal = (id, v) => {
      const el = document.getElementById(id);
      if (el && v !== undefined && v !== null) el.value = v;
    };

    if (sb.ZombieLore) {
      setVal('sb-ZombieLore-Speed', sb.ZombieLore.Speed);
      setVal('sb-ZombieLore-Strength', sb.ZombieLore.Strength);
      setVal('sb-ZombieLore-Toughness', sb.ZombieLore.Toughness);
      setVal('sb-ZombieLore-Transmission', sb.ZombieLore.Transmission);
      setVal('sb-ZombieLore-Mortality', sb.ZombieLore.Mortality);
      setVal('sb-ZombieLore-Reanimate', sb.ZombieLore.Reanimate);
      setVal('sb-ZombieLore-Cognition', sb.ZombieLore.Cognition);
    }
    if (sb.Loot) {
      setVal('sb-Loot-Food', sb.Loot.Food);
      setVal('sb-Loot-Weapon', sb.Loot.Weapon);
      setVal('sb-Loot-Literature', sb.Loot.Literature);
      setVal('sb-Loot-Medical', sb.Loot.Medical);
      setVal('sb-Loot-SurvivalGears', sb.Loot.SurvivalGears);
      setVal('sb-Loot-Mechanics', sb.Loot.Mechanics);
      setVal('sb-Loot-Other', sb.Loot.Other);
    }
    setVal('sb-WaterShut', sb.WaterShut);
    setVal('sb-ElecShut', sb.ElecShut);
    setVal('sb-CarSpawnRate', sb.CarSpawnRate);
    setVal('sb-InitialGas', sb.InitialGas);
    setVal('sb-XpMultiplier', sb.XpMultiplier);
  } catch (e) {
    console.error('Load sandbox error:', e);
  }
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

  const sb = { ...cachedSandboxData };

  sb.ZombieLore = {
    ...(sb.ZombieLore || {}),
    Speed: getInt('sb-ZombieLore-Speed', 2),
    Strength: getInt('sb-ZombieLore-Strength', 2),
    Toughness: getInt('sb-ZombieLore-Toughness', 2),
    Transmission: getInt('sb-ZombieLore-Transmission', 1),
    Mortality: getInt('sb-ZombieLore-Mortality', 5),
    Reanimate: getInt('sb-ZombieLore-Reanimate', 3),
    Cognition: getInt('sb-ZombieLore-Cognition', 3),
  };

  sb.Loot = {
    ...(sb.Loot || {}),
    Food: getInt('sb-Loot-Food', 3),
    Weapon: getInt('sb-Loot-Weapon', 3),
    Literature: getInt('sb-Loot-Literature', 3),
    Medical: getInt('sb-Loot-Medical', 3),
    SurvivalGears: getInt('sb-Loot-SurvivalGears', 3),
    Mechanics: getInt('sb-Loot-Mechanics', 3),
    Other: getInt('sb-Loot-Other', 3),
  };

  if (document.getElementById('sb-WaterShut')) sb.WaterShut = getInt('sb-WaterShut', 2);
  if (document.getElementById('sb-ElecShut')) sb.ElecShut = getInt('sb-ElecShut', 2);
  if (document.getElementById('sb-CarSpawnRate')) sb.CarSpawnRate = getInt('sb-CarSpawnRate', 3);
  if (document.getElementById('sb-InitialGas')) sb.InitialGas = getInt('sb-InitialGas', 2);
  if (document.getElementById('sb-XpMultiplier')) sb.XpMultiplier = getFloat('sb-XpMultiplier', 1.0);

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

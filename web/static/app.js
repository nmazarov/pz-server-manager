// ── Global State & Auth ──────────────────────────────────────────
let currentToken = localStorage.getItem('pz_token') || '';
let ws = null;
let selectedPlayer = null;
let currentSandboxData = {};
let currentSandboxMeta = {};

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
  pollStatus();
  setInterval(pollStatus, 4000);
  setInterval(pollMetrics, 3000);
  setInterval(() => {
    const srvPanel = document.getElementById('tab-server');
    if (srvPanel && srvPanel.classList.contains('active')) {
      refreshPlayers(true);
    }
  }, 5000);
  loadWatchdog();
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

// ── Metrics & Status Polling ──────────────────────────────────────
async function pollStatus() {
  try {
    const res = await fetch('/api/status', { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    const badgeStatus = document.getElementById('badge-status');
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnRestart = document.getElementById('btn-restart');

    if (data.is_running) {
      badgeStatus.className = 'badge online';
      badgeStatus.textContent = '🟢 Работает (PID ' + (data.pid || '') + ')';
      if (btnStart) btnStart.disabled = true;
      if (btnStop) btnStop.disabled = false;
      if (btnRestart) btnRestart.disabled = false;
    } else {
      badgeStatus.className = 'badge offline';
      badgeStatus.textContent = '🔴 Остановлен';
      if (btnStart) btnStart.disabled = false;
      if (btnStop) btnStop.disabled = true;
      if (btnRestart) btnRestart.disabled = true;
    }

    const badgeVer = document.getElementById('badge-version');
    if (badgeVer) {
      badgeVer.textContent = '🎯 Build ' + (data.target_version || '42');
    }
  } catch (e) {
    console.error('pollStatus error:', e);
  }
}

async function pollMetrics() {
  try {
    const res = await fetch('/api/metrics', { headers: getHeaders() });
    if (!res.ok) return;
    const m = await res.json();
    updateMetrics(m);
  } catch (e) {}
}

function updateMetrics(m) {
  if (!m) return;
  const bVPS = document.getElementById('badge-vps-ram');
  if (bVPS && m.vps_ram_used_gb !== undefined) {
    bVPS.textContent = `🖥️ VPS RAM: ${m.vps_ram_used_gb} / ${m.vps_ram_total_gb} GB (${m.vps_ram_percent}%)`;
  }
  const bSrv = document.getElementById('badge-srv-ram');
  if (bSrv && m.server_process_ram_mb !== undefined) {
    bSrv.textContent = `🎮 Server RAM: ${m.server_process_ram_mb} MB`;
  }
}

// ── Server Controls ───────────────────────────────────────────────
async function startServer() {
  const name = document.getElementById('srv-name')?.value.trim() || 'servertest';
  const ram = parseInt(document.getElementById('srv-ram')?.value || '6');

  const btnStart = document.getElementById('btn-start');
  if (btnStart) btnStart.disabled = true;

  try {
    const res = await fetch('/api/server/start', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ name: name, ram: ram })
    });
    const d = await res.json();
    if (!d.success) {
      alert('Ошибка запуска: ' + d.message);
      if (btnStart) btnStart.disabled = false;
    } else {
      setTimeout(pollStatus, 1000);
    }
  } catch (e) {
    alert('Сетевая ошибка запуска');
    if (btnStart) btnStart.disabled = false;
  }
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

// ── Watchdog Management ───────────────────────────────────────────
async function loadWatchdog() {
  try {
    const res = await fetch('/api/watchdog', { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const chk = document.getElementById('watchdog-chk');
    if (chk) chk.checked = !!data.enabled;
  } catch (e) {}
}

async function toggleWatchdog(enabled) {
  try {
    await fetch('/api/watchdog/toggle', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ enabled: !!enabled })
    });
  } catch (e) {}
}

// ── Live Player Dashboard ─────────────────────────────────────────
async function refreshPlayers(silent = false) {
  try {
    const res = await fetch('/api/players', { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    const listEl = document.getElementById('player-list');
    const countBadge = document.getElementById('player-count-badge');
    const players = data.players || [];

    if (countBadge) countBadge.textContent = players.length;

    if (!listEl) return;

    if (players.length === 0) {
      listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; text-align: center; margin-top: 30px;">Нет подключенных игроков</div>';
      selectedPlayer = null;
      updateSelectedPlayerLabel();
      return;
    }

    listEl.innerHTML = '';
    players.forEach(p => {
      const item = document.createElement('div');
      item.className = 'player-item' + (selectedPlayer === p ? ' selected' : '');
      item.innerHTML = `<span>👤 <b>${p}</b></span><span style="font-size: 11px; color: #81c784;">🟢 Online</span>`;
      item.onclick = () => {
        document.querySelectorAll('.player-item').forEach(el => el.classList.remove('selected'));
        item.classList.add('selected');
        selectedPlayer = p;
        updateSelectedPlayerLabel();
      };
      listEl.appendChild(item);
    });

    if (selectedPlayer && !players.includes(selectedPlayer)) {
      selectedPlayer = null;
      updateSelectedPlayerLabel();
    }
  } catch (e) {
    if (!silent) console.error('refreshPlayers error:', e);
  }
}

function updateSelectedPlayerLabel() {
  const lbl = document.getElementById('selected-player-name');
  if (lbl) {
    lbl.textContent = selectedPlayer || '—';
  }
}

async function playerAction(act) {
  if (!selectedPlayer && act !== 'refresh') {
    alert('Пожалуйста, сначала выберите игрока из списка!');
    return;
  }

  let reason = 'Действие администратора';
  let target = '';
  let level = 'admin';

  if (act === 'kick') {
    const r = prompt(`Укажите причину кика для ${selectedPlayer}:`, 'Нарушение правил сервера');
    if (r === null) return;
    reason = r.trim() || 'Kicked by admin';
  } else if (act === 'ban') {
    const r = prompt(`Укажите причину блокировки для ${selectedPlayer}:`, 'Читерство или нарушение правил');
    if (r === null) return;
    reason = r.trim() || 'Banned by admin';
  } else if (act === 'teleport') {
    const t = prompt(`К кому телепортировать игрока ${selectedPlayer}? (Оставьте пустым, чтобы телепортировать к администратору):`);
    if (t === null) return;
    target = t.trim();
  } else if (act === 'admin') {
    const l = prompt(`Укажите уровень доступа для ${selectedPlayer} (admin, moderator, observer, none):`, 'admin');
    if (l === null) return;
    level = l.trim() || 'admin';
  }

  try {
    const res = await fetch('/api/players/action', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        action: act,
        player: selectedPlayer,
        target: target,
        reason: reason,
        level: level
      })
    });
    const d = await res.json();
    if (d.success) {
      alert(`Действие "${act}" успешно выполнено!`);
      setTimeout(refreshPlayers, 1000);
    } else {
      alert('Ошибка: ' + (d.message || 'Не удалось выполнить действие'));
    }
  } catch (e) {
    alert('Сетевая ошибка при выполнении действия над игроком');
  }
}

// ── Settings (servertest.ini) ─────────────────────────────────────
async function loadSettings() {
  try {
    const res = await fetch('/api/settings', { headers: getHeaders() });
    if (!res.ok) return;
    const c = await res.json();

    for (const [key, val] of Object.entries(c)) {
      const el = document.getElementById('ini-' + key);
      if (!el) continue;

      if (el.type === 'checkbox') {
        el.checked = (String(val).toLowerCase() === 'true');
      } else {
        el.value = val;
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

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data)
    });
    const resData = await res.json();
    if (resData.success) {
      alert('✅ Настройки сервера (servertest.ini) успешно сохранены!');
    } else {
      alert('Ошибка сохранения настроек: ' + resData.message);
    }
  } catch (e) {
    alert('Сетевая ошибка при сохранении настроек');
  }
}

// ── Sandbox (servertest_SandboxVars.lua) ───────────────────────────
async function loadSandbox() {
  try {
    const res = await fetch('/api/sandbox/full', { headers: getHeaders() });
    if (!res.ok) return;
    const json = await res.json();
    currentSandboxData = json.vars || {};
    currentSandboxMeta = json.meta || {};

    const sb = currentSandboxData;

    // 1. ZombieLore
    const zl = sb.ZombieLore || {};
    setVal('sb-ZombieLore-Speed', zl.Speed, 3);
    setVal('sb-ZombieLore-Strength', zl.Strength, 2);
    setVal('sb-ZombieLore-Toughness', zl.Toughness, 2);
    setVal('sb-ZombieLore-Transmission', zl.Transmission, 1);
    setVal('sb-ZombieLore-Mortality', zl.Mortality, 6);
    setVal('sb-ZombieLore-Cognition', zl.Cognition, 3);
    setVal('sb-ZombieLore-Memory', zl.Memory, 2);
    setVal('sb-ZombieLore-Sight', zl.Sight, 2);
    setVal('sb-ZombieLore-Hearing', zl.Hearing, 2);
    setVal('sb-ZombieLore-Smell', zl.Smell, 2);
    setVal('sb-ZombieLore-Active', zl.Active, 1);
    setVal('sb-ZombieLore-Distribution', zl.Distribution, 1);
    setChk('sb-ZombieLore-ThumpNoChasing', zl.ThumpNoChasing);
    setChk('sb-ZombieLore-ThumpOnConstruction', zl.ThumpOnConstruction !== false);
    setChk('sb-ZombieLore-TriggerHouseAlarm', zl.TriggerHouseAlarm);

    // 2. ZombieConfig
    const zc = sb.ZombieConfig || {};
    setVal('sb-ZombieConfig-PopulationMultiplier', zc.PopulationMultiplier, 1.0);
    setVal('sb-ZombieConfig-PopulationStartMultiplier', zc.PopulationStartMultiplier, 1.0);
    setVal('sb-ZombieConfig-PopulationPeakMultiplier', zc.PopulationPeakMultiplier, 1.5);
    setVal('sb-ZombieConfig-PopulationPeakDay', zc.PopulationPeakDay, 28);
    setVal('sb-ZombieConfig-RespawnHours', zc.RespawnHours, 72);
    setVal('sb-ZombieConfig-RespawnUnseenHours', zc.RespawnUnseenHours, 16);
    setVal('sb-ZombieConfig-RespawnMultiplier', zc.RespawnMultiplier, 0.1);
    setVal('sb-ZombieConfig-RallyGroupSize', zc.RallyGroupSize, 20);

    // 3. Loot
    setVal('sb-WeaponLoot', sb.WeaponLoot, 2);
    setVal('sb-RangedWeaponLoot', sb.RangedWeaponLoot, 2);
    setVal('sb-AmmoLoot', sb.AmmoLoot, 2);
    setVal('sb-FoodLoot', sb.FoodLoot, 3);
    setVal('sb-CannedFoodLoot', sb.CannedFoodLoot, 2);
    setVal('sb-MedicalLoot', sb.MedicalLoot, 2);
    setVal('sb-LiteratureLoot', sb.LiteratureLoot, 2);
    setVal('sb-SurvivalGearsLoot', sb.SurvivalGearsLoot, 2);
    setVal('sb-MechanicsLoot', sb.MechanicsLoot, 2);
    setVal('sb-OtherLoot', sb.OtherLoot, 3);

    setVal('sb-HoursForLootRespawn', sb.HoursForLootRespawn || (sb.Loot && sb.Loot.HoursForLootRespawn), 0);
    setVal('sb-MaxItemsForLootRespawn', sb.MaxItemsForLootRespawn || (sb.Loot && sb.Loot.MaxItemsForLootRespawn), 4);
    setChk('sb-ConstructionPreventsLootRespawn', sb.ConstructionPreventsLootRespawn !== false);
    setVal('sb-WaterShutModifier', sb.WaterShutModifier !== undefined ? sb.WaterShutModifier : (sb.WaterShut || 14), 14);
    setVal('sb-ElecShutModifier', sb.ElecShutModifier !== undefined ? sb.ElecShutModifier : (sb.ElecShut || 14), 14);

    // 4. World & Time
    const gt = sb.GameTime || {};
    setVal('sb-DayLength', sb.DayLength || gt.DayLength, 3);
    setVal('sb-StartYear', sb.StartYear || gt.StartYear, 1);
    setVal('sb-StartMonth', sb.StartMonth || gt.StartMonth, 7);
    setVal('sb-StartDay', sb.StartDay || gt.StartDay, 9);
    setVal('sb-StartTime', sb.StartTime || gt.StartTime, 2);
    setVal('sb-NightDarkness', sb.NightDarkness || gt.NightDarkness, 3);
    setVal('sb-TimeSinceApo', sb.TimeSinceApo || gt.TimeSinceApo, 1);

    setChk('sb-FireSpread', sb.FireSpread !== false);
    setVal('sb-NatureAbundance', sb.NatureAbundance, 3);
    setVal('sb-Helicopter', sb.Helicopter, 2);
    setVal('sb-MetaEvent', sb.MetaEvent, 2);
    setVal('sb-SleepingEvent', sb.SleepingEvent, 2);
    setVal('sb-ErosionSpeed', sb.ErosionSpeed, 3);
    setVal('sb-ErosionDays', sb.ErosionDays, 100);
    setVal('sb-GeneratorSpawning', sb.GeneratorSpawning, 3);
    setVal('sb-GeneratorFuelConsumption', sb.GeneratorFuelConsumption, 1.0);

    // 5. Vehicles
    const cars = sb.Cars || {};
    setVal('sb-CarSpawnRate', sb.CarSpawnRate || cars.CarSpawnRate, 4);
    setVal('sb-CarGeneralCondition', sb.CarGeneralCondition || cars.CarGeneralCondition, 3);
    setVal('sb-ChanceHasGas', sb.ChanceHasGas || cars.ChanceHasGas, 3);
    setVal('sb-InitialGas', sb.InitialGas || cars.InitialGas, 2);
    setVal('sb-CarGasConsumption', sb.CarGasConsumption || cars.CarGasConsumption, 1.0);
    setVal('sb-CarAlarm', sb.CarAlarm || cars.CarAlarm, 3);
    setChk('sb-VehicleEasyUse', sb.VehicleEasyUse || cars.VehicleEasyUse);
    setChk('sb-TrafficJam', sb.TrafficJam !== false && cars.TrafficJam !== false);
    setChk('sb-PlayerDamagedFromCarCrash', sb.PlayerDamagedFromCarCrash !== false && cars.PlayerDamagedFromCarCrash !== false);

    // 6. Character
    setVal('sb-XPMultiplier', sb.XPMultiplier, 1.0);
    setVal('sb-FreePoints', sb.FreePoints, 0);
    setVal('sb-DamageToPlayer', sb.DamageToPlayer, 3);
    setVal('sb-FarmingSpeed', sb.FarmingSpeed || sb.Farming, 3);
    setVal('sb-PlantResilience', sb.PlantResilience, 3);
    setVal('sb-PlantAbundance', sb.PlantAbundance, 3);

    // 7. Dynamic Mod Options
    renderModOptions(sb, currentSandboxMeta);

  } catch (e) {
    console.error('loadSandbox error:', e);
  }
}

function setVal(id, val, def) {
  const el = document.getElementById(id);
  if (!el) return;
  if (val !== undefined && val !== null) {
    el.value = val;
  } else if (def !== undefined) {
    el.value = def;
  }
}

function setChk(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  el.checked = !!val;
}

function renderModOptions(sb, meta) {
  const container = document.getElementById('sandbox-mod-options-container');
  if (!container) return;

  const vanillaTables = new Set(['ZombieLore', 'ZombieConfig', 'MultiplierConfig', 'Map', 'Basement', 'SandboxVars', 'Loot', 'GameTime', 'Cars', 'Farming']);
  const modTables = Object.keys(sb).filter(k => typeof sb[k] === 'object' && sb[k] !== null && !vanillaTables.has(k)).sort();

  if (modTables.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; padding: 24px; text-align: center;">В файле SandboxVars.lua пока нет таблиц кастомных модов. Они появятся здесь автоматически при подключении модов, поддерживающих настройки песочницы.</div>';
    return;
  }

  container.innerHTML = '';
  modTables.forEach(tableName => {
    const tableData = sb[tableName];
    const box = document.createElement('div');
    box.className = 'form-group-box sb-group';
    box.setAttribute('data-title', tableName);

    let html = `<h4>🧩 ${tableName}</h4><div class="form-grid-2">`;
    Object.keys(tableData).forEach(key => {
      const val = tableData[key];
      const metaDesc = meta[`${tableName}.${key}`] || '';
      const inputId = `modopt-${tableName}-${key}`;

      html += `<div class="form-group sb-field" style="margin-bottom: 10px;">`;
      html += `<label style="font-weight: bold; font-size: 13px;">${key}:</label>`;

      if (typeof val === 'boolean') {
        html += `<div style="margin-top: 4px;"><label class="checkbox-tile">
                  <input type="checkbox" id="${inputId}" class="modopt-input" data-table="${tableName}" data-key="${key}" ${val ? 'checked' : ''}>
                  <span>Включено</span>
                  </label></div>`;
      } else if (typeof val === 'number') {
        const step = Number.isInteger(val) ? '1' : '0.1';
        html += `<input type="number" id="${inputId}" class="form-control modopt-input" data-table="${tableName}" data-key="${key}" value="${val}" step="${step}">`;
      } else {
        html += `<input type="text" id="${inputId}" class="form-control modopt-input" data-table="${tableName}" data-key="${key}" value="${val}">`;
      }

      if (metaDesc) {
        html += `<div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">${metaDesc}</div>`;
      }
      html += `</div>`;
    });
    html += `</div>`;
    box.innerHTML = html;
    container.appendChild(box);
  });
}

async function saveSandbox() {
  const sb = {
    WeaponLoot: parseInt(document.getElementById('sb-WeaponLoot')?.value || '2'),
    RangedWeaponLoot: parseInt(document.getElementById('sb-RangedWeaponLoot')?.value || '2'),
    AmmoLoot: parseInt(document.getElementById('sb-AmmoLoot')?.value || '2'),
    FoodLoot: parseInt(document.getElementById('sb-FoodLoot')?.value || '3'),
    CannedFoodLoot: parseInt(document.getElementById('sb-CannedFoodLoot')?.value || '2'),
    MedicalLoot: parseInt(document.getElementById('sb-MedicalLoot')?.value || '2'),
    LiteratureLoot: parseInt(document.getElementById('sb-LiteratureLoot')?.value || '2'),
    SurvivalGearsLoot: parseInt(document.getElementById('sb-SurvivalGearsLoot')?.value || '2'),
    MechanicsLoot: parseInt(document.getElementById('sb-MechanicsLoot')?.value || '2'),
    OtherLoot: parseInt(document.getElementById('sb-OtherLoot')?.value || '3'),

    HoursForLootRespawn: parseInt(document.getElementById('sb-HoursForLootRespawn')?.value || '0'),
    MaxItemsForLootRespawn: parseInt(document.getElementById('sb-MaxItemsForLootRespawn')?.value || '4'),
    ConstructionPreventsLootRespawn: document.getElementById('sb-ConstructionPreventsLootRespawn')?.checked,
    WaterShutModifier: parseInt(document.getElementById('sb-WaterShutModifier')?.value || '14'),
    ElecShutModifier: parseInt(document.getElementById('sb-ElecShutModifier')?.value || '14'),
    WaterShut: parseInt(document.getElementById('sb-WaterShutModifier')?.value || '14'),
    ElecShut: parseInt(document.getElementById('sb-ElecShutModifier')?.value || '14'),

    DayLength: parseInt(document.getElementById('sb-DayLength')?.value || '3'),
    StartYear: parseInt(document.getElementById('sb-StartYear')?.value || '1'),
    StartMonth: parseInt(document.getElementById('sb-StartMonth')?.value || '7'),
    StartDay: parseInt(document.getElementById('sb-StartDay')?.value || '9'),
    StartTime: parseInt(document.getElementById('sb-StartTime')?.value || '2'),
    NightDarkness: parseInt(document.getElementById('sb-NightDarkness')?.value || '3'),
    TimeSinceApo: parseInt(document.getElementById('sb-TimeSinceApo')?.value || '1'),

    FireSpread: document.getElementById('sb-FireSpread')?.checked,
    NatureAbundance: parseInt(document.getElementById('sb-NatureAbundance')?.value || '3'),
    Helicopter: parseInt(document.getElementById('sb-Helicopter')?.value || '2'),
    MetaEvent: parseInt(document.getElementById('sb-MetaEvent')?.value || '2'),
    SleepingEvent: parseInt(document.getElementById('sb-SleepingEvent')?.value || '2'),
    ErosionSpeed: parseInt(document.getElementById('sb-ErosionSpeed')?.value || '3'),
    ErosionDays: parseInt(document.getElementById('sb-ErosionDays')?.value || '100'),
    GeneratorSpawning: parseInt(document.getElementById('sb-GeneratorSpawning')?.value || '3'),
    GeneratorFuelConsumption: parseFloat(document.getElementById('sb-GeneratorFuelConsumption')?.value || '1.0'),

    CarSpawnRate: parseInt(document.getElementById('sb-CarSpawnRate')?.value || '4'),
    CarGeneralCondition: parseInt(document.getElementById('sb-CarGeneralCondition')?.value || '3'),
    ChanceHasGas: parseInt(document.getElementById('sb-ChanceHasGas')?.value || '3'),
    InitialGas: parseInt(document.getElementById('sb-InitialGas')?.value || '2'),
    CarGasConsumption: parseFloat(document.getElementById('sb-CarGasConsumption')?.value || '1.0'),
    CarAlarm: parseInt(document.getElementById('sb-CarAlarm')?.value || '3'),
    VehicleEasyUse: document.getElementById('sb-VehicleEasyUse')?.checked,
    TrafficJam: document.getElementById('sb-TrafficJam')?.checked,
    PlayerDamagedFromCarCrash: document.getElementById('sb-PlayerDamagedFromCarCrash')?.checked,

    XPMultiplier: parseFloat(document.getElementById('sb-XPMultiplier')?.value || '1.0'),
    FreePoints: parseInt(document.getElementById('sb-FreePoints')?.value || '0'),
    DamageToPlayer: parseInt(document.getElementById('sb-DamageToPlayer')?.value || '3'),
    FarmingSpeed: parseInt(document.getElementById('sb-FarmingSpeed')?.value || '3'),
    Farming: parseInt(document.getElementById('sb-FarmingSpeed')?.value || '3'),
    PlantResilience: parseInt(document.getElementById('sb-PlantResilience')?.value || '3'),
    PlantAbundance: parseInt(document.getElementById('sb-PlantAbundance')?.value || '3'),

    ZombieLore: {
      Speed: parseInt(document.getElementById('sb-ZombieLore-Speed')?.value || '3'),
      Strength: parseInt(document.getElementById('sb-ZombieLore-Strength')?.value || '2'),
      Toughness: parseInt(document.getElementById('sb-ZombieLore-Toughness')?.value || '2'),
      Transmission: parseInt(document.getElementById('sb-ZombieLore-Transmission')?.value || '1'),
      Mortality: parseInt(document.getElementById('sb-ZombieLore-Mortality')?.value || '6'),
      Cognition: parseInt(document.getElementById('sb-ZombieLore-Cognition')?.value || '3'),
      Memory: parseInt(document.getElementById('sb-ZombieLore-Memory')?.value || '2'),
      Sight: parseInt(document.getElementById('sb-ZombieLore-Sight')?.value || '2'),
      Hearing: parseInt(document.getElementById('sb-ZombieLore-Hearing')?.value || '2'),
      Smell: parseInt(document.getElementById('sb-ZombieLore-Smell')?.value || '2'),
      Active: parseInt(document.getElementById('sb-ZombieLore-Active')?.value || '1'),
      Distribution: parseInt(document.getElementById('sb-ZombieLore-Distribution')?.value || '1'),
      ThumpNoChasing: document.getElementById('sb-ZombieLore-ThumpNoChasing')?.checked,
      ThumpOnConstruction: document.getElementById('sb-ZombieLore-ThumpOnConstruction')?.checked,
      TriggerHouseAlarm: document.getElementById('sb-ZombieLore-TriggerHouseAlarm')?.checked,
    },
    ZombieConfig: {
      PopulationMultiplier: parseFloat(document.getElementById('sb-ZombieConfig-PopulationMultiplier')?.value || '1.0'),
      PopulationStartMultiplier: parseFloat(document.getElementById('sb-ZombieConfig-PopulationStartMultiplier')?.value || '1.0'),
      PopulationPeakMultiplier: parseFloat(document.getElementById('sb-ZombieConfig-PopulationPeakMultiplier')?.value || '1.5'),
      PopulationPeakDay: parseInt(document.getElementById('sb-ZombieConfig-PopulationPeakDay')?.value || '28'),
      RespawnHours: parseInt(document.getElementById('sb-ZombieConfig-RespawnHours')?.value || '72'),
      RespawnUnseenHours: parseInt(document.getElementById('sb-ZombieConfig-RespawnUnseenHours')?.value || '16'),
      RespawnMultiplier: parseFloat(document.getElementById('sb-ZombieConfig-RespawnMultiplier')?.value || '0.1'),
      RallyGroupSize: parseInt(document.getElementById('sb-ZombieConfig-RallyGroupSize')?.value || '20'),
    }
  };

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

  try {
    const res = await fetch('/api/sandbox', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(sb)
    });
    const resData = await res.json();
    if (resData.success) {
      alert('✅ Параметры песочницы мира (SandboxVars.lua) успешно сохранены!');
    } else {
      alert('Ошибка сохранения Sandbox: ' + resData.message);
    }
  } catch (e) {
    alert('Сетевая ошибка сохранения параметров песочницы');
  }
}

function applySandboxPreset(preset) {
  if (!preset) return;
  const p = preset.toLowerCase();

  if (p === 'apocalypse') {
    setVal('sb-ZombieConfig-PopulationMultiplier', 1.5);
    setVal('sb-ZombieLore-Speed', 2); // fast shamblers
    setVal('sb-ZombieLore-Strength', 2);
    setVal('sb-ZombieLore-Toughness', 2);
    setVal('sb-WeaponLoot', 1);
    setVal('sb-FoodLoot', 1);
    setVal('sb-OtherLoot', 1);
    setVal('sb-XPMultiplier', 1.0);
    setVal('sb-DamageToPlayer', 4); // high
  } else if (p === 'survivor') {
    setVal('sb-ZombieConfig-PopulationMultiplier', 1.0);
    setVal('sb-ZombieLore-Speed', 2);
    setVal('sb-ZombieLore-Strength', 2);
    setVal('sb-ZombieLore-Toughness', 2);
    setVal('sb-WeaponLoot', 2);
    setVal('sb-FoodLoot', 2);
    setVal('sb-XPMultiplier', 1.0);
    setVal('sb-DamageToPlayer', 3);
  } else if (p === 'builder') {
    setVal('sb-ZombieConfig-PopulationMultiplier', 0.35);
    setVal('sb-ZombieLore-Speed', 3); // shamblers
    setVal('sb-ZombieLore-Strength', 3); // weak
    setVal('sb-ZombieLore-Toughness', 3); // fragile
    setVal('sb-WeaponLoot', 4); // common
    setVal('sb-FoodLoot', 4);
    setVal('sb-XPMultiplier', 1.5);
    setVal('sb-DamageToPlayer', 1); // very low
  } else if (p === 'infection') {
    setVal('sb-ZombieConfig-PopulationMultiplier', 0.5);
    setVal('sb-ZombieLore-Transmission', 1);
    setVal('sb-ZombieLore-Mortality', 1); // instant
    setVal('sb-FoodLoot', 4);
    setVal('sb-WaterShutModifier', 30);
    setVal('sb-ElecShutModifier', 30);
  } else if (p === 'sixmonths') {
    setVal('sb-ZombieConfig-PopulationMultiplier', 2.0);
    setVal('sb-TimeSinceApo', 2); // 3-6 months
    setVal('sb-ErosionDays', 0);
    setVal('sb-NatureAbundance', 4);
    setVal('sb-FoodLoot', 1);
    setVal('sb-WaterShutModifier', 0);
    setVal('sb-ElecShutModifier', 0);
  }

  alert(`Применен пресет сложности: "${preset}"! Не забудьте нажать "Сохранить Sandbox".`);
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

async function deleteBackup(filename) {
  if (!confirm(`Удалить архив "${filename}" безвозвратно?`)) return;

  try {
    const res = await fetch('/api/backups/' + encodeURIComponent(filename), {
      method: 'DELETE',
      headers: getHeaders()
    });
    const d = await res.json();
    if (d.success) {
      loadBackups();
    } else {
      alert('Ошибка удаления: ' + (d.message || ''));
    }
  } catch (e) {
    alert('Ошибка удаления архива');
  }
}

// ── Mods Management ───────────────────────────────────────────────
let currentModsList = [];

async function loadMods() {
  try {
    const res = await fetch('/api/mods', { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    currentModsList = Array.isArray(data) ? data : (data.mods || []);
    renderMods(currentModsList);
  } catch (e) {
    console.error('loadMods error:', e);
  }
}

function renderMods(mods) {
  const container = document.getElementById('mods-container');
  if (!container) return;

  if (!Array.isArray(mods) || mods.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 24px;">Моды не добавлены. Введите Workshop ID, ссылку на коллекцию Steam или выберите готовый набор выше.</div>';
    return;
  }

  let html = `<div style="margin-bottom: 8px; font-size: 12.5px; color: var(--text-muted);">Всего подключено модов: <b>${mods.length}</b></div>
  <table class="data-table">
    <thead>
      <tr>
        <th style="width: 50px;">СТАТУС</th>
        <th>WORKSHOP ID</th>
        <th>НАЗВАНИЕ МОДА</th>
        <th style="text-align: right;">УПРАВЛЕНИЕ</th>
      </tr>
    </thead>
    <tbody>`;

  mods.forEach((m, idx) => {
    let dot = '🟢';
    if (m.status === 'incompatible') dot = '🔴';
    else if (m.status === 'warning' || m.status === 'unknown') dot = '🟡';

    const wid = m.workshop_id || m.mod_id || '--';
    const name = m.name || ('Workshop Item ' + wid);
    const reason = m.reason ? ` title="${m.reason.replace(/"/g, '&quot;')}"` : '';

    html += `<tr>
      <td style="font-size: 16px; text-align: center;"${reason}>${dot}</td>
      <td style="font-family: var(--font-mono); font-size: 12px; color: #ffb74d;">${wid}</td>
      <td><b>${name}</b></td>
      <td style="text-align: right; white-space: nowrap;">
        <button class="btn btn-secondary" onclick="moveMod(${idx}, -1)" style="padding: 3px 8px; font-size: 11px;">⬆</button>
        <button class="btn btn-secondary" onclick="moveMod(${idx}, 1)" style="padding: 3px 8px; font-size: 11px;">⬇</button>
        <button class="btn btn-danger" onclick="removeMod(${idx})" style="padding: 3px 9px; font-size: 11px; margin-left: 6px;">✕</button>
      </td>
    </tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

async function addMod() {
  const inp = document.getElementById('mod-input-id');
  if (!inp) return;
  const val = inp.value.trim();
  if (!val) return;

  const btn = document.querySelector("button[onclick='addMod()']");
  if (btn) {
    btn.disabled = true;
    btn.textContent = '⏳ Добавление...';
  }

  try {
    const res = await fetch('/api/mods/add', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ id_or_url: val })
    });
    const d = await res.json();
    if (d.success) {
      inp.value = '';
      await loadMods();
      if (d.is_collection) {
        alert(d.message || 'Коллекция успешно импортирована!');
      }
    } else {
      alert('Ошибка при добавлении: ' + (d.message || 'Не удалось распознать ID или коллекцию'));
    }
  } catch (e) {
    alert('Сетевая ошибка при добавлении: ' + e);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = '➕ Добавить мод';
    }
  }
}

async function removeMod(idx) {
  if (idx < 0 || idx >= currentModsList.length) return;
  const m = currentModsList[idx];
  const wid = m.workshop_id || m.mod_id;
  try {
    const res = await fetch('/api/mods/remove', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ id_or_url: String(wid) })
    });
    if (res.ok) {
      await loadMods();
    }
  } catch (e) {
    console.error('removeMod error:', e);
  }
}

async function moveMod(idx, dir) {
  const newIdx = idx + dir;
  if (newIdx < 0 || newIdx >= currentModsList.length) return;
  const temp = currentModsList[idx];
  currentModsList[idx] = currentModsList[newIdx];
  currentModsList[newIdx] = temp;
  renderMods(currentModsList);
  await saveModsPayload(currentModsList);
}

async function saveMods() {
  try {
    const res = await fetch('/api/mods/save', {
      method: 'POST',
      headers: getHeaders()
    });
    const d = await res.json();
    if (d.success) {
      alert('Список модов успешно сохранен в конфигурации сервера!');
    } else {
      alert('Ошибка сохранения: ' + d.message);
    }
  } catch (e) {
    alert('Ошибка сохранения модов: ' + e);
  }
}

async function saveModsPayload(mods) {
  try {
    await fetch('/api/mods/save', {
      method: 'POST',
      headers: getHeaders()
    });
  } catch (e) {
    console.error('saveModsPayload error:', e);
  }
}

async function clearMods() {
  if (!confirm('Очистить весь список подключенных модов?')) return;
  try {
    const res = await fetch('/api/mods/clear', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ id_or_url: '' })
    });
    if (res.ok) {
      await loadMods();
    }
  } catch (e) {
    console.error('clearMods error:', e);
  }
}

async function checkAllModsCompatibility() {
  try {
    const res = await fetch('/api/mods/check', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ id_or_url: '' })
    });
    const d = await res.json();
    await loadMods();
    if (d.success) {
      alert(`Проверка завершена!\nВсего: ${d.total}\nСовместимо: ${d.compatible}\nПредупреждения: ${d.warning}\nНесовместимо: ${d.incompatible}`);
    }
  } catch (e) {
    alert('Ошибка при проверке совместимости: ' + e);
  }
}

async function analyzeMods() {
  try {
    const res = await fetch('/api/mods/analyze', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ id_or_url: '' })
    });
    const d = await res.json();
    if (d.success) {
      await loadMods();
      alert('Анализ завершен! Оптимальный порядок загрузки применен.');
    }
  } catch (e) {
    alert('Ошибка анализа зависимостей: ' + e);
  }
}

async function applyModPack(pack) {
  try {
    const res = await fetch('/api/mods/preset', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ action: pack })
    });
    const d = await res.json();
    if (d.success) {
      await loadMods();
      alert(`Набор "${pack}" успешно применен (добавлено модов: ${d.added || 0})!`);
    }
  } catch (e) {
    alert('Ошибка применения набора: ' + e);
  }
}

// ── Install & Steam Betas ─────────────────────────────────────────
async function checkSteamUpdate() {
  try {
    const res = await fetch('/api/install/check-update', { headers: getHeaders() });
    if (!res.ok) return;
    const d = await res.json();
    await loadInstallInfo();
    if (d.update_available) {
      alert(`Доступно обновление сервера!\nУстановленная версия: ${d.installed_version} (Build ${d.installed_buildid || '?'})\nНовейшая в Steam: ${d.latest_version} (Build ${d.latest_buildid})`);
    } else {
      alert(`Сервер обновлен до последней версии!\nТекущая версия: ${d.latest_version} (Build ${d.latest_buildid || 'Latest'})`);
    }
  } catch (e) {
    alert('Не удалось проверить обновления: ' + e);
  }
}

async function loadInstallInfo() {
  try {
    const res = await fetch('/api/install/branches', { headers: getHeaders() });
    if (!res.ok) return;
    const d = await res.json();
    const branches = Array.isArray(d) ? d : (d.branches || []);
    renderSteamBranches(branches);
  } catch (e) {
    console.error('Failed to load branches:', e);
  }
}

function renderSteamBranches(branches) {
  const container = document.getElementById('steam-branch-rows');
  if (!container) return;

  if (!Array.isArray(branches) || branches.length === 0) {
    container.innerHTML = '<div style="padding: 16px; color: #8f98a0; font-size: 13px;">Загрузка версий из Steam...</div>';
    return;
  }

  container.innerHTML = '';
  branches.forEach((b, idx) => {
    const row = document.createElement('div');
    const branchVal = b.branch !== undefined ? b.branch : (b.name === 'public' ? '' : b.name);
    const title = b.name_ru || b.name || b.key || 'Public';
    const desc = b.desc_ru || b.description || '';
    const date = b.date_str || b.date_ru || b.updated || 'Актуально';
    const buildId = b.buildid ? `Build ID: ${b.buildid}` : '';

    row.className = 'steam-branch-item';
    row.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 1px solid #223447; cursor: pointer; transition: background 0.15s;';

    const isSelected = idx === 0;
    if (isSelected) {
      row.style.background = '#2a475e';
      const inputEl = document.getElementById('install-branch');
      if (inputEl) inputEl.value = branchVal;
    }

    row.innerHTML = `
      <div>
        <div style="font-weight: 700; color: #fff; font-size: 13.5px; display: flex; align-items: center; gap: 8px;">
          <span>${title}</span>
          ${buildId ? `<span class="badge metric" style="font-size: 11px; padding: 1px 7px;">${buildId}</span>` : ''}
          ${isSelected ? `<span class="badge online" id="selected-branch-badge" style="font-size: 10px; padding: 1px 6px;">Выбрана</span>` : ''}
        </div>
        <div style="font-size: 12px; color: #8f98a0; margin-top: 4px;">${desc}</div>
      </div>
      <div style="font-size: 12px; color: #90caf9; font-weight: 600; text-align: right;">${date}</div>
    `;

    row.onclick = () => {
      document.querySelectorAll('#steam-branch-rows > div').forEach(el => {
        el.style.background = '';
        const badge = el.querySelector('#selected-branch-badge');
        if (badge) badge.remove();
      });
      row.style.background = '#2a475e';
      const titleEl = row.querySelector('div > div');
      if (titleEl && !titleEl.querySelector('#selected-branch-badge')) {
        titleEl.insertAdjacentHTML('beforeend', '<span class="badge online" id="selected-branch-badge" style="font-size: 10px; padding: 1px 6px;">Выбрана</span>');
      }
      const inputEl = document.getElementById('install-branch');
      if (inputEl) inputEl.value = branchVal;
    };
    container.appendChild(row);
  });
}

function checkBetaCode() {
  const branch = document.getElementById('beta-hidden-branch')?.value.trim();
  const code = document.getElementById('beta-access-code')?.value.trim();
  const msg = document.getElementById('beta-code-msg');

  if (!code) {
    alert('Пожалуйста, введите код доступа');
    return;
  }

  if (msg) {
    msg.textContent = 'Код принят!';
    msg.style.display = 'inline-block';
  }
}

async function startInstallation() {
  const branch = document.getElementById('install-branch')?.value.trim() || 'public';
  const pwd = document.getElementById('beta-access-code')?.value.trim() || '';

  if (!confirm(`Начать установку/обновление ветки "${branch}" через SteamCMD?`)) return;

  const btn = document.getElementById('btn-do-install');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch('/api/install/start', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ branch: branch, password: pwd })
    });
    const d = await res.json();
    if (d.success) {
      pollInstallProgress();
    } else {
      alert('Ошибка запуска SteamCMD: ' + d.message);
      if (btn) btn.disabled = false;
    }
  } catch (e) {
    alert('Сетевая ошибка при запуске установки');
    if (btn) btn.disabled = false;
  }
}

function pollInstallProgress() {
  const timer = setInterval(async () => {
    try {
      const res = await fetch('/api/install/status', { headers: getHeaders() });
      const st = await res.json();

      const pctEl = document.getElementById('install-status-pct');
      const fillEl = document.getElementById('install-progress-fill');
      const msgEl = document.getElementById('install-status-msg');
      const logEl = document.getElementById('install-log-output');

      if (pctEl) pctEl.textContent = (st.progress || 0) + '%';
      if (fillEl) fillEl.style.width = (st.progress || 0) + '%';
      if (msgEl) msgEl.textContent = st.message || 'Выполняется...';
      const logContent = Array.isArray(st.logs) ? st.logs.join('\n') : (st.log || '');
      if (logEl && logContent) {
        logEl.textContent = logContent;
        logEl.scrollTop = logEl.scrollHeight;
      }

      const isRunning = st.running || st.in_progress;
      if (!isRunning && st.progress !== undefined && st.progress > 0) {
        clearInterval(timer);
        const btn = document.getElementById('btn-do-install');
        if (btn) btn.disabled = false;
        if (st.progress >= 100) {
          alert('Установка/обновление сервера успешно завершено!');
        } else if (st.message && st.message.includes('Ошибка')) {
          alert('Установка завершилась с ошибкой: ' + st.message);
        }
      }
    } catch (e) {
      clearInterval(timer);
    }
  }, 1000);
}

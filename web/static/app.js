// 🧟 Project Zomboid Server Manager - Web Panel Client

let authToken = localStorage.getItem('pz_token') || '';
let ws = null;
let currentTab = 'server';
let isServerRunning = false;

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
    updateServerButtons(data.running);
    if (data.metrics) updateMetricsUI(data.metrics);
    if (data.target_version) {
      document.getElementById('badge-version').textContent = `🎯 Build ${data.target_version}`;
    }
  } catch (err) {
    console.error('Fetch status error:', err);
  }
}

function updateServerButtons(running) {
  const btnStart = document.getElementById('btn-start');
  const btnStop = document.getElementById('btn-stop');
  const btnRestart = document.getElementById('btn-restart');
  const badgeStatus = document.getElementById('badge-status');

  if (running) {
    btnStart.disabled = true;
    btnStop.disabled = false;
    btnRestart.disabled = false;
    badgeStatus.className = 'badge online';
    badgeStatus.textContent = '🟢 Работает';
  } else {
    btnStart.disabled = false;
    btnStop.disabled = true;
    btnRestart.disabled = true;
    badgeStatus.className = 'badge offline';
    badgeStatus.textContent = '🔴 Остановлен';
  }
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
  if (m.server_running !== undefined) {
    updateServerButtons(m.server_running);
  }
}

async function startServer() {
  const name = document.getElementById('srv-name').value.trim() || 'servertest';
  const ram = parseInt(document.getElementById('srv-ram').value) || 6;
  const res = await fetch('/api/server/start', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ server_name: name, ram_gb: ram })
  });
  const data = await res.json();
  if (!data.success) alert('Ошибка запуска сервера: ' + data.message);
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

// ── Settings (INI) ────────────────────────────────────────────────
async function loadSettings() {
  try {
    const res = await fetch('/api/settings', { headers: getHeaders() });
    const c = await res.json();
    for (const [key, val] of Object.entries(c)) {
      const el = document.getElementById('ini-' + key);
      if (el) el.value = val;
    }
  } catch (e) {
    console.error('Load settings error:', e);
  }
}

async function saveSettings() {
  const data = {};
  document.querySelectorAll('[id^="ini-"]').forEach(el => {
    const key = el.id.replace('ini-', '');
    data[key] = el.value;
  });

  const res = await fetch('/api/settings', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data)
  });
  const resData = await res.json();
  if (resData.success) {
    alert('Настройки сервера успешно сохранены!');
  } else {
    alert('Ошибка сохранения: ' + resData.message);
  }
}

// ── SandboxVars ───────────────────────────────────────────────────
async function loadSandbox() {
  try {
    const res = await fetch('/api/sandbox', { headers: getHeaders() });
    const sb = await res.json();

    if (sb.ZombieLore) {
      if (sb.ZombieLore.Speed) document.getElementById('sb-ZombieLore-Speed').value = sb.ZombieLore.Speed;
      if (sb.ZombieLore.Strength) document.getElementById('sb-ZombieLore-Strength').value = sb.ZombieLore.Strength;
      if (sb.ZombieLore.Toughness) document.getElementById('sb-ZombieLore-Toughness').value = sb.ZombieLore.Toughness;
      if (sb.ZombieLore.Transmission) document.getElementById('sb-ZombieLore-Transmission').value = sb.ZombieLore.Transmission;
    }
    if (sb.Loot) {
      if (sb.Loot.Food) document.getElementById('sb-Loot-Food').value = sb.Loot.Food;
      if (sb.Loot.Weapon) document.getElementById('sb-Loot-Weapon').value = sb.Loot.Weapon;
      if (sb.Loot.Literature) document.getElementById('sb-Loot-Literature').value = sb.Loot.Literature;
      if (sb.Loot.Medical) document.getElementById('sb-Loot-Medical').value = sb.Loot.Medical;
    }
  } catch (e) {
    console.error('Load sandbox error:', e);
  }
}

async function saveSandbox() {
  const sb = {
    ZombieLore: {
      Speed: parseInt(document.getElementById('sb-ZombieLore-Speed').value),
      Strength: parseInt(document.getElementById('sb-ZombieLore-Strength').value),
      Toughness: parseInt(document.getElementById('sb-ZombieLore-Toughness').value),
      Transmission: parseInt(document.getElementById('sb-ZombieLore-Transmission').value),
    },
    Loot: {
      Food: parseInt(document.getElementById('sb-Loot-Food').value),
      Weapon: parseInt(document.getElementById('sb-Loot-Weapon').value),
      Literature: parseInt(document.getElementById('sb-Loot-Literature').value),
      Medical: parseInt(document.getElementById('sb-Loot-Medical').value),
    }
  };

  const res = await fetch('/api/sandbox', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(sb)
  });
  const resData = await res.json();
  if (resData.success) {
    alert('Параметры Sandbox успешно сохранены!');
  } else {
    alert('Ошибка сохранения Sandbox: ' + resData.message);
  }
}

function applySandboxPreset(preset) {
  if (preset === 'apocalypse') {
    document.getElementById('sb-ZombieLore-Speed').value = '2';
    document.getElementById('sb-ZombieLore-Strength').value = '2';
    document.getElementById('sb-ZombieLore-Toughness').value = '2';
    document.getElementById('sb-Loot-Food').value = '2';
    document.getElementById('sb-Loot-Weapon').value = '2';
  } else if (preset === 'survivor') {
    document.getElementById('sb-ZombieLore-Speed').value = '2';
    document.getElementById('sb-ZombieLore-Strength').value = '2';
    document.getElementById('sb-Loot-Food').value = '3';
    document.getElementById('sb-Loot-Weapon').value = '3';
  } else if (preset === 'builder') {
    document.getElementById('sb-ZombieLore-Speed').value = '3';
    document.getElementById('sb-ZombieLore-Strength').value = '3';
    document.getElementById('sb-Loot-Food').value = '4';
    document.getElementById('sb-Loot-Weapon').value = '4';
  }
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

      item.innerHTML = `
        <div>
          <div class="mod-title">${m.name} <span style="color: var(--text-muted); font-size: 11px;">(ID: ${m.workshop_id})</span></div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">
            Mod IDs: ${m.mod_ids.join(', ') || 'none'}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="mod-badge ${badgeClass}">${badgeText}</span>
          <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="removeMod('${m.workshop_id}')">✕</button>
        </div>
      `;
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

      row.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <input type="radio" name="steam-branch-radio" value="${b.branch}" ${idx === 0 ? 'checked' : ''} style="cursor: pointer; width: 16px; height: 16px; accent-color: #67c1f5;">
          <div style="font-weight: bold; font-size: 13px; color: #fff;">${b.name_ru || b.name}</div>
          <div style="font-size: 12px; color: #8f98a0;">— ${b.desc_ru || b.description}</div>
        </div>
        <div style="font-size: 12px; color: #8f98a0; font-weight: normal; text-align: right;">
          ${b.date_ru || b.date_str || ''}
        </div>
      `;

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
      item.innerHTML = `
        <div>
          <div style="font-weight: bold; font-size: 13px;">📦 ${b.name}</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Размер архива: ${b.size_mb} MB</div>
        </div>
        <button class="btn btn-secondary" style="font-size: 12px;" onclick="restoreBackup('${b.name}')">Восстановить</button>
      `;
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
  setInterval(fetchStatus, 5000);
}

document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
});

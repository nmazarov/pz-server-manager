/**
 * Project Zomboid Interactive World Map
 * High-performance HTML5 Canvas renderer with pyramid tile streaming,
 * live player tracking, towns navigation, and admin teleportation.
 */

(function () {
  'use strict';

  let canvas = null;
  let ctx = null;
  let mapInfo = null;
  let playersData = [];
  let pollTimer = null;
  let animId = null;

  // Viewport State
  // Knox County bounds default: [0, 0, 19968, 16128]
  let cx = 10500;  // Center X in world coords
  let cy = 9500;   // Center Y in world coords
  let s = 0.045;   // Scale (screen pixels per world unit)
  let w = 800;
  let h = 600;

  // Interaction State
  let isDragging = false;
  let lastMouseX = 0;
  let lastMouseY = 0;
  let hoverPlayer = null;
  let selectedTarget = null; // { x, y, player }
  let targetPulse = 0;

  // Tile Cache
  const tileCache = new Map();
  const MAX_TILES = 1200;

  // Visibility filters
  const filters = {
    online: true,
    offline: true,
    dead: true,
    towns: true,
    grid: true
  };

  // Category visibility filters
  const categoryFilters = {
    police: true,
    guns: true,
    medical: true,
    fire: true,
    fuel: true,
    food: true,
    tools: true,
    bank: true,
    mechanics: true,
    clothing: true,
    electronics: true,
    books: true,
    church: true,
    office: true,
    residential: true
  };

  let poisData = [];
  const buildingsMap = new Map();
  let lastBuildingsQuery = null;
  let hoverBuilding = null;
  let hoverPoi = null;
  let buildingsFetchTimer = null;

  function getApiHeaders() {
    const token = localStorage.getItem('pz_token') || sessionStorage.getItem('pz_token');
    return token ? { 'Authorization': 'Bearer ' + token } : {};
  }

  function getTileImage(level, tx, ty) {
    const key = `${level}_${tx}_${ty}`;
    let item = tileCache.get(key);
    if (!item) {
      item = { img: new Image(), loaded: false, error: false };
      item.img.onload = () => {
        item.loaded = true;
        requestRedraw();
      };
      item.img.onerror = () => {
        item.error = true;
      };
      item.img.src = `/api/map/tile/${level}/${tx}/${ty}.png`;
      tileCache.set(key, item);

      if (tileCache.size > MAX_TILES) {
        const oldestKey = tileCache.keys().next().value;
        tileCache.delete(oldestKey);
      }
    }
    return item;
  }

  function toScreen(wx, wy) {
    return [
      (wx - cx) * s + w / 2,
      (wy - cy) * s + h / 2
    ];
  }

  function toWorld(sx, sy) {
    return [
      (sx - w / 2) / s + cx,
      (sy - h / 2) / s + cy
    ];
  }

  function selectZoomLevel() {
    // Zoom levels: 0 (most detailed, 256x256), 1, 2, 3, 4 (4096x4096 per tile)
    if (s >= 0.7) return 0;
    if (s >= 0.3) return 1;
    if (s >= 0.12) return 2;
    if (s >= 0.05) return 3;
    return 4;
  }

  function requestRedraw() {
    if (!animId) {
      animId = requestAnimationFrame(draw);
    }
  }

  function resizeCanvas() {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    w = rect.width || 800;
    h = rect.height || 600;

    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    requestRedraw();
  }

  function drawGrid() {
    if (!filters.grid) return;
    const bounds = (mapInfo && mapInfo.bounds) ? mapInfo.bounds : [0, 0, 19968, 16128];
    const [x0, y0, x1, y1] = bounds;
    const [sx0, sy0] = toScreen(x0, y0);
    const [sx1, sy1] = toScreen(x1, y1);

    // Map boundary border
    ctx.strokeStyle = '#38ef7d';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 4]);
    ctx.strokeRect(sx0, sy0, (x1 - x0) * s, (y1 - y0) * s);
    ctx.setLineDash([]);

    // Grid coordinates lines
    const step = s < 0.08 ? 2000 : (s < 0.25 ? 1000 : 500);
    const startX = Math.floor(x0 / step) * step;
    const startY = Math.floor(y0 / step) * step;

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    ctx.font = '10px Inter, monospace';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';

    for (let gx = startX; gx <= x1; gx += step) {
      const [gsx, gsy] = toScreen(gx, y0);
      if (gsx >= -20 && gsx <= w + 20) {
        ctx.beginPath();
        ctx.moveTo(gsx, Math.max(0, sy0));
        ctx.lineTo(gsx, Math.min(h, sy1));
        ctx.stroke();
        ctx.fillText(`${gx}`, gsx + 4, Math.max(16, sy0 + 14));
      }
    }

    for (let gy = startY; gy <= y1; gy += step) {
      const [gsx, gsy] = toScreen(x0, gy);
      if (gsy >= -20 && gsy <= h + 20) {
        ctx.beginPath();
        ctx.moveTo(Math.max(0, sx0), gsy);
        ctx.lineTo(Math.min(w, sx1), gsy);
        ctx.stroke();
        ctx.fillText(`${gy}`, Math.max(6, sx0 + 4), gsy - 4);
      }
    }
  }

  function drawLevel(L) {
    const [x0, y0, x1, y1] = mapInfo.bounds || [0, 0, 19968, 16128];
    const T = 256 * Math.pow(2, L);

    const [wx0, wy0] = toWorld(0, 0);
    const [wx1, wy1] = toWorld(w, h);

    const tx0 = Math.max(0, Math.floor((Math.min(wx0, wx1) - x0) / T));
    const ty0 = Math.max(0, Math.floor((Math.min(wy0, wy1) - y0) / T));
    const tx1 = Math.min(Math.ceil((x1 - x0) / T) - 1, Math.floor((Math.max(wx0, wx1) - x0) / T));
    const ty1 = Math.min(Math.ceil((y1 - y0) / T) - 1, Math.floor((Math.max(wy0, wy1) - y0) / T));

    for (let ty = ty0; ty <= ty1; ty++) {
      for (let tx = tx0; tx <= tx1; tx++) {
        const item = getTileImage(L, tx, ty);
        const [sx, sy] = toScreen(x0 + tx * T, y0 + ty * T);
        const sw = T * s + 0.6;
        const sh = T * s + 0.6;

        if (item.loaded) {
          ctx.drawImage(item.img, sx, sy, sw, sh);
        }
      }
    }
  }


  function hexToRgba(hex, alpha) {
    if (!hex) return `rgba(100, 116, 139, ${alpha})`;
    let clean = hex.replace('#', '');
    if (clean.length === 3) {
      clean = clean.split('').map(c => c + c).join('');
    }
    const num = parseInt(clean, 16);
    if (isNaN(num)) return `rgba(100, 116, 139, ${alpha})`;
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  async function loadPois() {
    try {
      const resp = await fetch('/api/map/pois', { headers: getApiHeaders() });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.ok && Array.isArray(data.pois)) {
        poisData = data.pois;
        requestRedraw();
      }
    } catch (e) {
      console.debug('Error loading map POIs:', e);
    }
  }

  function fetchVisibleBuildings() {
    if (s < 0.45) return;
    const [wx0, wy0] = toWorld(0, 0);
    const [wx1, wy1] = toWorld(w, h);
    const min_x = Math.min(wx0, wx1);
    const max_x = Math.max(wx0, wx1);
    const min_y = Math.min(wy0, wy1);
    const max_y = Math.max(wy0, wy1);

    const queryKey = `${Math.floor(min_x / 256)}_${Math.floor(min_y / 256)}_${Math.ceil(max_x / 256)}_${Math.ceil(max_y / 256)}`;
    if (lastBuildingsQuery === queryKey) return;
    lastBuildingsQuery = queryKey;

    if (buildingsFetchTimer) clearTimeout(buildingsFetchTimer);
    buildingsFetchTimer = setTimeout(async () => {
      try {
        const resp = await fetch(`/api/map/buildings?x0=${Math.round(min_x)}&y0=${Math.round(min_y)}&x1=${Math.round(max_x)}&y1=${Math.round(max_y)}`, {
          headers: getApiHeaders()
        });
        if (!resp.ok) return;
        const data = await resp.json();
        if (data.ok && data.buildings) {
          data.buildings.forEach(b => buildingsMap.set(b.id, b));
          requestRedraw();
        }
      } catch (e) {
        console.debug('Failed to fetch buildings:', e);
      }
    }, 60);
  }

  function drawPois() {
    if (!poisData || !poisData.length) return;
    ctx.save();
    for (const p of poisData) {
      if (!categoryFilters[p.category]) continue;
      const [sx, sy] = toScreen(p.x, p.y);
      if (sx < -80 || sy < -40 || sx > w + 80 || sy > h + 40) continue;

      const isHover = Boolean(hoverPoi && hoverPoi.id === p.id);
      const color = p.color || '#38ef7d';

      ctx.beginPath();
      ctx.arc(sx, sy, isHover ? 7 : 5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.lineWidth = isHover ? 2 : 1.2;
      ctx.strokeStyle = '#ffffff';
      ctx.stroke();

      if (s >= 0.08 || isHover) {
        const label = `${p.icon || ''} ${p.category_name_ru || p.category}`;
        ctx.font = 'bold 10px Inter, sans-serif';
        const tw = ctx.measureText(label).width + 10;
        ctx.fillStyle = 'rgba(10, 14, 20, 0.85)';
        ctx.fillRect(sx - tw / 2, sy - 22, tw, 18);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(sx - tw / 2, sy - 22, tw, 18);
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, sx, sy - 13);
      }
    }
    ctx.restore();
  }

  function drawBuildings() {
    if (!buildingsMap.size) return;
    const [wx0, wy0] = toWorld(0, 0);
    const [wx1, wy1] = toWorld(w, h);
    const min_x = Math.min(wx0, wx1);
    const max_x = Math.max(wx0, wx1);
    const min_y = Math.min(wy0, wy1);
    const max_y = Math.max(wy0, wy1);

    ctx.save();
    for (const b of buildingsMap.values()) {
      const cat = b.category || 'residential';
      if (!categoryFilters[cat]) continue;

      const [bx, by, bw, bh] = b.bounds;
      if (bx + bw < min_x || bx > max_x || by + bh < min_y || by > max_y) continue;

      const isHover = Boolean(hoverBuilding && hoverBuilding.id === b.id);
      const isSel = Boolean(selectedTarget && selectedTarget.building && selectedTarget.building.id === b.id);

      const color = b.color || '#64748b';
      ctx.fillStyle = isHover || isSel ? hexToRgba(color, 0.45) : hexToRgba(color, cat === 'residential' ? 0.15 : 0.3);
      ctx.strokeStyle = isHover || isSel ? '#ffffff' : hexToRgba(color, 0.7);
      ctx.lineWidth = isHover || isSel ? 2 : 1;

      for (const r of b.rects) {
        const [rwx, rwy, rw, rh] = r;
        const [sx, sy] = toScreen(rwx, rwy);
        const sw = rw * s;
        const sh = rh * s;
        ctx.fillRect(sx, sy, sw, sh);
        ctx.strokeRect(sx, sy, sw, sh);
      }

      if (isHover || isSel || (cat !== 'residential' && s >= 0.8)) {
        const [cx, cy] = b.center;
        const [scx, scy] = toScreen(cx, cy);
        const label = `${b.icon || ''} ${b.category_name || cat}`;
        ctx.font = 'bold 11px Inter, sans-serif';
        const tw = ctx.measureText(label).width + 12;
        ctx.fillStyle = 'rgba(10, 14, 20, 0.85)';
        ctx.fillRect(scx - tw / 2, scy - 10, tw, 20);
        ctx.strokeStyle = isHover || isSel ? '#ffffff' : color;
        ctx.lineWidth = 1;
        ctx.strokeRect(scx - tw / 2, scy - 10, tw, 20);
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, scx, scy);
      }
    }
    ctx.restore();
  }

  function drawTiles() {
    if (!mapInfo) return;
    ctx.imageSmoothingEnabled = s < 1;
    const ideal = selectZoomLevel();
    for (let L = Math.min(4, ideal + 1); L >= ideal; L--) {
      drawLevel(L);
    }
  }

  function drawTowns() {
    if (!filters.towns || !mapInfo || !mapInfo.towns) return;
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const fontSize = Math.max(12, Math.min(22, Math.round(11 + s * 30)));
    ctx.font = `bold ${fontSize}px Inter, sans-serif`;

    mapInfo.towns.forEach(t => {
      const [sx, sy] = toScreen(t.x, t.y);
      if (sx < -150 || sy < -40 || sx > w + 150 || sy > h + 40) return;

      // Glow marker
      ctx.beginPath();
      ctx.arc(sx, sy - 8, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffd54f';
      ctx.fill();
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Text with tactical dark outline
      ctx.lineWidth = 4;
      ctx.strokeStyle = 'rgba(10, 14, 20, 0.9)';
      ctx.strokeText(t.name, sx, sy + 10);
      ctx.fillStyle = '#fff6d6';
      ctx.fillText(t.name, sx, sy + 10);
    });
    ctx.restore();
  }

  function drawPlayers() {
    if (!playersData || !playersData.length) return;

    hoverPlayer = null;
    const now = Date.now();

    playersData.forEach(p => {
      if (p.dead && !filters.dead) return;
      if (!p.dead && p.online && !filters.online) return;
      if (!p.dead && !p.online && !filters.offline) return;

      const [sx, sy] = toScreen(p.x, p.y);
      if (sx < -40 || sy < -40 || sx > w + 40 || sy > h + 40) return;

      const isOnline = p.online;
      const isDead = p.dead;

      // Pulsing effect for online players
      if (isOnline && !isDead) {
        const pulse = (Math.sin(now / 250) + 1) / 2;
        ctx.beginPath();
        ctx.arc(sx, sy, 8 + pulse * 6, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(16, 185, 129, ${0.35 - pulse * 0.25})`;
        ctx.fill();
      }

      // Marker Dot
      ctx.beginPath();
      ctx.arc(sx, sy, isOnline ? 7 : 5, 0, Math.PI * 2);
      ctx.fillStyle = isDead ? '#ef4444' : (isOnline ? '#10b981' : '#3b82f6');
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#ffffff';
      ctx.stroke();

      // Check hover
      const dist = Math.hypot(lastMouseX - sx, lastMouseY - sy);
      if (dist < 14) {
        hoverPlayer = p;
      }

      // Name Label
      const label = p.character ? `${p.username} (${p.character})` : p.username;
      ctx.font = 'bold 12px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';

      ctx.lineWidth = 3;
      ctx.strokeStyle = 'rgba(10, 14, 20, 0.95)';
      ctx.strokeText(label, sx + 12, sy);
      ctx.fillStyle = isDead ? '#fca5a5' : (isOnline ? '#a7f3d0' : '#bfdbfe');
      ctx.fillText(label, sx + 12, sy);
    });
  }

  function drawSelectedTarget() {
    if (!selectedTarget) return;
    const [sx, sy] = toScreen(selectedTarget.x, selectedTarget.y);
    if (sx < -50 || sy < -50 || sx > w + 50 || sy > h + 50) return;

    targetPulse = (targetPulse + 0.05) % (Math.PI * 2);
    const r = 16 + Math.sin(targetPulse) * 3;

    ctx.save();
    ctx.strokeStyle = '#38ef7d';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(sx, sy, r, 0, Math.PI * 2);
    ctx.stroke();

    // Crosshair lines
    ctx.beginPath();
    ctx.moveTo(sx - r - 6, sy);
    ctx.lineTo(sx - 4, sy);
    ctx.moveTo(sx + 4, sy);
    ctx.lineTo(sx + r + 6, sy);
    ctx.moveTo(sx, sy - r - 6);
    ctx.lineTo(sx, sy - 4);
    ctx.moveTo(sx, sy + 4);
    ctx.lineTo(sx, sy + r + 6);
    ctx.stroke();

    // Target label badge
    ctx.fillStyle = 'rgba(16, 22, 34, 0.85)';
    ctx.strokeStyle = '#38ef7d';
    ctx.lineWidth = 1;
    const text = `X: ${Math.round(selectedTarget.x)}, Y: ${Math.round(selectedTarget.y)}`;
    const tw = ctx.measureText(text).width + 16;
    ctx.fillRect(sx - tw / 2, sy + r + 8, tw, 22);
    ctx.strokeRect(sx - tw / 2, sy + r + 8, tw, 22);

    ctx.fillStyle = '#38ef7d';
    ctx.font = 'bold 11px Inter, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, sx, sy + r + 19);
    ctx.restore();
  }

  function draw() {
    animId = null;
    if (!ctx || !w || !h) return;

    // Background fill
    ctx.fillStyle = '#0a0d14';
    ctx.fillRect(0, 0, w, h);

    drawTiles();
    drawGrid();
    if (s >= 0.45) {
      drawBuildings();
      fetchVisibleBuildings();
    } else {
      drawPois();
    }
    drawTowns();
    drawPlayers();
    drawSelectedTarget();

    // Re-trigger animation if online players or target crosshair is active
    if (filters.online || selectedTarget) {
      if (!animId) animId = requestAnimationFrame(draw);
    }
  }

  function findNearestTown(wx, wy) {
    if (!mapInfo || !mapInfo.towns || !mapInfo.towns.length) return null;
    let nearest = null;
    let minDist = Infinity;
    mapInfo.towns.forEach(t => {
      const d = Math.hypot(t.x - wx, t.y - wy);
      if (d < minDist) {
        minDist = d;
        nearest = { town: t, dist: Math.round(d) };
      }
    });
    return nearest;
  }

  function updateHud(wx, wy) {
    const coordsEl = document.getElementById('map-hud-coords');
    const townEl = document.getElementById('map-hud-town');
    const zoomEl = document.getElementById('map-hud-zoom');

    if (coordsEl) {
      coordsEl.textContent = `X: ${Math.round(wx)}, Y: ${Math.round(wy)}`;
    }
    if (townEl) {
      const near = findNearestTown(wx, wy);
      if (near) {
        townEl.textContent = `${near.town.name} (${near.dist}м)`;
      } else {
        townEl.textContent = 'Округ Нокс';
      }
    }
    if (zoomEl) {
      zoomEl.textContent = `${Math.round(s * 1000)}%`;
    }
  }

  function flyTo(wx, wy, targetScale = null) {
    const startX = cx;
    const startY = cy;
    const startS = s;
    const destS = targetScale !== null ? targetScale : Math.max(s, 0.15);
    const startTime = performance.now();
    const duration = 500;

    function step(now) {
      const elapsed = now - startTime;
      const t = Math.min(1, elapsed / duration);
      // Ease out cubic
      const ease = 1 - Math.pow(1 - t, 3);

      cx = startX + (wx - startX) * ease;
      cy = startY + (wy - startY) * ease;
      s = startS + (destS - startS) * ease;

      requestRedraw();
      updateHud(cx, cy);

      if (t < 1) {
        requestAnimationFrame(step);
      }
    }
    requestAnimationFrame(step);
  }

  function showTargetCard(x, y, target = null) {
    const player = (target && target.player) ? target.player : (target && target.username ? target : null);
    const building = (target && target.building) ? target.building : null;
    const poi = (target && target.poi) ? target.poi : null;

    selectedTarget = { x, y, player, building, poi };
    const cardEl = document.getElementById('map-target-card');
    if (!cardEl) return;

    const near = findNearestTown(x, y);
    const townStr = near ? `${near.town.name} (${near.dist}м)` : 'Округ Нокс';

    let cardTitle = '🎯 Выбранная точка';
    if (building) {
      cardTitle = `${building.icon || '🏢'} ${building.category_name || building.category}`;
    } else if (poi) {
      cardTitle = `${poi.icon || '📍'} ${poi.label || poi.category_name_ru}`;
    } else if (player) {
      cardTitle = `👤 ${player.character ? `${player.username} (${player.character})` : player.username}`;
    }

    let html = `
      <div class="map-card-header">
        <span class="map-card-title">${cardTitle}</span>
        <button class="map-card-close" onclick="window.pzMap.closeTargetCard()">✕</button>
      </div>
      <div class="map-card-body">
        <div class="map-card-row">
          <span class="map-card-lbl">Координаты:</span>
          <span class="map-card-val mono">X: ${Math.round(x)}, Y: ${Math.round(y)}</span>
        </div>
        <div class="map-card-row">
          <span class="map-card-lbl">Ближайший город:</span>
          <span class="map-card-val">${townStr}</span>
        </div>
    `;

    if (building) {
      html += `
        <div class="map-card-row" style="margin-top: 6px; border-top: 1px solid var(--border); padding-top: 6px;">
          <span class="map-card-lbl">Категория:</span>
          <span class="badge" style="background: ${hexToRgba(building.color, 0.25)}; color: ${building.color}; border: 1px solid ${building.color};">${building.category_name || building.category}</span>
        </div>
        <div class="map-card-row">
          <span class="map-card-lbl">Этажи:</span>
          <span class="map-card-val small">${building.floors ? building.floors.join(', ') : '0'}</span>
        </div>
      `;
      if (building.rooms_by_floor && Object.keys(building.rooms_by_floor).length > 0) {
        html += `<div style="margin-top: 6px; font-size: 11px; color: var(--text-muted); font-weight: bold;">Помещения:</div>`;
        for (const [fl, rlist] of Object.entries(building.rooms_by_floor)) {
          html += `
            <div class="map-card-row" style="font-size: 11px;">
              <span class="map-card-lbl">Этаж ${fl}:</span>
              <span class="map-card-val small" style="max-width: 200px;">${rlist.slice(0, 4).join(', ')}</span>
            </div>
          `;
        }
      }
    } else if (poi) {
      html += `
        <div class="map-card-row" style="margin-top: 6px; border-top: 1px solid var(--border); padding-top: 6px;">
          <span class="map-card-lbl">Категория:</span>
          <span class="badge" style="background: ${hexToRgba(poi.color, 0.25)}; color: ${poi.color}; border: 1px solid ${poi.color};">${poi.category_name_ru}</span>
        </div>
        <div class="map-card-row">
          <span class="map-card-lbl">Район:</span>
          <span class="map-card-val small">${poi.town}</span>
        </div>
      `;
    } else if (player) {
      const statColor = player.dead ? 'var(--danger)' : (player.online ? 'var(--primary)' : 'var(--info)');
      const statText = player.dead ? 'Погиб' : (player.online ? 'В игре (Online)' : 'Оффлайн');
      html += `
        <div class="map-card-row" style="margin-top: 6px; border-top: 1px solid var(--border); padding-top: 6px;">
          <span class="map-card-lbl">Игрок:</span>
          <span class="map-card-val" style="color: ${statColor}; font-weight: bold;">${player.username}</span>
        </div>
        ${player.character ? `
        <div class="map-card-row">
          <span class="map-card-lbl">Персонаж:</span>
          <span class="map-card-val">${player.character}</span>
        </div>` : ''}
        ${player.steamid ? `
        <div class="map-card-row">
          <span class="map-card-lbl">Steam ID:</span>
          <span class="map-card-val mono small">${player.steamid}</span>
        </div>` : ''}
      `;
    }

    // Teleport dropdown and button
    const onlinePlayers = playersData.filter(p => p.online);
    if (onlinePlayers.length > 0) {
      html += `
        <div class="map-teleport-box">
          <label style="font-size: 11px; color: var(--text-muted); font-weight: 600;">Телепортировать игрока сюда:</label>
          <div style="display: flex; gap: 6px; margin-top: 4px;">
            <select id="map-teleport-user" class="form-control form-control-sm" style="flex: 1;">
              ${onlinePlayers.map(p => `<option value="${p.username}" ${player && player.username === p.username ? 'selected' : ''}>${p.username}</option>`).join('')}
            </select>
            <button class="btn btn-sm btn-primary" onclick="window.pzMap.teleportSelected()">⚡ ТП</button>
          </div>
        </div>
      `;
    } else {
      html += `
        <div class="muted small" style="margin-top: 8px; font-style: italic;">
          Нет активных игроков онлайн для мгновенной телепортации.
        </div>
      `;
    }

    html += `
      <div style="display: flex; gap: 6px; margin-top: 10px;">
        <button class="btn btn-sm btn-secondary" style="flex: 1;" onclick="window.pzMap.copyCoords(${Math.round(x)}, ${Math.round(y)})">📋 Скопировать</button>
        <button class="btn btn-sm btn-secondary" style="flex: 1;" onclick="window.pzMap.focusHere(${Math.round(x)}, ${Math.round(y)})">🔍 Приблизить</button>
      </div>
    </div>`;

    cardEl.innerHTML = html;
    cardEl.classList.remove('hidden');
    requestRedraw();
  }

  function closeTargetCard() {
    selectedTarget = null;
    const cardEl = document.getElementById('map-target-card');
    if (cardEl) cardEl.classList.add('hidden');
    requestRedraw();
  }

  async function teleportSelected() {
    const selEl = document.getElementById('map-teleport-user');
    if (!selEl || !selectedTarget) return;
    const uname = selEl.value;
    if (!uname) return;

    try {
      const resp = await fetch('/api/map/teleport', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getApiHeaders() },
        body: JSON.stringify({
          username: uname,
          x: Math.round(selectedTarget.x),
          y: Math.round(selectedTarget.y),
          z: 0
        })
      });
      const data = await resp.json();
      if (data.ok) {
        showToast(data.message || 'Команда телепортации отправлена', 'success');
        refreshPlayers();
      } else {
        showToast(data.error || 'Ошибка при телепортации', 'error');
      }
    } catch (e) {
      showToast('Сетевая ошибка при отправке команды', 'error');
    }
  }

  function copyCoords(x, y) {
    const text = `${x}, ${y}`;
    navigator.clipboard.writeText(text).then(() => {
      showToast(`Координаты скопированы: ${text}`, 'info');
    });
  }

  function focusHere(x, y) {
    flyTo(x, y, 0.45);
  }

  async function triggerServerSave() {
    try {
      showToast('Отправка команды сохранения мира (save)...', 'info');
      const resp = await fetch('/api/map/save', {
        method: 'POST',
        headers: getApiHeaders()
      });
      const data = await resp.json();
      if (data.ok) {
        showToast(data.message || 'Сервер сохраняет мир...', 'success');
        setTimeout(refreshPlayers, 2000);
      }
    } catch (e) {
      showToast('Ошибка сохранения мира', 'error');
    }
  }

  async function refreshPlayers() {
    try {
      const resp = await fetch('/api/map/players', { headers: getApiHeaders() });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.ok && Array.isArray(data.players)) {
        playersData = data.players;
        renderPlayersList();
        requestRedraw();
      }
    } catch (e) {
      console.debug('Error fetching players positions:', e);
    }
  }

  function renderPlayersList() {
    const listEl = document.getElementById('map-players-sidebar-list');
    if (!listEl) return;

    if (!playersData.length) {
      listEl.innerHTML = `<div class="muted small text-center" style="padding: 12px;">Пока нет сохраненных игроков в базе данных.</div>`;
      return;
    }

    listEl.innerHTML = playersData.map(p => {
      const badgeCls = p.dead ? 'badge-danger' : (p.online ? 'badge-success' : 'badge-info');
      const statLabel = p.dead ? 'Погиб' : (p.online ? 'Online' : 'Оффлайн');
      return `
        <div class="map-player-item" onclick="window.pzMap.flyToPlayer('${p.username}')">
          <div class="map-player-main">
            <span class="map-player-dot ${p.dead ? 'dead' : (p.online ? 'online' : 'offline')}"></span>
            <div class="map-player-info">
              <span class="map-player-name">${p.username}</span>
              ${p.character && p.character !== p.username ? `<span class="map-player-char">${p.character}</span>` : ''}
            </div>
          </div>
          <div class="map-player-meta">
            <span class="badge ${badgeCls}">${statLabel}</span>
            <span class="mono small muted">${Math.round(p.x)}, ${Math.round(p.y)}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  function flyToPlayer(username) {
    const p = playersData.find(x => x.username.toLowerCase() === username.toLowerCase());
    if (p) {
      flyTo(p.x, p.y, 0.4);
      showTargetCard(p.x, p.y, p);
    }
  }

  function setupEventHandlers() {
    if (!canvas) return;

    // Mouse Drag & Pan
    canvas.addEventListener('mousedown', e => {
      if (e.button === 0 || e.button === 1) { // Left or middle click
        isDragging = true;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      }
    });

    window.addEventListener('mousemove', e => {
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;
      lastMouseX = sx;
      lastMouseY = sy;

      if (sx >= 0 && sy >= 0 && sx <= w && sy <= h) {
        const [wx, wy] = toWorld(sx, sy);
        updateHud(wx, wy);

        // Building / POI hit test
        const oldB = hoverBuilding;
        const oldP = hoverPoi;
        hoverBuilding = null;
        hoverPoi = null;

        if (s >= 0.45) {
          for (const b of buildingsMap.values()) {
            if (!categoryFilters[b.category]) continue;
            const [bx, by, bw, bh] = b.bounds;
            if (wx >= bx && wx <= bx + bw && wy >= by && wy <= by + bh) {
              for (const r of b.rects) {
                if (wx >= r[0] && wx <= r[0] + r[2] && wy >= r[1] && wy <= r[1] + r[3]) {
                  hoverBuilding = b;
                  break;
                }
              }
              if (hoverBuilding) break;
            }
          }
        } else {
          for (const p of poisData) {
            if (!categoryFilters[p.category]) continue;
            const [psx, psy] = toScreen(p.x, p.y);
            if (Math.hypot(sx - psx, sy - psy) <= 12) {
              hoverPoi = p;
              break;
            }
          }
        }

        if (hoverBuilding !== oldB || hoverPoi !== oldP) {
          canvas.style.cursor = (hoverBuilding || hoverPoi || hoverPlayer) ? 'pointer' : (isDragging ? 'grabbing' : 'default');
          requestRedraw();
        }
      }

      if (isDragging) {
        cx -= (e.movementX || 0) / s;
        cy -= (e.movementY || 0) / s;
        requestRedraw();
      }
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });

    // Click to select
    canvas.addEventListener('click', e => {
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;
      const [wx, wy] = toWorld(sx, sy);

      // Check if clicked near an existing player
      let clickedPlayer = null;
      for (const p of playersData) {
        const [psx, psy] = toScreen(p.x, p.y);
        if (Math.hypot(sx - psx, sy - psy) < 16) {
          clickedPlayer = p;
          break;
        }
      }

      if (clickedPlayer) {
        showTargetCard(clickedPlayer.x, clickedPlayer.y, { player: clickedPlayer });
      } else if (hoverBuilding) {
        showTargetCard(hoverBuilding.center[0], hoverBuilding.center[1], { building: hoverBuilding });
      } else if (hoverPoi) {
        showTargetCard(hoverPoi.x, hoverPoi.y, { poi: hoverPoi });
      } else {
        showTargetCard(wx, wy, null);
      }
    });

    // Wheel to Zoom
    canvas.addEventListener('wheel', e => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;
      const [wx, wy] = toWorld(sx, sy);

      const factor = e.deltaY < 0 ? 1.25 : 0.8;
      const newS = Math.max(0.012, Math.min(2.5, s * factor));

      // Keep world coordinate under cursor stable
      cx = wx - (sx - w / 2) / newS;
      cy = wy - (sy - h / 2) / newS;
      s = newS;

      requestRedraw();
      updateHud(wx, wy);
    }, { passive: false });

    // Touch Support for Mobile / Tablets
    let initialTouchDist = 0;
    let initialTouchScale = s;

    canvas.addEventListener('touchstart', e => {
      if (e.touches.length === 1) {
        isDragging = true;
        const rect = canvas.getBoundingClientRect();
        lastMouseX = e.touches[0].clientX - rect.left;
        lastMouseY = e.touches[0].clientY - rect.top;
      } else if (e.touches.length === 2) {
        isDragging = false;
        initialTouchDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        initialTouchScale = s;
      }
    }, { passive: true });

    canvas.addEventListener('touchmove', e => {
      const rect = canvas.getBoundingClientRect();
      if (e.touches.length === 1 && isDragging) {
        const sx = e.touches[0].clientX - rect.left;
        const sy = e.touches[0].clientY - rect.top;
        const dx = sx - lastMouseX;
        const dy = sy - lastMouseY;
        cx -= dx / s;
        cy -= dy / s;
        lastMouseX = sx;
        lastMouseY = sy;
        requestRedraw();
      } else if (e.touches.length === 2 && initialTouchDist > 0) {
        const dist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const factor = dist / initialTouchDist;
        s = Math.max(0.012, Math.min(2.5, initialTouchScale * factor));
        requestRedraw();
      }
    }, { passive: true });

    canvas.addEventListener('touchend', () => {
      isDragging = false;
      initialTouchDist = 0;
    });

    window.addEventListener('resize', resizeCanvas);
  }

  async function initPzMap() {
    canvas = document.getElementById('pzMapCanvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');

    resizeCanvas();
    setupEventHandlers();

    // Fetch map info
    try {
      const resp = await fetch('/api/map/info', { headers: getApiHeaders() });
      if (resp.ok) {
        mapInfo = await resp.json();
        renderTownsDropdown();
        if (mapInfo.hasTiles) {
          const banner = document.getElementById('map-no-tiles-banner');
          if (banner) banner.style.display = 'none';
        }
      }
    } catch (e) {
      console.warn('Map info fetch failed:', e);
    }

    loadPois();
    refreshPlayers();

    if (!pollTimer) {
      pollTimer = setInterval(refreshPlayers, 5000);
    }

    requestRedraw();
  }

  function renderTownsDropdown() {
    const sel = document.getElementById('map-towns-select');
    if (!sel || !mapInfo || !mapInfo.towns) return;
    sel.innerHTML = '<option value="">📍 Выберите город / сектор...</option>' +
      mapInfo.towns.map(t => `<option value="${t.x},${t.y}">${t.name}</option>`).join('');
  }

  function onTownSelected(val) {
    if (!val) return;
    const [tx, ty] = val.split(',').map(Number);
    flyTo(tx, ty, 0.25);
  }

  function toggleFilter(key) {
    if (filters.hasOwnProperty(key)) {
      filters[key] = !filters[key];
      requestRedraw();
    }
  }

  function searchMap(query) {
    query = (query || '').trim().toLowerCase();
    if (!query) return;

    // 1. Search player
    const p = playersData.find(x => x.username.toLowerCase().includes(query) || (x.character && x.character.toLowerCase().includes(query)));
    if (p) {
      flyTo(p.x, p.y, 0.4);
      showTargetCard(p.x, p.y, p);
      return;
    }

    // 2. Search town
    if (mapInfo && mapInfo.towns) {
      const t = mapInfo.towns.find(x => x.name.toLowerCase().includes(query));
      if (t) {
        flyTo(t.x, t.y, 0.25);
        showTargetCard(t.x, t.y, null);
        return;
      }
    }

    showToast(`Ничего не найдено по запросу "${query}"`, 'info');
  }


  // Close category dropdown on click outside
  document.addEventListener('click', (e) => {
    const menu = document.getElementById('map-categories-menu');
    const btn = document.getElementById('btn-map-layers');
    if (menu && !menu.classList.contains('hidden')) {
      if (!menu.contains(e.target) && (!btn || !btn.contains(e.target))) {
        menu.classList.add('hidden');
      }
    }
  });

  // Global namespace for onclick bindings
  window.pzMap = {
    init: initPzMap,
    toggleCategoryDropdown: (e) => {
      if (e) e.stopPropagation();
      const menu = document.getElementById('map-categories-menu');
      if (menu) menu.classList.toggle('hidden');
    },
    setCategory: (catId, enabled) => {
      categoryFilters[catId] = !!enabled;
      requestRedraw();
    },
    setAllCategories: (enabled) => {
      const container = document.getElementById('map-category-checkboxes');
      if (container) {
        const boxes = container.querySelectorAll('input[type="checkbox"]');
        boxes.forEach(cb => {
          cb.checked = enabled;
          const cat = cb.getAttribute('data-cat');
          if (cat) categoryFilters[cat] = enabled;
        });
      } else {
        Object.keys(categoryFilters).forEach(k => categoryFilters[k] = enabled);
      }
      requestRedraw();
    },
    toggleCategory: (catId, btn) => {
      categoryFilters[catId] = !categoryFilters[catId];
      if (btn) {
        btn.classList.toggle('active', categoryFilters[catId]);
      }
      requestRedraw();
    },
    flyTo,
    flyToPlayer,
    closeTargetCard,
    teleportSelected,
    copyCoords,
    focusHere,
    triggerServerSave,
    refreshPlayers,
    onTownSelected,
    toggleFilter,
    searchMap,
    resetView: () => flyTo(10500, 9500, 0.045),
    zoomIn: () => { s = Math.min(2.5, s * 1.35); requestRedraw(); },
    zoomOut: () => { s = Math.max(0.012, s * 0.75); requestRedraw(); }
  };

  // Expose initPzMap for app.js switchTab hook
  window.initPzMap = initPzMap;
})();

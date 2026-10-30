#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Performance Map Tab for Project Zomboid Server Manager.

Provides a smooth 60 FPS interactive world map viewer in PyQt5 with asynchronous
background tile loading, pyramid tile streaming, player tracking, towns navigation,
and admin teleportation.
"""

import math
import queue
import logging
import webbrowser
from collections import OrderedDict
from typing import Optional, List, Dict, Any, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QFrame, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QToolTip, QSizePolicy, QToolButton,
    QMenu, QWidgetAction, QCheckBox
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QImage,
    QCursor, QPolygonF
)

from core.translations import tr
from core.map_manager import MapManager

logger = logging.getLogger(__name__)


class TileLoaderWorker(QThread):
    """Background worker thread that loads and decodes tile images asynchronously."""

    tileLoaded = pyqtSignal(str, QImage)  # (key, image)

    def __init__(self, map_manager: MapManager, parent=None):
        super().__init__(parent)
        self.map_manager = map_manager
        self._queue = queue.Queue()
        self._pending = set()
        self._running = True

    def request_tile(self, level: int, tx: int, ty: int):
        key = f"{level}_{tx}_{ty}"
        if key not in self._pending:
            self._pending.add(key)
            self._queue.put((level, tx, ty, key))

    def run(self):
        while self._running:
            try:
                item = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            level, tx, ty, key = item
            try:
                data = self.map_manager.get_tile(level, tx, ty)
                if data:
                    img = QImage()
                    if img.loadFromData(data, "PNG"):
                        self.tileLoaded.emit(key, img)
            except Exception as e:
                logger.debug(f"Async tile load error {key}: {e}")
            finally:
                self._pending.discard(key)
                self._queue.task_done()

    def stop(self):
        self._running = False
        self.wait(500)


class PzMapCanvasWidget(QWidget):
    """Interactive canvas widget rendering PZ map tiles, towns, and players with zero UI lag."""

    coordHovered = pyqtSignal(float, float)
    targetClicked = pyqtSignal(float, float, object)

    def __init__(self, map_manager: MapManager, parent=None):
        super().__init__(parent)
        self.map_manager = map_manager
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Viewport parameters
        self.bounds = self.map_manager.bounds or [0, 0, 19968, 16128]
        self.cx = 10500.0
        self.cy = 9500.0
        self.scale = 0.045
        self.min_scale = 0.012
        self.max_scale = 2.5

        # Interactions
        self.is_dragging = False
        self.last_mouse_pos = None
        self.selected_target: Optional[Dict[str, Any]] = None
        self.players: List[Dict[str, Any]] = []

        # Filters
        self.show_online = True
        self.show_offline = True
        self.show_dead = True
        self.show_towns = True
        self.show_grid = True

        # POIs and Building Footprints
        self.pois = self.map_manager.get_pois()
        self.category_filters = {c["id"]: True for c in self.map_manager.get_categories()}
        self.hover_building: Optional[Dict[str, Any]] = None
        self.hover_poi: Optional[Dict[str, Any]] = None
        self.selected_building: Optional[Dict[str, Any]] = None

        # Tile pixmap cache in memory (LRU with OrderedDict)
        self._pixmap_cache: OrderedDict[str, QPixmap] = OrderedDict()
        self._max_cache = 1500

        # Background Tile Loader
        self._tile_loader = TileLoaderWorker(self.map_manager, self)
        self._tile_loader.tileLoaded.connect(self._on_tile_loaded)
        self._tile_loader.start()

        # Animation timer for pulsing markers (reduced to 150ms to eliminate CPU load)
        self.pulse_phase = 0.0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_anim_tick)
        self.anim_timer.start(150)

        # Preload base overview tiles (level 4)
        QTimer.singleShot(100, self._preload_overview_tiles)

    def cleanup(self):
        if hasattr(self, 'anim_timer'):
            self.anim_timer.stop()
        if hasattr(self, '_tile_loader') and self._tile_loader:
            self._tile_loader.stop()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def _preload_overview_tiles(self):
        """Preloads level 4 overview tiles so zoomed-out view is instant."""
        for tx in range(6):
            for ty in range(5):
                self._tile_loader.request_tile(4, tx, ty)

    def _on_tile_loaded(self, key: str, img: QImage):
        """Called when background worker finishes decoding a tile."""
        pm = QPixmap.fromImage(img)
        if len(self._pixmap_cache) >= self._max_cache:
            for _ in range(100):
                if self._pixmap_cache:
                    self._pixmap_cache.popitem(last=False)
        self._pixmap_cache[key] = pm
        self.update()

    def _on_anim_tick(self):
        # Only repaint for pulse animation if online players exist or a target crosshair is selected
        has_active_players = any(p.get("online") and not p.get("dead") for p in self.players)
        if (self.show_online and has_active_players) or self.selected_target:
            self.pulse_phase = (self.pulse_phase + 0.25) % (2 * math.pi)
            self.update()

    def set_players(self, players: List[Dict[str, Any]]):
        self.players = players
        self.update()

    def to_screen(self, wx: float, wy: float) -> QPointF:
        sx = (wx - self.cx) * self.scale + self.width() / 2.0
        sy = (wy - self.cy) * self.scale + self.height() / 2.0
        return QPointF(sx, sy)

    def to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        wx = (sx - self.width() / 2.0) / self.scale + self.cx
        wy = (sy - self.height() / 2.0) / self.scale + self.cy
        return wx, wy

    def select_zoom_level(self) -> int:
        if self.scale >= 0.7:
            return 0
        if self.scale >= 0.3:
            return 1
        if self.scale >= 0.12:
            return 2
        if self.scale >= 0.05:
            return 3
        return 4

    def get_tile_pixmap(self, level: int, tx: int, ty: int) -> Optional[QPixmap]:
        """Gets tile from cache; if missing, requests async background load and returns parent tile if possible."""
        key = f"{level}_{tx}_{ty}"
        if key in self._pixmap_cache:
            self._pixmap_cache.move_to_end(key)
            return self._pixmap_cache[key]

        # Request background loading
        self._tile_loader.request_tile(level, tx, ty)

        # Fallback: check parent zoom level tile for instant seamless rendering
        if level < 4:
            parent_level = level + 1
            ptx = tx // 2
            pty = ty // 2
            parent_key = f"{parent_level}_{ptx}_{pty}"
            if parent_key in self._pixmap_cache:
                # Return parent tile to avoid black gaps
                return None  # handled in _draw_tiles fallback
        return None

    def fly_to(self, wx: float, wy: float, target_scale: Optional[float] = None):
        self.cx = wx
        self.cy = wy
        if target_scale:
            self.scale = max(self.min_scale, min(self.max_scale, target_scale))
        self.update()
        self.coordHovered.emit(self.cx, self.cy)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, self.scale < 1.0)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor("#090d14"))

        # 1. Tiles
        self._draw_tiles(painter)

        # 2. Grid & bounds
        if self.show_grid:
            self._draw_grid(painter)

        # 3. Buildings Footprints or POI Landmarks
        if self.scale >= 0.45:
            self._draw_buildings(painter)
        else:
            self._draw_pois(painter)

        # 4. Towns
        if self.show_towns:
            self._draw_towns(painter)

        # 4. Players
        self._draw_players(painter)

        # 5. Selected Target Crosshair
        if self.selected_target:
            self._draw_selected_target(painter)

        painter.end()

    def _draw_tiles(self, painter: QPainter):
        level = self.select_zoom_level()
        T = 256 * (2 ** level)
        x0, y0, x1, y1 = self.bounds

        wx0, wy0 = self.to_world(0, 0)
        wx1, wy1 = self.to_world(self.width(), self.height())

        tx0 = max(0, int(math.floor((min(wx0, wx1) - x0) / T)))
        ty0 = max(0, int(math.floor((min(wy0, wy1) - y0) / T)))
        tx1 = min(int(math.ceil((x1 - x0) / T)) - 1, int(math.floor((max(wx0, wx1) - x0) / T)))
        ty1 = min(int(math.ceil((y1 - y0) / T)) - 1, int(math.floor((max(wy0, wy1) - y0) / T)))

        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                pm = self.get_tile_pixmap(level, tx, ty)
                sp = self.to_screen(x0 + tx * T, y0 + ty * T)
                sw = T * self.scale + 0.6
                sh = T * self.scale + 0.6
                rect = QRectF(sp.x(), sp.y(), sw, sh)

                if pm:
                    painter.drawPixmap(rect.toRect(), pm)
                else:
                    # Seamless fallback: check parent level (level + 1)
                    parent_drawn = False
                    if level < 4:
                        p_level = level + 1
                        ptx, pty = tx // 2, ty // 2
                        p_pm = self._pixmap_cache.get(f"{p_level}_{ptx}_{pty}")
                        if p_pm:
                            # Draw quadrant of parent tile
                            sub_x = 128 if (tx % 2 == 1) else 0
                            sub_y = 128 if (ty % 2 == 1) else 0
                            sub_rect = QRectF(sub_x, sub_y, 128, 128)
                            painter.drawPixmap(rect.toRect(), p_pm, sub_rect.toRect())
                            parent_drawn = True

                    if not parent_drawn:
                        painter.fillRect(rect, QColor("#0e1520"))
                        painter.setPen(QPen(QColor("#182335"), 0.5))
                        painter.drawRect(rect)

    def _draw_grid(self, painter: QPainter):
        x0, y0, x1, y1 = self.bounds
        p0 = self.to_screen(x0, y0)
        p1 = self.to_screen(x1, y1)

        # Boundary border
        pen = QPen(QColor("#34d399"), 1.5, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(QRectF(p0.x(), p0.y(), (x1 - x0) * self.scale, (y1 - y0) * self.scale))

        # Coordinate lines
        step = 2000 if self.scale < 0.08 else (1000 if self.scale < 0.25 else 500)
        painter.setPen(QPen(QColor(255, 255, 255, 18), 1, Qt.SolidLine))
        painter.setFont(QFont("JetBrains Mono", 8))

        startX = int(math.floor(x0 / step) * step)
        startY = int(math.floor(y0 / step) * step)

        for gx in range(startX, x1 + 1, step):
            sp = self.to_screen(gx, y0)
            if -20 <= sp.x() <= self.width() + 20:
                painter.drawLine(int(sp.x()), max(0, int(p0.y())), int(sp.x()), min(self.height(), int(p1.y())))
                painter.setPen(QPen(QColor(255, 255, 255, 80)))
                painter.drawText(int(sp.x()) + 4, max(14, int(p0.y()) + 14), f"{gx}")
                painter.setPen(QPen(QColor(255, 255, 255, 18), 1, Qt.SolidLine))

        for gy in range(startY, y1 + 1, step):
            sp = self.to_screen(x0, gy)
            if -20 <= sp.y() <= self.height() + 20:
                painter.drawLine(max(0, int(p0.x())), int(sp.y()), min(self.width(), int(p1.x())), int(sp.y()))
                painter.setPen(QPen(QColor(255, 255, 255, 80)))
                painter.drawText(max(4, int(p0.x()) + 4), int(sp.y()) - 4, f"{gy}")
                painter.setPen(QPen(QColor(255, 255, 255, 18), 1, Qt.SolidLine))

    def _draw_towns(self, painter: QPainter):
        fsize = max(9, min(16, int(10 + self.scale * 20)))
        font = QFont("Segoe UI", fsize, QFont.Bold)
        painter.setFont(font)

        for town in self.map_manager.towns:
            sp = self.to_screen(town["x"], town["y"])
            if -100 <= sp.x() <= self.width() + 100 and -40 <= sp.y() <= self.height() + 40:
                # Dot
                painter.setBrush(QBrush(QColor("#ffd54f")))
                painter.setPen(QPen(QColor("#000000"), 1.5))
                painter.drawEllipse(sp, 4, 4)

                # Text with dark background rect for legibility
                name = town["name"]
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(name)
                th = fm.height()

                rect = QRectF(sp.x() - tw / 2.0 - 4, sp.y() + 6, tw + 8, th)
                painter.fillRect(rect, QColor(10, 14, 20, 200))
                painter.setPen(QPen(QColor("#fff6d6")))
                painter.drawText(rect, Qt.AlignCenter, name)

    def _draw_players(self, painter: QPainter):
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)

        for p in self.players:
            is_dead = p.get("dead", False)
            is_online = p.get("online", False)

            if is_dead and not self.show_dead:
                continue
            if not is_dead and is_online and not self.show_online:
                continue
            if not is_dead and not is_online and not self.show_offline:
                continue

            sp = self.to_screen(p["x"], p["y"])
            if -50 <= sp.x() <= self.width() + 50 and -50 <= sp.y() <= self.height() + 50:
                # Online pulse
                if is_online and not is_dead:
                    pulse_r = 7.0 + math.sin(self.pulse_phase) * 3.5
                    alpha = int(70 + math.sin(self.pulse_phase) * 50)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(16, 185, 129, alpha)))
                    painter.drawEllipse(sp, pulse_r, pulse_r)

                # Main dot
                color = QColor("#ef4444") if is_dead else (QColor("#10b981") if is_online else QColor("#3b82f6"))
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor("#ffffff"), 1.8))
                r = 6 if is_online else 5
                painter.drawEllipse(sp, r, r)

                # Label
                uname = p.get("username", "Unknown")
                char = p.get("character")
                label = f"{uname} ({char})" if char and char != uname else uname

                painter.setPen(QPen(QColor("#000000"), 3))
                painter.drawText(int(sp.x()) + 10, int(sp.y()) + 4, label)
                painter.setPen(QPen(QColor("#ffffff"), 1))
                painter.drawText(int(sp.x()) + 10, int(sp.y()) + 4, label)

    def _draw_selected_target(self, painter: QPainter):
        sp = self.to_screen(self.selected_target["x"], self.selected_target["y"])
        if -50 <= sp.x() <= self.width() + 50 and -50 <= sp.y() <= self.height() + 50:
            painter.setPen(QPen(QColor("#38ef7d"), 2))
            painter.setBrush(Qt.NoBrush)
            r = 14 + math.sin(self.pulse_phase) * 2
            painter.drawEllipse(sp, r, r)

            # Crosshairs
            painter.drawLine(int(sp.x() - r - 6), int(sp.y()), int(sp.x() - 4), int(sp.y()))
            painter.drawLine(int(sp.x() + 4), int(sp.y()), int(sp.x() + r + 6), int(sp.y()))
            painter.drawLine(int(sp.x()), int(sp.y() - r - 6), int(sp.x()), int(sp.y() - 4))
            painter.drawLine(int(sp.x()), int(sp.y() + 4), int(sp.x()), int(sp.y() + r + 6))

            # Label box
            text = f"X: {int(self.selected_target['x'])}, Y: {int(self.selected_target['y'])}"
            painter.setFont(QFont("JetBrains Mono", 9, QFont.Bold))
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text)
            rect = QRectF(sp.x() - tw / 2.0 - 6, sp.y() + r + 6, tw + 12, 20)
            painter.fillRect(rect, QColor(16, 22, 34, 210))
            painter.setPen(QPen(QColor("#38ef7d"), 1))
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignCenter, text)

    def toggle_category(self, cat_id: str, enabled: bool):
        self.category_filters[cat_id] = enabled
        self.update()

    def _draw_pois(self, painter: QPainter):
        """Draws landmark POIs (police, guns, medical, gas, fire, food) when zoomed out."""
        if not self.pois:
            return

        font_sm = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_sm)

        for poi in self.pois:
            cat = poi.get("category", "")
            if not self.category_filters.get(cat, True):
                continue

            sp = self.to_screen(poi["x"], poi["y"])
            if sp.x() < -80 or sp.y() < -30 or sp.x() > self.width() + 80 or sp.y() > self.height() + 30:
                continue

            color = QColor(poi.get("color", "#38ef7d"))
            is_hover = bool(self.hover_poi and self.hover_poi.get("id") == poi.get("id"))

            r = 7 if is_hover else 5
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#ffffff") if is_hover else QColor(10, 14, 20, 200), 1.5))
            painter.drawEllipse(sp, r, r)

            if self.scale >= 0.08 or is_hover:
                label = f"{poi.get('icon', '')} {poi.get('category_name_ru', cat)}"
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(label)
                th = fm.height()
                rect = QRectF(sp.x() - tw / 2.0 - 4, sp.y() - th - 8, tw + 8, th + 2)
                painter.fillRect(rect, QColor(10, 14, 20, 210))
                painter.setPen(QPen(color, 1))
                painter.drawRect(rect)
                painter.setPen(QPen(QColor("#ffffff")))
                painter.drawText(rect, Qt.AlignCenter, label)

    def _draw_buildings(self, painter: QPainter):
        """Draws building footprints with category coloring and room counts when zoomed in."""
        p0 = self.to_world(0, 0)
        p1 = self.to_world(self.width(), self.height())
        min_x, max_x = min(p0[0], p1[0]), max(p0[0], p1[0])
        min_y, max_y = min(p0[1], p1[1]), max(p0[1], p1[1])

        buildings = self.map_manager.get_buildings_in_bounds(min_x, min_y, max_x, max_y)
        font_bld = QFont("Segoe UI", 8, QFont.Bold)

        for b in buildings:
            cat = b.get("category", "residential")
            if not self.category_filters.get(cat, True):
                continue

            color = QColor(b.get("color", "#64748b"))
            is_hover = bool(self.hover_building and self.hover_building.get("id") == b.get("id"))
            is_sel = bool(self.selected_target and self.selected_target.get("building") and self.selected_target["building"].get("id") == b.get("id"))

            fill_alpha = 110 if (is_hover or is_sel) else (50 if cat != "residential" else 28)
            fill_color = QColor(color.red(), color.green(), color.blue(), fill_alpha)
            painter.setBrush(QBrush(fill_color))

            border_color = QColor("#ffffff") if (is_hover or is_sel) else QColor(color.red(), color.green(), color.blue(), 180)
            painter.setPen(QPen(border_color, 2.0 if (is_hover or is_sel) else 1.0))

            for r in b.get("rects", []):
                wx, wy, rw, rh, layer, _ = r
                sp = self.to_screen(wx, wy)
                sw = rw * self.scale
                sh = rh * self.scale
                painter.drawRect(QRectF(sp.x(), sp.y(), sw, sh))

            if is_hover or is_sel or (cat != "residential" and self.scale >= 0.8):
                cx, cy = b.get("center", [0, 0])
                sp_c = self.to_screen(cx, cy)
                label = f"{b.get('icon', '')} {b.get('category_name', cat)}"
                painter.setFont(font_bld)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(label)
                th = fm.height()
                tag_rect = QRectF(sp_c.x() - tw / 2.0 - 4, sp_c.y() - th / 2.0 - 2, tw + 8, th + 4)
                painter.fillRect(tag_rect, QColor(10, 14, 20, 230))
                painter.setPen(QPen(border_color, 1.2))
                painter.drawRect(tag_rect)
                painter.setPen(QPen(QColor("#ffffff")))
                painter.drawText(tag_rect, Qt.AlignCenter, label)

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.MidButton):
            self.is_dragging = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        wx, wy = self.to_world(event.x(), event.y())
        self.coordHovered.emit(wx, wy)

        if self.is_dragging and self.last_mouse_pos:
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()
            self.cx -= dx / self.scale
            self.cy -= dy / self.scale
            self.last_mouse_pos = event.pos()
            self.update()
            return

        # Building or POI hit test
        old_b = self.hover_building
        old_p = self.hover_poi
        self.hover_building = None
        self.hover_poi = None

        if self.scale >= 0.45:
            self.hover_building = self.map_manager.get_building_at(wx, wy)
        else:
            for p in (self.pois or []):
                if not self.category_filters.get(p.get("category"), True):
                    continue
                sp = self.to_screen(p["x"], p["y"])
                if math.hypot(event.x() - sp.x(), event.y() - sp.y()) <= 12:
                    self.hover_poi = p
                    break

        if self.hover_building != old_b or self.hover_poi != old_p:
            if self.hover_building or self.hover_poi:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.setCursor(Qt.ArrowCursor)

        if event.button() == Qt.LeftButton:
            wx, wy = self.to_world(event.x(), event.y())
            clicked_player = None
            for p in self.players:
                sp = self.to_screen(p["x"], p["y"])
                dist = math.hypot(event.x() - sp.x(), event.y() - sp.y())
                if dist < 14:
                    clicked_player = p
                    break

            clicked_building = self.hover_building
            clicked_poi = self.hover_poi

            target_x = wx
            target_y = wy
            if clicked_player:
                target_x, target_y = clicked_player["x"], clicked_player["y"]
            elif clicked_building:
                target_x, target_y = clicked_building["center"][0], clicked_building["center"][1]
            elif clicked_poi:
                target_x, target_y = clicked_poi["x"], clicked_poi["y"]

            payload = clicked_player or clicked_building or clicked_poi
            self.selected_target = {
                "x": target_x,
                "y": target_y,
                "player": clicked_player,
                "building": clicked_building,
                "poi": clicked_poi
            }
            self.targetClicked.emit(target_x, target_y, payload)
            self.update()

    def wheelEvent(self, event):
        wx, wy = self.to_world(event.x(), event.y())
        delta = event.angleDelta().y()

        # Smooth scaling step
        factor = 1.18 if delta > 0 else 0.85
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))

        # Keep coordinate under cursor pinned
        self.cx = wx - (event.x() - self.width() / 2.0) / new_scale
        self.cy = wy - (event.y() - self.height() / 2.0) / new_scale
        self.scale = new_scale

        self.update()
        self.coordHovered.emit(wx, wy)


class MapTabMixin:
    def cleanup_map_tab(self):
        if hasattr(self, 'map_refresh_timer'):
            self.map_refresh_timer.stop()
        if hasattr(self, 'pz_map_canvas'):
            self.pz_map_canvas.cleanup()

    """Mixin providing the Map tab UI to MainWindow."""

    def create_map_tab(self):
        """Creates and configures the World Map tab."""
        self.map_tab = QWidget()
        layout = QVBoxLayout(self.map_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Initialize map manager if not already done
        if not hasattr(self, 'map_manager') or self.map_manager is None:
            self.map_manager = MapManager(self.paths, self.current_server_name)

        # ── Top Toolbar Card ──────────────────────────────────────────
        toolbar_card = QFrame()
        toolbar_card.setObjectName("card")
        tb_layout = QHBoxLayout(toolbar_card)
        tb_layout.setContentsMargins(10, 6, 10, 6)
        tb_layout.setSpacing(10)

        # Map tile status pill
        has_tiles = self.map_manager.pyramid_path is not None and self.map_manager.pyramid_path.exists()
        status_text = "🗺️ Тайлы PZ активны" if has_tiles else "⚠️ Тайлы не найдены (векторная сетка)"
        status_color = "#34d399" if has_tiles else "#f59e0b"
        self.lbl_map_status = QLabel(status_text)
        self.lbl_map_status.setStyleSheet(
            f"color: {status_color}; font-weight: bold; font-size: 12px; "
            "padding: 5px 10px; background: #131922; border-radius: 5px; border: 1px solid #23354b;"
        )
        tb_layout.addWidget(self.lbl_map_status)

        # Town jump combobox
        tb_layout.addWidget(QLabel("📍 Город:"))
        self.cb_map_towns = QComboBox()
        self.cb_map_towns.setMinimumWidth(180)
        self.cb_map_towns.view().setMinimumWidth(220)
        self.cb_map_towns.addItem("Выберите сектор...")
        for t in self.map_manager.towns:
            self.cb_map_towns.addItem(f"{t['name']}", (t['x'], t['y']))
        self.cb_map_towns.currentIndexChanged.connect(self._on_map_town_jump)
        tb_layout.addWidget(self.cb_map_towns)

        # Filter buttons / checkboxes
        self.chk_online = QPushButton("🟢 Онлайн")
        self.chk_online.setCheckable(True)
        self.chk_online.setChecked(True)
        self.chk_online.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        self.chk_online.toggled.connect(lambda v: self._toggle_map_layer('online', v))
        tb_layout.addWidget(self.chk_online)

        self.chk_offline = QPushButton("🔵 Оффлайн")
        self.chk_offline.setCheckable(True)
        self.chk_offline.setChecked(True)
        self.chk_offline.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        self.chk_offline.toggled.connect(lambda v: self._toggle_map_layer('offline', v))
        tb_layout.addWidget(self.chk_offline)

        self.chk_dead = QPushButton("🔴 Погибшие")
        self.chk_dead.setCheckable(True)
        self.chk_dead.setChecked(True)
        self.chk_dead.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        self.chk_dead.toggled.connect(lambda v: self._toggle_map_layer('dead', v))
        tb_layout.addWidget(self.chk_dead)

        # Dropdown Popup for POI & Building Categories
        self.btn_map_layers = QToolButton()
        self.btn_map_layers.setText("🏢 Фильтр объектов ▾")
        self.btn_map_layers.setPopupMode(QToolButton.InstantPopup)
        self.btn_map_layers.setStyleSheet(
            "QToolButton { background: #212631; color: #f0f3f6; border: 1px solid #384255; "
            "border-radius: 5px; padding: 4px 12px; font-size: 11px; font-weight: bold; } "
            "QToolButton:hover { background: #2b3242; border-color: #4ea8de; } "
            "QToolButton::menu-indicator { image: none; }"
        )

        menu = QMenu(self.btn_map_layers)
        menu.setStyleSheet("QMenu { background: #161a23; border: 1px solid #384255; padding: 6px; border-radius: 6px; }")

        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(6)

        header_lbl = QLabel("Отображение на карте:")
        header_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #8b949e; margin-bottom: 2px;")
        panel_layout.addWidget(header_lbl)

        self.cat_checkboxes = {}
        category_defs = [
            ("police", "🛡️ Полиция", "#3b82f6"),
            ("guns", "🎯 Оружие и охота", "#f97316"),
            ("medical", "🏥 Медицина и аптеки", "#ef4444"),
            ("fuel", "⛽ АЗС и топливо", "#eab308"),
            ("food", "🛒 Супермаркеты и еда", "#22c55e"),
            ("tools", "🔨 Склады и инструменты", "#d97706"),
            ("bank", "🏦 Банки и сейфы", "#f59e0b"),
            ("residential", "🏠 Жилые дома", "#94a3b8")
        ]

        for cat_id, cat_name, col in category_defs:
            chk = QCheckBox(cat_name)
            chk.setChecked(True)
            chk.setStyleSheet(
                f"QCheckBox {{ color: {col}; font-weight: bold; font-size: 11px; padding: 2px 4px; }} "
                f"QCheckBox:hover {{ background: rgba(255, 255, 255, 0.05); border-radius: 3px; }}"
            )
            chk.toggled.connect(lambda v, c=cat_id: self.pz_map_canvas.toggle_category(c, v))
            panel_layout.addWidget(chk)
            self.cat_checkboxes[cat_id] = chk

        row_sel = QHBoxLayout()
        btn_all = QPushButton("Все")
        btn_all.setStyleSheet("padding: 2px 8px; font-size: 10px; background: #262d3d;")
        btn_all.clicked.connect(self._select_all_map_categories)
        btn_none = QPushButton("Снять все")
        btn_none.setStyleSheet("padding: 2px 8px; font-size: 10px; background: #262d3d;")
        btn_none.clicked.connect(self._deselect_all_map_categories)
        row_sel.addWidget(btn_all)
        row_sel.addWidget(btn_none)
        panel_layout.addLayout(row_sel)

        wa = QWidgetAction(menu)
        wa.setDefaultWidget(panel)
        menu.addAction(wa)
        self.btn_map_layers.setMenu(menu)
        tb_layout.addWidget(self.btn_map_layers)

        tb_layout.addStretch()

        # Action: Refresh Players
        btn_refresh = QPushButton("🔄 Обновить игроков")
        btn_refresh.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        btn_refresh.clicked.connect(self.refresh_map_players)
        tb_layout.addWidget(btn_refresh)

        # Action: Save world (save)
        btn_save = QPushButton("💾 Сохранить мир")
        btn_save.setToolTip("Отправить команду 'save' на сервер для сохранения актуальных координат игроков в базе")
        btn_save.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        btn_save.clicked.connect(self._save_world_state)
        tb_layout.addWidget(btn_save)

        # Action: Open Web Map in browser
        btn_open_web = QPushButton("🌐 Открыть веб-карту")
        btn_open_web.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669); "
            "color: #fff; font-weight: bold; padding: 5px 14px; border-radius: 5px; font-size: 12px;"
        )
        btn_open_web.clicked.connect(self._open_web_map)
        tb_layout.addWidget(btn_open_web)

        layout.addWidget(toolbar_card)

        # ── Splitter Layout: Canvas (left) + Sidebar (right) ──────────
        splitter = QSplitter(Qt.Horizontal)

        # Left Canvas Widget
        self.pz_map_canvas = PzMapCanvasWidget(self.map_manager)
        self.pz_map_canvas.coordHovered.connect(self._on_map_coord_hover)
        self.pz_map_canvas.targetClicked.connect(self._on_map_target_click)
        splitter.addWidget(self.pz_map_canvas)

        # Right Sidebar (Players & Teleport Card)
        sidebar = QFrame()
        sidebar.setObjectName("card")
        sidebar.setStyleSheet("background: #141822; border: 1px solid #23354b; border-radius: 8px;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 10, 10, 10)
        sb_layout.setSpacing(8)

        sb_title = QLabel("👥 Игроки на сервере")
        sb_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #f0f3f6;")
        sb_layout.addWidget(sb_title)

        # Players Table
        self.tbl_map_players = QTableWidget()
        self.tbl_map_players.setColumnCount(3)
        self.tbl_map_players.setHorizontalHeaderLabels(["Игрок", "Статус", "Координаты"])
        self.tbl_map_players.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_map_players.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_map_players.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_map_players.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_map_players.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_map_players.itemDoubleClicked.connect(self._on_player_table_double_click)
        sb_layout.addWidget(self.tbl_map_players, 1)

        # Teleport Control Box
        tp_box = QFrame()
        tp_box.setStyleSheet("background: #0d1117; border: 1px solid #262c36; border-radius: 6px; padding: 6px;")
        tp_box_layout = QVBoxLayout(tp_box)
        tp_box_layout.setSpacing(6)

        tp_title = QLabel("🎯 Телепортация игрока")
        tp_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #34d399;")
        tp_box_layout.addWidget(tp_title)

        self.lbl_selected_target_info = QLabel("Кликните на карту для выбора точки")
        self.lbl_selected_target_info.setStyleSheet("font-size: 11px; color: #8b949e;")
        tp_box_layout.addWidget(self.lbl_selected_target_info)

        row_tp = QHBoxLayout()
        self.cb_teleport_target_player = QComboBox()
        self.cb_teleport_target_player.setStyleSheet("min-width: 110px;")
        row_tp.addWidget(self.cb_teleport_target_player, 1)

        btn_do_teleport = QPushButton("⚡ ТП сюда")
        btn_do_teleport.setStyleSheet(
            "background: #10b981; color: #fff; font-weight: bold; padding: 4px 10px; font-size: 11px;"
        )
        btn_do_teleport.clicked.connect(self._do_teleport)
        row_tp.addWidget(btn_do_teleport)

        tp_box_layout.addLayout(row_tp)
        sb_layout.addWidget(tp_box)

        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        # ── Bottom HUD Bar ────────────────────────────────────────────
        hud_bar = QFrame()
        hud_bar.setStyleSheet("background: #0d1117; border: 1px solid #23354b; border-radius: 6px; padding: 4px 10px;")
        hud_layout = QHBoxLayout(hud_bar)
        hud_layout.setContentsMargins(6, 2, 6, 2)

        self.lbl_hud_coords = QLabel("📍 Координаты: X: 10500, Y: 9500")
        self.lbl_hud_coords.setStyleSheet("font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #34d399;")
        hud_layout.addWidget(self.lbl_hud_coords)

        hud_layout.addStretch()

        self.lbl_hud_town = QLabel("🏙️ Ближайший город: Muldraugh")
        self.lbl_hud_town.setStyleSheet("font-size: 11px; color: #8b949e;")
        hud_layout.addWidget(self.lbl_hud_town)

        layout.addWidget(hud_bar)

        # Add Tab to QTabWidget
        self.tabs.addTab(self.map_tab, tr('tab_map'))

        # Auto refresh timer for players (every 10 seconds)
        self.map_refresh_timer = QTimer(self)
        self.map_refresh_timer.timeout.connect(self.refresh_map_players)
        self.map_refresh_timer.start(10000)

        # Initial load
        QTimer.singleShot(600, self.refresh_map_players)

    def _toggle_map_layer(self, layer: str, enabled: bool):
        if layer == 'online':
            self.pz_map_canvas.show_online = enabled
        elif layer == 'offline':
            self.pz_map_canvas.show_offline = enabled
        elif layer == 'dead':
            self.pz_map_canvas.show_dead = enabled
        self.pz_map_canvas.update()

    def _select_all_map_categories(self):
        for cid, chk in self.cat_checkboxes.items():
            chk.setChecked(True)

    def _deselect_all_map_categories(self):
        for cid, chk in self.cat_checkboxes.items():
            chk.setChecked(False)

    def _on_map_town_jump(self, idx: int):
        data = self.cb_map_towns.currentData()
        if data:
            self.pz_map_canvas.fly_to(data[0], data[1], 0.25)

    def _on_map_coord_hover(self, wx: float, wy: float):
        self.lbl_hud_coords.setText(f"📍 Координаты: X: {int(wx)}, Y: {int(wy)}")
        nearest = None
        min_d = float('inf')
        for t in self.map_manager.towns:
            d = math.hypot(t['x'] - wx, t['y'] - wy)
            if d < min_d:
                min_d = d
                nearest = t
        if nearest:
            self.lbl_hud_town.setText(f"🏙️ Ближайший город: {nearest['name']} ({int(min_d)}м)")

    def _on_map_target_click(self, wx: float, wy: float, obj: Optional[Dict[str, Any]]):
        if isinstance(obj, dict) and "category" in obj:
            # Building clicked
            cat_name = obj.get("category_name", obj.get("category", "Здание"))
            icon = obj.get("icon", "🏢")
            rooms_summary = []
            for fl, rlist in sorted(obj.get("rooms_by_floor", {}).items()):
                rooms_summary.append(f"Этаж {fl}: {', '.join(rlist[:3])}")
            rooms_text = "\n".join(rooms_summary[:3]) if rooms_summary else "Жилые помещения"
            self.lbl_selected_target_info.setText(
                f"{icon} {cat_name}\n{rooms_text}\n📍 X: {int(wx)}, Y: {int(wy)}"
            )
        elif isinstance(obj, dict) and "label" in obj:
            # POI clicked
            self.lbl_selected_target_info.setText(
                f"{obj.get('icon', '')} {obj.get('label', '')}\n📍 X: {int(wx)}, Y: {int(wy)}"
            )
        elif isinstance(obj, dict) and "username" in obj:
            # Player clicked
            stat = "Погиб" if obj.get("dead") else ("Online" if obj.get("online") else "Offline")
            self.lbl_selected_target_info.setText(
                f"👤 Игрок: {obj.get('username')} [{stat}]\n📍 X: {int(wx)}, Y: {int(wy)}"
            )
        else:
            self.lbl_selected_target_info.setText(f"📍 Точка: X: {int(wx)}, Y: {int(wy)}")

    def _on_player_table_double_click(self, item: QTableWidgetItem):
        row = item.row()
        uname = self.tbl_map_players.item(row, 0).text()
        player = next((p for p in self.pz_map_canvas.players if p.get('username') == uname), None)
        if player:
            self.pz_map_canvas.fly_to(player['x'], player['y'], 0.45)
            self._on_map_target_click(player['x'], player['y'], player)

    def refresh_map_players(self):
        """Fetches active player positions from players.db."""
        if not hasattr(self, 'map_manager') or not self.map_manager:
            return

        online_names = []
        if hasattr(self, 'server_process') and self.server_process.is_running:
            if hasattr(self, 'player_manager') and self.player_manager:
                try:
                    online_names = self.player_manager.get_online_players()
                except Exception:
                    pass

        res = self.map_manager.get_players(online_names)
        players = res.get("players", [])
        self.pz_map_canvas.set_players(players)

        # Update table
        self.tbl_map_players.setRowCount(len(players))
        self.cb_teleport_target_player.clear()

        for row, p in enumerate(players):
            uname = p.get("username", "Unknown")
            is_dead = p.get("dead", False)
            is_online = p.get("online", False)

            stat_str = "Погиб" if is_dead else ("Online" if is_online else "Оффлайн")
            stat_color = QColor("#ef4444") if is_dead else (QColor("#10b981") if is_online else QColor("#79c0ff"))

            item_uname = QTableWidgetItem(uname)
            item_stat = QTableWidgetItem(stat_str)
            item_stat.setForeground(QBrush(stat_color))
            item_coords = QTableWidgetItem(f"{int(p.get('x', 0))}, {int(p.get('y', 0))}")

            self.tbl_map_players.setItem(row, 0, item_uname)
            self.tbl_map_players.setItem(row, 1, item_stat)
            self.tbl_map_players.setItem(row, 2, item_coords)

            if is_online:
                self.cb_teleport_target_player.addItem(uname)

    def _save_world_state(self):
        if hasattr(self, 'server_process') and self.server_process.is_running:
            self.server_process.send_command("save")
            QMessageBox.information(
                self, "Сохранение мира",
                "Команда 'save' отправлена серверу. Мир и позиции игроков сохраняются."
            )
            QTimer.singleShot(2000, self.refresh_map_players)
        else:
            QMessageBox.warning(self, "Внимание", "Сервер в данный момент остановлен.")

    def _do_teleport(self):
        target = self.pz_map_canvas.selected_target
        if not target:
            QMessageBox.warning(self, "Телепортация", "Сначала выберите точку на карте!")
            return

        uname = self.cb_teleport_target_player.currentText().strip()
        if not uname:
            QMessageBox.warning(self, "Телепортация", "Нет доступных игроков онлайн для телепортации.")
            return

        if not hasattr(self, 'server_process') or not self.server_process.is_running:
            QMessageBox.warning(self, "Ошибка", "Сервер не запущен. Телепортация невозможна.")
            return

        x = int(target["x"])
        y = int(target["y"])
        cmd = f'teleportto "{uname}" {x},{y},0'
        self.server_process.send_command(cmd)
        QMessageBox.information(
            self, "Телепортация",
            f"Игрок {uname} телепортирован на координаты ({x}, {y})!"
        )

    def _open_web_map(self):
        """Opens interactive web map in the user's default browser."""
        from core.config_manager import AppPreferences
        prefs = AppPreferences.load(self.paths)
        web_port = int(prefs.get('web_port', 8080))
        url = f"http://127.0.0.1:{web_port}/#map"
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")

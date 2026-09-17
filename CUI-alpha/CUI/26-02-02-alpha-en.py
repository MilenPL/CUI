#!/usr/bin/env python

# English language version

import sys
import os
import math
import shutil
import json
import subprocess

# Force the appropriate Qt variables for Wayland / X11
os.environ["QT_QPA_PLATFORM"] = "xcb;wayland"

try:
    from PyQt6.QtCore import Qt, QTime, QTimer, QRectF, QPointF, QFileSystemWatcher, QCoreApplication, QUrl
    from PyQt6.QtWidgets import (
        QApplication, QGraphicsView, QGraphicsScene, QGraphicsItem, 
        QGraphicsObject, QGraphicsEllipseItem, QGraphicsTextItem, 
        QGraphicsPixmapItem, QGraphicsProxyWidget, QLineEdit, QStyle, QToolTip,
        QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
        QFileDialog, QLabel, QTabWidget, QWidget, QComboBox, QInputDialog, QMessageBox
    )
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QIcon, QPixmap, QCursor, QDesktopServices
except ImportError as e:
    print(f"[ERROR] Missing required PyQt6 libraries: {e}")
    print("Install them with: pip install PyQt6")
    sys.exit(1)

# Resource and configuration paths
DATA_DIR = "CUI-DATA"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
WALLPAPER_DIR = os.path.join("grafic", "wallpapers")
DEFAULT_WALLPAPER_PATH = os.path.join(WALLPAPER_DIR, "wallpaper1.png")
LOGO_PATH = os.path.join("grafic", "GOD_logo2-removebg-preview.png")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WALLPAPER_DIR, exist_ok=True)

# Global color theme (default)
THEME_COLOR = QColor(0, 243, 255)
THEME_NAME = "Cyan (Default)"

COLOR_MAP = {
    "Cyan (Default)": QColor(0, 243, 255),
    "Green Neon": QColor(57, 255, 20),
    "Red Cyber": QColor(255, 0, 85),
    "Purple": QColor(170, 0, 255),
    "Orange": QColor(255, 110, 0),
    "Yellow": QColor(255, 230, 0)
}

# ==============================================================================
# 1. OKNO DIALOGOWE DOSTOSOWYWANIA IKON
# ==============================================================================
class IconCustomizeDialog(QDialog):
    def __init__(self, current_apps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize desktop icons")
        self.resize(450, 520)
        self.custom_apps = list(current_apps)
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #0a0f19; color: {THEME_COLOR.name()}; border: 2px solid {THEME_COLOR.name()}; font-family: Arial; }}
            QLabel {{ color: {THEME_COLOR.name()}; font-size: 13px; font-weight: bold; }}
            QListWidget {{ background-color: #050c19; border: 1px solid {THEME_COLOR.name()}; color: #ffffff; font-size: 12px; }}
            QListWidget::item:selected {{ background-color: rgba(0, 243, 255, 80); color: #ffffff; }}
            QPushButton {{ background-color: #0a1423; border: 1px solid {THEME_COLOR.name()}; color: {THEME_COLOR.name()}; padding: 6px 12px; border-radius: 6px; font-weight: bold; }}
            QPushButton:hover {{ background-color: rgba(0, 243, 255, 60); }}
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Manage icons on the ring (max 12):"))

        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        layout.addWidget(self.list_widget)

        self.refresh_list()

        action_btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add custom...")
        self.btn_remove = QPushButton("Remove selected")
        action_btn_layout.addWidget(self.btn_add)
        action_btn_layout.addWidget(self.btn_remove)
        layout.addLayout(action_btn_layout)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_add.clicked.connect(self.add_custom_icon)
        self.btn_remove.clicked.connect(self.remove_selected_icon)
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def refresh_list(self):
        self.list_widget.clear()
        for app in self.custom_apps:
            item = QListWidgetItem(app.name)
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.list_widget.addItem(item)

    def add_custom_icon(self):
        name, ok1 = QInputDialog.getText(self, "New Icon", "Enter icon name:")
        if ok1 and name:
            cmd, ok2 = QInputDialog.getText(self, "New Icon", "Enter command/path to launch:")
            if ok2 and cmd:
                new_item = RadialIconItem(name[:10], cmd, is_dir=os.path.isdir(cmd))
                self.custom_apps.append(new_item)
                self.refresh_list()

    def remove_selected_icon(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            del self.custom_apps[current_row]
            self.refresh_list()

    def get_ordered_apps(self):
        apps = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            apps.append(item.data(Qt.ItemDataRole.UserRole))
        return apps

# ==============================================================================
# 2. OKNO DIALOGOWE WYBORU TAPETY
# ==============================================================================
class WallpaperSelectorDialog(QDialog):
    def __init__(self, current_wallpaper_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wallpaper selection")
        self.resize(450, 400)
        self.selected_path = current_wallpaper_path
        self.setStyleSheet(f"""
            QDialog {{ background-color: #0a0f19; color: {THEME_COLOR.name()}; border: 2px solid {THEME_COLOR.name()}; font-family: Arial; }}
            QListWidget {{ background-color: #050c19; border: 1px solid {THEME_COLOR.name()}; color: #ffffff; }}
            QListWidget::item:selected {{ background-color: rgba(0, 243, 255, 80); color: {THEME_COLOR.name()}; }}
            QPushButton {{ background-color: #0a1423; border: 1px solid {THEME_COLOR.name()}; color: {THEME_COLOR.name()}; padding: 6px 12px; border-radius: 6px; font-weight: bold; }}
            QPushButton:hover {{ background-color: rgba(0, 243, 255, 60); }}
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Available wallpapers in grafic/wallpapers:"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.load_wallpapers()

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Upload new...")
        self.btn_apply = QPushButton("Apply")
        self.btn_cancel = QPushButton("Cancel")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_add.clicked.connect(self.upload_wallpaper)
        self.btn_apply.clicked.connect(self.apply_wallpaper)
        self.btn_cancel.clicked.connect(self.reject)

    def load_wallpapers(self):
        self.list_widget.clear()
        if os.path.exists(WALLPAPER_DIR):
            for file in os.listdir(WALLPAPER_DIR):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                    full_path = os.path.join(WALLPAPER_DIR, file)
                    item = QListWidgetItem(file)
                    item.setData(Qt.ItemDataRole.UserRole, full_path)
                    self.list_widget.addItem(item)
                    if full_path == self.selected_path:
                        self.list_widget.setCurrentItem(item)

    def upload_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a new wallpaper", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(WALLPAPER_DIR, filename)
            try:
                shutil.copy(file_path, dest_path)
                self.load_wallpapers()
            except Exception as e:
                print(f"[ERROR] Copy error: {e}")

    def apply_wallpaper(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_path = item.data(Qt.ItemDataRole.UserRole)
            self.accept()

# ==============================================================================
# 3. OKNO USTAWIENIA (SETTINGS DIALOG)
# ==============================================================================
class SettingsDialog(QDialog):
    def __init__(self, main_view, parent=None):
        super().__init__(parent)
        self.main_view = main_view
        self.setWindowTitle("System Settings")
        self.resize(550, 420)
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #0a0f19; color: {THEME_COLOR.name()}; border: 2px solid {THEME_COLOR.name()}; font-family: Arial; }}
            QTabWidget::pane {{ border: 1px solid {THEME_COLOR.name()}; background-color: #050c19; }}
            QTabBar::tab {{ background: #0a1423; color: {THEME_COLOR.name()}; padding: 8px 16px; border: 1px solid {THEME_COLOR.name()}; border-bottom: none; }}
            QTabBar::tab:selected {{ background: {THEME_COLOR.name()}; color: #0a0f19; font-weight: bold; }}
            QLabel {{ color: #ffffff; font-size: 12px; }}
            QPushButton {{ background-color: #0a1423; border: 1px solid {THEME_COLOR.name()}; color: {THEME_COLOR.name()}; padding: 6px 12px; border-radius: 6px; font-weight: bold; }}
            QPushButton:hover {{ background-color: rgba(0, 243, 255, 60); }}
            QComboBox, QListWidget {{ background-color: #0a1423; border: 1px solid {THEME_COLOR.name()}; color: #ffffff; padding: 4px; }}
        """)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Wallpaper
        tab_wallpaper = QWidget()
        lay_wp = QVBoxLayout(tab_wallpaper)
        lay_wp.addWidget(QLabel("Manage desktop background:"))
        btn_open_wp = QPushButton("Open Wallpaper Manager")
        btn_open_wp.clicked.connect(self.open_wp)
        lay_wp.addWidget(btn_open_wp)
        lay_wp.addStretch()
        self.tabs.addTab(tab_wallpaper, "Wallpaper")

        # Tab 2: Accent Color
        tab_color = QWidget()
        lay_col = QVBoxLayout(tab_color)
        lay_col.addWidget(QLabel("Choose the interface accent color:"))
        self.combo_color = QComboBox()
        self.combo_color.addItems(list(COLOR_MAP.keys()))
        self.combo_color.setCurrentText(self.main_view.theme_name)
        lay_col.addWidget(self.combo_color)
        btn_apply_color = QPushButton("Apply Color")
        btn_apply_color.clicked.connect(self.change_theme_color)
        lay_col.addWidget(btn_apply_color)
        lay_col.addStretch()
        self.tabs.addTab(tab_color, "Color")

        # Tab 3: Time Zone
        tab_tz = QWidget()
        lay_tz = QVBoxLayout(tab_tz)
        lay_tz.addWidget(QLabel("Set timezone:"))
        self.combo_tz = QComboBox()
        self.combo_tz.addItems(["UTC", "Europe/Warsaw", "Europe/London", "America/New_York", "Asia/Tokyo"])
        self.combo_tz.setCurrentText(self.main_view.timezone_str)
        lay_tz.addWidget(self.combo_tz)
        btn_apply_tz = QPushButton("Set Time Zone")
        btn_apply_tz.clicked.connect(self.change_timezone)
        lay_tz.addWidget(btn_apply_tz)
        lay_tz.addStretch()
        self.tabs.addTab(tab_tz, "Time Zone")

        # Tab 4: Linux Users
        tab_users = QWidget()
        lay_usr = QVBoxLayout(tab_users)
        lay_usr.addWidget(QLabel("Manage system users (Linux):"))
        self.user_list = QListWidget()
        lay_usr.addWidget(self.user_list)
        self.refresh_users()
        
        usr_btns = QHBoxLayout()
        btn_add_usr = QPushButton("Add User")
        btn_edit_usr = QPushButton("Edit Password")
        btn_del_usr = QPushButton("Delete User")
        usr_btns.addWidget(btn_add_usr)
        usr_btns.addWidget(btn_edit_usr)
        usr_btns.addWidget(btn_del_usr)
        lay_usr.addLayout(usr_btns)

        btn_add_usr.clicked.connect(self.add_user)
        btn_edit_usr.clicked.connect(self.edit_user)
        btn_del_usr.clicked.connect(self.del_user)
        self.tabs.addTab(tab_users, "Users")

        # Tab 5: Help
        tab_help = QWidget()
        lay_hp = QVBoxLayout(tab_help)
        self.btn_toggle_help = QPushButton("Toggle [?] Button Visibility")
        self.btn_toggle_help.clicked.connect(self.toggle_help_btn)
        lay_hp.addWidget(self.btn_toggle_help)

        lay_hp.addWidget(QLabel("Join our community:"))
        btn_discord = QPushButton("Open Discord (https://discord.gg/t7aPNRb69v)")
        btn_discord.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://discord.gg/t7aPNRb69v")))
        lay_hp.addWidget(btn_discord)
        lay_hp.addStretch()
        self.tabs.addTab(tab_help, "Help")

    def open_wp(self):
        self.main_view.open_wallpaper_selector()

    def change_theme_color(self):
        selected = self.combo_color.currentText()
        if selected in COLOR_MAP:
            self.main_view.set_theme_color(selected)
            QMessageBox.information(self, "Success", f"Accent color changed to {selected}!")

    def change_timezone(self):
        tz = self.combo_tz.currentText()
        self.main_view.set_timezone(tz)
        QMessageBox.information(self, "Time zone", f"Timezone set to: {tz}")

    def refresh_users(self):
        self.user_list.clear()
        try:
            with open("/etc/passwd", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) > 2 and int(parts[2]) >= 1000 and parts[0] != "nobody":
                        self.user_list.addItem(parts[0])
        except Exception:
            self.user_list.addItem("Error reading /etc/passwd")

    def add_user(self):
        username, ok = QInputDialog.getText(self, "Add User", "New username:")
        if ok and username:
            cmd = f"pkexec useradd -m {username}"
            subprocess.run(cmd, shell=True)
            self.refresh_users()

    def edit_user(self):
        item = self.user_list.currentItem()
        if item:
            username = item.text()
            cmd = f"pkexec passwd {username}"
            subprocess.run(cmd, shell=True)

    def del_user(self):
        item = self.user_list.currentItem()
        if item:
            username = item.text()
            cmd = f"pkexec userdel -r {username}"
            subprocess.run(cmd, shell=True)
            self.refresh_users()

    def toggle_help_btn(self):
        vis = not self.main_view.help_btn.isVisible()
        self.main_view.help_btn.setVisible(vis)
        self.main_view.help_text.setVisible(vis)

# ==============================================================================
# 4. POMOC / OVERLAY
# ==============================================================================
class HelpOverlayItem(QGraphicsObject):
    def __init__(self, help_button_item=None, help_text_item=None, parent=None):
        super().__init__(parent)
        self.help_button_item = help_button_item
        self.help_text_item = help_text_item
        self.setVisible(False)
        self.setZValue(100)

    def boundingRect(self):
        return QRectF(-250, -210, 500, 420)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(10, 15, 25, 245)))
        painter.setPen(QPen(THEME_COLOR, 2))
        painter.drawRoundedRect(-250, -210, 500, 420, 20, 20)

        painter.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        painter.setPen(THEME_COLOR)
        painter.drawText(QRectF(-230, -190, 460, 40), Qt.AlignmentFlag.AlignCenter, "USER GUIDE")

        help_text = (
            "• NAVIGATION & SHORTCUTS:\n"
            "  - [SUPER / WINDOWS]: Opens/closes the Applications Menu.\n"
            "  - [Right click on desktop]: Context menu with options (Settings, Icons, Wallpaper).\n"
            "  - [Back arrow]: Returns to the previous (higher) directory.\n"
            "  - [Home arrow]: Returns to the user-pinned start icons.\n\n"

            "• DESKTOP MENU & SETTINGS:\n"
            "  - You can customize the ring icons (add/remove).\n"
            "  - Change accent color, timezone, and users.\n"
            "  - You can hide this button (help [?]) in settings under the Help tab.\n\n"

            "• DISCORD SERVER:\n"
            "  - Join the community here: https://discord.gg/t7aPNRb69v"
        )
        painter.setFont(QFont("Arial", 10))
        painter.setPen(QColor(220, 235, 255))
        painter.drawText(QRectF(-220, -140, 440, 250), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, help_text)

        painter.setBrush(QBrush(THEME_COLOR))
        painter.setPen(QPen(THEME_COLOR, 1))
        painter.drawRoundedRect(-60, 150, 120, 35, 10, 10)
        
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QColor(10, 15, 25))
        painter.drawText(QRectF(-60, 150, 120, 35), Qt.AlignmentFlag.AlignCenter, "CLOSE")

    def mousePressEvent(self, event):
        if QRectF(-60, 150, 120, 35).contains(event.pos()):
            self.setVisible(False)
            event.accept()

# ==============================================================================
# 5. IKONY NA OBRĘCZY
# ==============================================================================
class RadialIconItem(QGraphicsObject):
    def __init__(self, name, path_or_cmd, is_dir=False, icon_name=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.path_or_cmd = path_or_cmd
        self.is_dir = is_dir
        self.icon_name = icon_name
        self.setAcceptHoverEvents(True)
        self.is_hovered = False
        self.setZValue(10)

        self.pixmap = None
        if icon_name:
            icon = QIcon.fromTheme(icon_name)
            if not icon.isNull():
                self.pixmap = icon.pixmap(32, 32)
        
        if not self.pixmap or self.pixmap.isNull():
            std_icon = QStyle.StandardPixmap.SP_DirIcon if is_dir else QStyle.StandardPixmap.SP_FileIcon
            self.pixmap = QApplication.style().standardIcon(std_icon).pixmap(32, 32)

    def boundingRect(self):
        return QRectF(-35, -35, 70, 90)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.is_hovered:
            border_color = THEME_COLOR
            bg_color = QColor(THEME_COLOR.red(), THEME_COLOR.green(), THEME_COLOR.blue(), 80)
            radius = 32
        else:
            border_color = THEME_COLOR
            bg_color = QColor(10, 20, 35, 210)
            radius = 28

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        if self.pixmap:
            painter.drawPixmap(-16, -16, 32, 32, self.pixmap)

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(-45, 33, 90, 25), Qt.AlignmentFlag.AlignCenter, self.name)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        view = self.scene().views()[0]
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dir:
                view.open_directory(self.path_or_cmd)
            else:
                view.launch_item(self.path_or_cmd, name=self.name)
        event.accept()

# ==============================================================================
# 6. TARCZA ZEGARA
# ==============================================================================
class CenterClockItem(QGraphicsObject):
    def __init__(self, logo_path=LOGO_PATH, parent=None):
        super().__init__(parent)
        self.time_str = QTime.currentTime().toString("hh:mm:ss")
        self.setZValue(10)
        
        self.logo_pixmap = QPixmap()
        if os.path.exists(logo_path):
            original_pixmap = QPixmap(logo_path)
            self.logo_pixmap = original_pixmap.scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def update_time(self):
        self.time_str = QTime.currentTime().toString("hh:mm:ss")
        self.update()

    def boundingRect(self):
        return QRectF(-90, -90, 180, 180)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(QColor(10, 15, 30, 220)))
        painter.setPen(QPen(THEME_COLOR, 2))
        painter.drawEllipse(QPointF(0, 0), 85, 85)

        if not self.logo_pixmap.isNull():
            pix_w = self.logo_pixmap.width()
            pix_h = self.logo_pixmap.height()
            painter.drawPixmap(int(-pix_w / 2), int(-pix_h / 2), self.logo_pixmap)

        painter.setBrush(QBrush(QColor(5, 10, 20, 160)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(-65, -18, 130, 32), 8, 8)

        painter.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        painter.setPen(THEME_COLOR)
        painter.drawText(QRectF(-80, -15, 160, 30), Qt.AlignmentFlag.AlignCenter, self.time_str)

        # Przycisk "Wstecz" (◄)
        painter.setBrush(QBrush(QColor(THEME_COLOR.red(), THEME_COLOR.green(), THEME_COLOR.blue(), 60)))
        painter.setPen(QPen(THEME_COLOR, 1))
        painter.drawEllipse(QRectF(-49, -64, 28, 28))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(-49, -64, 28, 28), Qt.AlignmentFlag.AlignCenter, "◄")

        # Przycisk "Home / Początek" (▲)
        painter.drawEllipse(QRectF(21, -64, 28, 28))
        painter.drawText(QRectF(21, -64, 28, 28), Qt.AlignmentFlag.AlignCenter, "▲")

    def mousePressEvent(self, event):
        pos = event.pos()
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        
        btn_back_rect = QRectF(-49, -64, 28, 28)
        btn_home_rect = QRectF(21, -64, 28, 28)

        if btn_back_rect.contains(pos):
            if view:
                view.go_back()
            event.accept()
        elif btn_home_rect.contains(pos):
            if view:
                view.go_home()
            event.accept()
        else:
            super().mousePressEvent(event)

# ==============================================================================
# 7. MENU PODRĘCZNE PULPITU (PPM) Z USTAWIENIAMI
# ==============================================================================
class DesktopContextMenuOverlay(QGraphicsObject):
    def __init__(self, main_view, parent=None):
        super().__init__(parent)
        self.main_view = main_view
        self.setVisible(False)
        self.setZValue(200)

    def boundingRect(self):
        return QRectF(-140, -160, 280, 320)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(QColor(8, 12, 22, 245)))
        painter.setPen(QPen(THEME_COLOR, 2))
        painter.drawEllipse(QPointF(0, 0), 145, 145)

        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        painter.setPen(THEME_COLOR)
        painter.drawText(QRectF(-100, -125, 200, 25), Qt.AlignmentFlag.AlignCenter, "DESKTOP MENU")

        options = ["Terminal", "Customize icons", "Wallpaper", "Settings"]
        for i, opt in enumerate(options):
            rect = QRectF(-100, -85 + (i * 45), 200, 36)
            painter.setBrush(QBrush(QColor(15, 25, 45, 220)))
            painter.setPen(QPen(QColor(THEME_COLOR.red(), THEME_COLOR.green(), THEME_COLOR.blue(), 150), 1))
            painter.drawRoundedRect(rect, 8, 8)

            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, opt)

    def mousePressEvent(self, event):
        pos = event.pos()
        options = ["Terminal", "Customize icons", "Wallpaper", "Settings"]
        
        for i, opt in enumerate(options):
            rect = QRectF(-100, -85 + (i * 45), 200, 36)
            if rect.contains(pos):
                self.setVisible(False)
                if opt == "Terminal":
                    self.main_view.launch_item(self.main_view.get_terminal_command(), name="Terminal")
                elif opt == "Customize icons":
                    self.main_view.open_icon_customizer()
                elif opt == "Wallpaper":
                    self.main_view.open_wallpaper_selector()
                elif opt == "Settings":
                    self.main_view.open_settings()
                event.accept()
                return

        self.setVisible(False)
        event.accept()

# ==============================================================================
# 8. MENU GŁÓWNE APLIKACJI
# ==============================================================================
class ApplicationMenuOverlay(QGraphicsObject):
    def __init__(self, main_view, parent=None):
        super().__init__(parent)
        self.main_view = main_view
        self.setVisible(False)
        self.setZValue(150)
        self.setAcceptHoverEvents(True)

        self.scroll_offset = 0

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search applications...")
        self.update_style()
        self.search_box.textChanged.connect(self.on_search_text_changed)

        self.proxy_search = QGraphicsProxyWidget(self)
        self.proxy_search.setWidget(self.search_box)
        self.proxy_search.setGeometry(QRectF(-160, -215, 320, 32))

        term_cmd = self.main_view.get_terminal_command()
        self.favorites = [{"name": "Terminal", "cmd": term_cmd}]
        self.init_app_scanner()

    def update_style(self):
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(5, 12, 25, 230);
                border: 2px solid {THEME_COLOR.name()};
                border-radius: 12px; color: {THEME_COLOR.name()};
                font-family: Consolas, Arial; font-size: 13px; padding: 4px 10px;
            }}
        """)

    def init_app_scanner(self):
        self.refresh_system_apps()

        self.watcher = QFileSystemWatcher()
        watch_dirs = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
        existing_dirs = [d for d in watch_dirs if os.path.exists(d)]
        if existing_dirs:
            self.watcher.addPaths(existing_dirs)
            self.watcher.directoryChanged.connect(self.refresh_system_apps)

    def refresh_system_apps(self):
        self.all_apps = self.scan_desktop_files()
        self.on_search_text_changed(self.search_box.text())

    def scan_desktop_files(self):
        dirs_to_scan = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
        apps_dict = {}
        for directory in dirs_to_scan:
            if not os.path.exists(directory):
                continue
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(".desktop"):
                        filepath = os.path.join(root, file)
                        app_info = self.parse_desktop_file(filepath)
                        if app_info and app_info["name"] and app_info["cmd"]:
                            apps_dict[app_info["name"]] = app_info

        return sorted(list(apps_dict.values()), key=lambda x: x["name"].lower())

    def parse_desktop_file(self, filepath):
        try:
            name, cmd, icon, no_display = None, None, None, False
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                in_entry = False
                for line in f:
                    line = line.strip()
                    if line == "[Desktop Entry]":
                        in_entry = True
                        continue
                    elif line.startswith("[") and line.endswith("]"):
                        in_entry = False

                    if in_entry:
                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1]
                        elif line.startswith("Exec=") and not cmd:
                            raw_cmd = line.split("=", 1)[1]
                            cmd = " ".join([arg for arg in raw_cmd.split() if not arg.startswith("%")])
                        elif line.startswith("Icon=") and not icon:
                            icon = line.split("=", 1)[1]
                        elif line.startswith("NoDisplay=true"):
                            no_display = True

            if no_display:
                return None

            return {"name": name, "cmd": cmd, "icon": icon}
        except Exception:
            return None

    def get_battery_info(self):
        bat_path = "/sys/class/power_supply"
        if os.path.exists(bat_path):
            for dev in os.listdir(bat_path):
                if dev.startswith("BAT"):
                    cap_file = os.path.join(bat_path, dev, "capacity")
                    stat_file = os.path.join(bat_path, dev, "status")
                    capacity, status = "N/A", ""
                    if os.path.exists(cap_file):
                        with open(cap_file, "r") as f:
                            capacity = f.read().strip()
                    if os.path.exists(stat_file):
                        with open(stat_file, "r") as f:
                            status = f.read().strip()
                    status_str = " (Charging)" if status == "Charging" else ""
                    return f"{capacity}%{status_str}", int(capacity) if capacity.isdigit() else 100
        return "No battery / AC power", 100

    def on_search_text_changed(self, text):
        query = text.strip().lower()
        self.scroll_offset = 0
        if not query:
            self.filtered_apps = list(self.all_apps)
        else:
            self.filtered_apps = [a for a in self.all_apps if query in a["name"].lower() or query in a["cmd"].lower()]
        self.update()

    def wheelEvent(self, event):
        delta = event.delta()
        if delta < 0:
            if self.scroll_offset + 7 < len(self.filtered_apps):
                self.scroll_offset += 1
        else:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
        self.update()
        event.accept()

    def boundingRect(self):
        return QRectF(-260, -260, 520, 520)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(QColor(8, 12, 22, 245)))
        painter.setPen(QPen(THEME_COLOR, 3))
        painter.drawEllipse(QPointF(0, 0), 250, 250)

        painter.setBrush(QBrush(QColor(12, 20, 36, 220)))
        painter.setPen(QPen(QColor(THEME_COLOR.red(), THEME_COLOR.green(), THEME_COLOR.blue(), 120), 1))
        painter.drawEllipse(QPointF(0, 0), 80, 80)

        painter.setPen(QPen(QColor(THEME_COLOR.red(), THEME_COLOR.green(), THEME_COLOR.blue(), 80), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, -170, 0, 160)
        painter.drawLine(80, 0, 240, 0)

        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        painter.setPen(THEME_COLOR)
        painter.drawText(QRectF(-230, -175, 210, 25), Qt.AlignmentFlag.AlignCenter, f"ALL ({len(self.filtered_apps)})")
        painter.drawText(QRectF(20, -175, 210, 25), Qt.AlignmentFlag.AlignCenter, "★ FAVORITES ★")
        painter.drawText(QRectF(20, 10, 210, 25), Qt.AlignmentFlag.AlignCenter, "🕒 RECENTLY USED")

        # All
        painter.setFont(QFont("Arial", 9))
        visible_apps = self.filtered_apps[self.scroll_offset : self.scroll_offset + 7]
        for i, app in enumerate(visible_apps):
            item_rect = QRectF(-230, -140 + (i * 38), 210, 32)
            is_fav = any(f["cmd"] == app["cmd"] for f in self.favorites)
            
            painter.setBrush(QBrush(QColor(THEME_COLOR.red(), THEME_COLOR.green(), THEME_COLOR.blue(), 30) if is_fav else QColor(15, 25, 45, 180)))
            painter.setPen(QPen(THEME_COLOR if is_fav else QColor(0, 180, 255, 100), 1))
            painter.drawRoundedRect(item_rect, 6, 6)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(item_rect.adjusted(10, 0, -25, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, app["name"])
            
            painter.setPen(THEME_COLOR if is_fav else QColor(100, 120, 150))
            painter.drawText(item_rect.adjusted(180, 0, -5, 0), Qt.AlignmentFlag.AlignCenter, "★" if is_fav else "☆")

        # Favorites
        fav_items = self.favorites[:4]
        for i, app in enumerate(fav_items):
            item_rect = QRectF(20, -140 + (i * 38), 210, 32)
            painter.setBrush(QBrush(QColor(THEME_COLOR.red(), THEME_COLOR.green(), THEME_COLOR.blue(), 40)))
            painter.setPen(QPen(THEME_COLOR, 1))
            painter.drawRoundedRect(item_rect, 6, 6)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(item_rect.adjusted(10, 0, -10, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, app["name"])

        # Recently Used
        recent_items = self.main_view.recent_apps[:3]
        for i, app in enumerate(recent_items):
            item_rect = QRectF(20, 40 + (i * 38), 210, 32)
            painter.setBrush(QBrush(QColor(20, 35, 60, 180)))
            painter.setPen(QPen(QColor(0, 180, 255, 120), 1))
            painter.drawRoundedRect(item_rect, 6, 6)

            painter.setPen(QColor(220, 235, 255))
            painter.drawText(item_rect.adjusted(10, 0, -10, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, app["name"])

        # Dolny pasek
        bottom_bar_rect = QRectF(-90, 185, 180, 42)
        painter.setBrush(QBrush(QColor(10, 20, 35, 230)))
        painter.setPen(QPen(THEME_COLOR, 1))
        painter.drawRoundedRect(bottom_bar_rect, 21, 21)

        # Battery
        bat_info_str, bat_percent = self.get_battery_info()
        bat_color = THEME_COLOR if bat_percent > 20 else QColor(255, 60, 60)
        
        painter.setPen(QPen(bat_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(-65, 197, 24, 16), 3, 3)
        painter.drawRect(QRectF(-41, 201, 2, 8))
        
        fill_width = max(0, min(18, int(18 * (bat_percent / 100.0))))
        if fill_width > 0:
            painter.setBrush(QBrush(bat_color))
            painter.drawRect(QRectF(-63, 199, fill_width, 12))

        # Restart
        painter.setPen(QPen(THEME_COLOR, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(-11, 195, 22, 22), 40 * 16, 280 * 16)
        painter.setBrush(QBrush(THEME_COLOR))
        painter.drawPolygon(QPointF(4, 193), QPointF(10, 197), QPointF(4, 201))

        # Shutdown
        painter.setPen(QPen(QColor(255, 60, 90), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(39, 195, 22, 22), -50 * 16, 280 * 16)
        painter.drawLine(50, 193, 50, 204)

    def hoverMoveEvent(self, event):
        pos = event.pos()
        if QRectF(-70, 190, 40, 30).contains(pos):
            bat_str, _ = self.get_battery_info()
            QToolTip.showText(QCursor.pos(), f"Battery: {bat_str}")
        else:
            QToolTip.hideText()
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        pos = event.pos()

        if QRectF(-160, -215, 320, 32).contains(pos):
            self.search_box.setFocus()
            event.accept()
            return

        if QRectF(35, 190, 35, 32).contains(pos):
            QApplication.quit()
            event.accept()
            return

        if QRectF(-18, 190, 35, 32).contains(pos):
            QCoreApplication.quit()
            subprocess.Popen([sys.executable] + sys.argv)
            event.accept()
            return

        visible_apps = self.filtered_apps[self.scroll_offset : self.scroll_offset + 7]
        for i, app in enumerate(visible_apps):
            item_rect = QRectF(-230, -140 + (i * 38), 210, 32)
            if item_rect.contains(pos):
                if event.button() == Qt.MouseButton.RightButton:
                    if any(f["cmd"] == app["cmd"] for f in self.favorites):
                        self.favorites = [f for f in self.favorites if f["cmd"] != app["cmd"]]
                    else:
                        self.favorites.append(app)
                    self.update()
                else:
                    self.main_view.launch_item(app["cmd"], name=app["name"])
                    self.toggle_menu(False)
                event.accept()
                return

        fav_items = self.favorites[:4]
        for i, app in enumerate(fav_items):
            item_rect = QRectF(20, -140 + (i * 38), 210, 32)
            if item_rect.contains(pos):
                self.main_view.launch_item(app["cmd"], name=app["name"])
                self.toggle_menu(False)
                event.accept()
                return

        recent_items = self.main_view.recent_apps[:3]
        for i, app in enumerate(recent_items):
            item_rect = QRectF(20, 40 + (i * 38), 210, 32)
            if item_rect.contains(pos):
                self.main_view.launch_item(app["cmd"], name=app["name"])
                self.toggle_menu(False)
                event.accept()
                return

        event.accept()

    def toggle_menu(self, state=None):
        new_state = not self.isVisible() if state is None else state
        self.setVisible(new_state)
        if new_state:
            self.scroll_offset = 0
            self.search_box.setText("")
            self.search_box.setFocus()
            self.update()

# ==============================================================================
# 9. GŁÓWNY WIDOK / PULPIT
# ==============================================================================
class RadialDesktopView(QGraphicsView):
    def __init__(self, wallpaper_path=DEFAULT_WALLPAPER_PATH):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.wallpaper_path = wallpaper_path
        self.theme_name = THEME_NAME
        self.timezone_str = "Europe/Warsaw"
        self.bg_item = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background: black;")
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.history_stack = []
        self.root_items = []
        self.current_items = []
        self.recent_apps = []

        self.is_kde = os.environ.get("XDG_CURRENT_DESKTOP", "").upper() == "KDE"
        self.disable_kde_super_key()

        self.init_ui()
        self.load_config()

    def disable_kde_super_key(self):
        """Zasłania/zablokuje działanie klawisza Super dla menu Plasmy na środowisku KDE, gdy dostępny jest qdbus."""
        if self.is_kde:
            try:
                # Sprawdzenie czy qdbus jest dostępny
                if subprocess.call(["which", "qdbus"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    subprocess.run([
                        "qdbus", "org.kde.kglobalaccel", "/component/krunner",
                        "org.kde.kglobalaccel.Component.invokeShortcut", "_launch"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    subprocess.run([
                        "kwriteconfig5", "--file", "kwinrc",
                        "--group", "ModifierOnlyShortcuts",
                        "--key", "Meta", ""
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    subprocess.run([
                        "qdbus", "org.kde.KWin", "/KWin", "reconfigure"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"[KDE] Nie udało się zablokować klawisza Super: {e}")

    def restore_kde_super_key(self):
        """Przywraca domyślne działanie klawisza Super w KDE Plasma."""
        if self.is_kde:
            try:
                if subprocess.call(["which", "qdbus"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    subprocess.run([
                        "kwriteconfig5", "--file", "kwinrc",
                        "--group", "ModifierOnlyShortcuts",
                        "--key", "Meta", "org.kde.plasmashell,/PlasmaShell,org.kde.PlasmaShell,activateLauncherMenu"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    subprocess.run([
                        "qdbus", "org.kde.KWin", "/KWin", "reconfigure"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"[KDE] Nie udało się przywrócić skrótu Super: {e}")

    def get_terminal_command(self):
        term_list = ["gnome-terminal", "kitty", "alacritty", "konsole", "xfce4-terminal", "x-terminal-emulator"]
        for cmd in term_list:
            if subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                return cmd
        return "gnome-terminal"

    def init_ui(self):
        screen = QApplication.primaryScreen()
        if not screen:
            sys.exit(1)

        screen_rect = screen.geometry()
        self.screen_w = screen_rect.width()
        self.screen_h = screen_rect.height()
        self.scene.setSceneRect(0, 0, self.screen_w, self.screen_h)

        self.center_x = self.screen_w / 2
        self.center_y = self.screen_h / 2

        self.set_wallpaper(self.wallpaper_path)

        self.glass_disk = QGraphicsEllipseItem(self.center_x - 260, self.center_y - 260, 520, 520)
        self.glass_disk.setBrush(QBrush(QColor(10, 20, 35, 120)))
        self.glass_disk.setPen(QPen(THEME_COLOR, 3))
        self.glass_disk.setZValue(5)
        self.scene.addItem(self.glass_disk)

        self.clock = CenterClockItem(logo_path=LOGO_PATH)
        self.clock.setPos(self.center_x, self.center_y)
        self.scene.addItem(self.clock)

        self.help_btn = QGraphicsEllipseItem(self.screen_w - 80, self.screen_h - 80, 50, 50)
        self.help_btn.setBrush(QBrush(QColor(10, 20, 35, 200)))
        self.help_btn.setPen(QPen(THEME_COLOR, 2))
        self.help_btn.setZValue(10)
        self.scene.addItem(self.help_btn)

        self.help_text = QGraphicsTextItem("?", self.help_btn)
        self.help_text.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.help_text.setDefaultTextColor(THEME_COLOR)
        self.help_text.setPos(self.screen_w - 67, self.screen_h - 73)
        self.help_text.setZValue(11)

        self.help_overlay = HelpOverlayItem(self.help_btn, self.help_text)
        self.help_overlay.setPos(self.center_x, self.center_y)
        self.scene.addItem(self.help_overlay)

        self.help_btn.setAcceptHoverEvents(True)
        self.help_btn.mousePressEvent = lambda e: self.help_overlay.setVisible(True)

        self.app_menu = ApplicationMenuOverlay(self)
        self.app_menu.setPos(self.center_x, self.center_y)
        self.scene.addItem(self.app_menu)

        self.desktop_context_menu = DesktopContextMenuOverlay(self)
        self.desktop_context_menu.setPos(self.center_x, self.center_y)
        self.scene.addItem(self.desktop_context_menu)

        self.load_desktop_level()

    def set_theme_color(self, name):
        global THEME_COLOR
        if name in COLOR_MAP:
            THEME_COLOR = COLOR_MAP[name]
            self.theme_name = name
            self.update_theme()

    def set_timezone(self, tz_str):
        self.timezone_str = tz_str
        os.environ['TZ'] = tz_str
        try:
            import time
            time.tzset()
        except AttributeError:
            pass

    def update_theme(self):
        self.glass_disk.setPen(QPen(THEME_COLOR, 3))
        self.help_btn.setPen(QPen(THEME_COLOR, 2))
        self.help_text.setDefaultTextColor(THEME_COLOR)
        self.app_menu.update_style()
        self.scene.update()

    def set_wallpaper(self, wallpaper_path):
        if self.bg_item:
            self.scene.removeItem(self.bg_item)
            self.bg_item = None

        self.wallpaper_path = wallpaper_path
        if os.path.exists(wallpaper_path):
            wallpaper_pix = QPixmap(wallpaper_path)
            scaled_wallpaper = wallpaper_pix.scaled(
                self.screen_w, self.screen_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.bg_item = QGraphicsPixmapItem(scaled_wallpaper)
            bg_x = (self.screen_w - scaled_wallpaper.width()) / 2
            bg_y = (self.screen_h - scaled_wallpaper.height()) / 2
            self.bg_item.setPos(bg_x, bg_y)
            self.bg_item.setZValue(0)
            self.scene.addItem(self.bg_item)

    def get_default_apps(self):
        home = os.path.expanduser("~")

        def find_cmd(cmd_list):
            for cmd in cmd_list:
                if subprocess.call(["which", cmd.split()[0]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    return cmd
            return cmd_list[0]

        term_cmd = self.get_terminal_command()
        browser_cmd = find_cmd(["google-chrome", "firefox", "chromium", "brave-browser", "x-www-browser"])
        file_mgr_cmd = find_cmd(["nautilus", "thunar", "dolphin", "pcmanfm"])
        calc_cmd = find_cmd(["gnome-calculator", "kcalc", "galculator"])

        return [
            RadialIconItem("Terminal", term_cmd, is_dir=False, icon_name="utilities-terminal"),
            RadialIconItem("Browser", browser_cmd, is_dir=False, icon_name="web-browser"),
            RadialIconItem("Documents", os.path.join(home, "Documents"), is_dir=True, icon_name="folder-documents"),
            RadialIconItem("Downloads", os.path.join(home, "Downloads"), is_dir=True, icon_name="folder-download"),
            RadialIconItem("Music", os.path.join(home, "Music"), is_dir=True, icon_name="folder-music"),
            RadialIconItem("Pictures", os.path.join(home, "Pictures"), is_dir=True, icon_name="folder-pictures"),
            RadialIconItem("Videos", os.path.join(home, "Videos"), is_dir=True, icon_name="folder-videos"),
            RadialIconItem("Code / Editor", find_cmd(["code", "vscodium", "gedit", "kate"]), is_dir=False, icon_name="text-editor"),
            RadialIconItem("Settings", find_cmd(["gnome-control-center", "systemsettings", "xfce4-settings-manager"]), is_dir=False, icon_name="preferences-system"),
            RadialIconItem("Manager", file_mgr_cmd, is_dir=False, icon_name="system-file-manager"),
            RadialIconItem("Home", home, is_dir=True, icon_name="user-home"),
            RadialIconItem("Calculator", calc_cmd, is_dir=False, icon_name="accessories-calculator")
        ]

    def render_orbit_items(self, items_list):
        for item in self.current_items:
            self.scene.removeItem(item)
        self.current_items.clear()

        orbit_radius = 200
        count = min(12, len(items_list))

        for i in range(count):
            item = items_list[i]
            angle_deg = (i * 30) - 90
            angle_rad = math.radians(angle_deg)

            x = self.center_x + orbit_radius * math.cos(angle_rad)
            y = self.center_y + orbit_radius * math.sin(angle_rad)

            item.setPos(x, y)
            self.scene.addItem(item)
            self.current_items.append(item)

    def load_desktop_level(self):
        self.history_stack.clear()
        self.root_items = self.get_default_apps()
        self.render_orbit_items(self.root_items)

    def open_directory(self, path):
        if not os.path.exists(path):
            return

        self.history_stack.append(list(self.current_items))

        try:
            entries = os.listdir(path)[:12]
            new_items = []
            for entry in entries:
                full_path = os.path.join(path, entry)
                is_dir = os.path.isdir(full_path)
                icon_name = "folder" if is_dir else "text-x-generic"
                new_items.append(RadialIconItem(entry[:10], full_path, is_dir=is_dir, icon_name=icon_name))

            if not new_items:
                new_items.append(RadialIconItem("[Empty]", "", is_dir=False, icon_name="dialog-information"))

            self.render_orbit_items(new_items)
        except PermissionError:
            pass

    def go_back(self):
        if self.history_stack:
            previous_items = self.history_stack.pop()
            self.render_orbit_items(previous_items)

    def go_home(self):
        """Returns to the main desktop while preserving the current customized icon list."""
        self.history_stack.clear()
        if self.root_items:
            self.render_orbit_items(self.root_items)
        else:
            self.load_desktop_level()

    def launch_item(self, cmd_or_path, name=None):
        if not cmd_or_path:
            return
            
        try:
            if os.path.exists(cmd_or_path):
                subprocess.Popen(["xdg-open", cmd_or_path], start_new_session=True)
            else:
                subprocess.Popen(cmd_or_path, shell=True, start_new_session=True)
                
            app_name = name if name else os.path.basename(cmd_or_path)
            self.recent_apps = [a for a in self.recent_apps if a["cmd"] != cmd_or_path]
            self.recent_apps.insert(0, {"name": app_name, "cmd": cmd_or_path})
            
        except Exception as e:
            print(f"[ERROR] Failed to launch '{cmd_or_path}': {e}")

    def open_icon_customizer(self):
        dialog = IconCustomizeDialog(self.current_items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_ordered_apps = dialog.get_ordered_apps()
            
            # Jeśli dostosowujemy ikonki w katalogu głównym (brak stosu cofania), zapisujemy je jako bazowe root_items
            if not self.history_stack:
                self.root_items = new_ordered_apps
                
            self.render_orbit_items(new_ordered_apps)
            self.save_config()

    def open_wallpaper_selector(self):
        dialog = WallpaperSelectorDialog(self.wallpaper_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.set_wallpaper(dialog.selected_path)
            self.save_config()

    def open_settings(self):
        dialog = SettingsDialog(self, self)
        dialog.exec()
        self.save_config()

    # ZAPIS I ODCZYT KONFIGURACJI Z CUI-DATA/
    def save_config(self):
        items_to_save = self.root_items if self.root_items else self.current_items
        config_data = {
            "wallpaper": self.wallpaper_path,
            "theme_name": self.theme_name,
            "timezone": self.timezone_str,
            "help_button_visible": self.help_btn.isVisible(),
            "orbit_icons": [
                {
                    "name": item.name,
                    "cmd": item.path_or_cmd,
                    "is_dir": item.is_dir,
                    "icon_name": item.icon_name
                }
                for item in items_to_save
            ]
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print(f"[CUI-DATA] Configuration saved successfully in {CONFIG_FILE}")
        except Exception as e:
            print(f"[ERROR] Failed to save configuration: {e}")

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            if "wallpaper" in config_data:
                self.set_wallpaper(config_data["wallpaper"])

            if "theme_name" in config_data:
                self.set_theme_color(config_data["theme_name"])

            if "timezone" in config_data:
                self.set_timezone(config_data["timezone"])

            if "help_button_visible" in config_data:
                vis = config_data["help_button_visible"]
                self.help_btn.setVisible(vis)
                self.help_text.setVisible(vis)

            if "orbit_icons" in config_data and isinstance(config_data["orbit_icons"], list):
                custom_items = []
                for ic in config_data["orbit_icons"]:
                    custom_items.append(
                        RadialIconItem(
                            ic["name"], 
                            ic["cmd"], 
                            is_dir=ic.get("is_dir", False), 
                            icon_name=ic.get("icon_name")
                        )
                    )
                if custom_items:
                    self.root_items = custom_items
                    self.render_orbit_items(self.root_items)

            print(f"[CUI-DATA] Configuration loaded from {CONFIG_FILE}")
        except Exception as e:
            print(f"[ERROR] Failed to read configuration: {e}")

    def closeEvent(self, event):
        self.save_config()
        self.restore_kde_super_key()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if event.button() == Qt.MouseButton.RightButton:
            if item is None or item == self.bg_item:
                self.desktop_context_menu.setPos(self.center_x, self.center_y)
                self.desktop_context_menu.setVisible(True)
                event.accept()
                return

        if self.desktop_context_menu.isVisible() and item != self.desktop_context_menu:
            self.desktop_context_menu.setVisible(False)

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R):
            self.app_menu.toggle_menu()
            return

        if event.key() == Qt.Key.Key_Escape:
            if self.desktop_context_menu.isVisible():
                self.desktop_context_menu.setVisible(False)
            elif self.app_menu.isVisible():
                self.app_menu.toggle_menu(False)
            elif self.help_overlay.isVisible():
                self.help_overlay.setVisible(False)
        else:
            super().keyPressEvent(event)

# ==============================================================================
# 10. START PROGRAMU
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    desktop = RadialDesktopView()
    desktop.showFullScreen()
    sys.exit(app.exec())
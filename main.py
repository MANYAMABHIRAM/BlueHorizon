import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                           QPushButton, QLabel, QDialog, QGraphicsOpacityEffect)
from PyQt6.QtGui import QPalette, QColor, QLinearGradient, QBrush, QPixmap, QPainter, QFont, QRadialGradient
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect, QSize, QVariantAnimation, pyqtProperty ,  QThread, pyqtSignal
from telemetry import TelemetryWidget
from hud import EnhancedHUDWidget
from messages import MessagesWidget
from map_widget import MapWidget
from gauges import GaugesWidget
from pymavlink import mavutil
from threadentities import MonitoringThread , ConnectionThread

class FuturisticDialog(QDialog):
    def __init__(self, parent=None, success=True, connecting=False, show_button=False):
        super().__init__(parent)
        
        # Remove title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # Set fixed size
        self.setFixedSize(350, 180)
        
        # Make background partially transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)
        
        # Create a container widget for the background
        container = QWidget(self)
        container.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)
        
        # Status and message
        if connecting:
            self.status = "CONNECTING"
            self.message = "Establishing secure link..."
            self.status_color = "#ffaa00"  # Orange/amber for connecting state
            self.border_color = "#cc8800"
        elif success:
            self.status = "CONNECTION ESTABLISHED"
            self.message = "Secure link active"
            self.status_color = "#00ffaa"
            self.border_color = "#00cc88"
        else:
            self.status = "CONNECTION FAILED"
            self.message = "Unable to establish secure link"
            self.status_color = "#ff3366"
            self.border_color = "#cc2952"
        
        # Status label with hexagon indicator
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        
        # Hexagon indicator
        hex_indicator = QLabel()
        hex_indicator.setFixedSize(12, 12)
        hex_indicator.setObjectName("hexIndicator")
        hex_indicator.setStyleSheet(f"background-color: {self.status_color}; border-radius: 6px;")
        
        # For connecting state, create blinking effect
        if connecting:
            self.blink_timer = QTimer(self)
            self.blink_timer.timeout.connect(self.toggle_indicator)
            self.blink_timer.start(500)  # Toggle every 500ms
            self.indicator_on = True
        
        # Status label
        status_label = QLabel(self.status)
        status_label.setObjectName("statusLabel")
        status_label.setStyleSheet(f"color: {self.status_color}; font-weight: bold; font-size: 14px;")
        
        status_layout.addWidget(hex_indicator)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        
        # Message label
        message_label = QLabel(self.message)
        message_label.setObjectName("messageLabel")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar (for visual effect)
        progress_bar = QWidget()
        progress_bar.setFixedHeight(4)
        progress_bar.setObjectName("progressBar")
        
        # Create animation for progress bar
        self.progress_animation = QVariantAnimation()
        
        # For connecting dialog, we modify the animation
        if connecting:
            # We'll use animation phase values 0-100 to control different stages of animation
            self.progress_animation.setStartValue(0)
            self.progress_animation.setEndValue(100)
            self.progress_animation.setDuration(2000)  # 2 seconds for a complete cycle
            self.progress_animation.valueChanged.connect(self.update_connecting_progress)
            # Make it loop continuously
            self.progress_animation.finished.connect(self.restart_progress_animation)
            
            # Track animation phase
            self.animation_phase = 0  # 0: growing, 1: moving, 2: shrinking
            self.max_width_percent = 30  # Maximum width as percentage of bar width
        else:
            self.progress_animation.setStartValue(0)
            self.progress_animation.setEndValue(100)
            self.progress_animation.setDuration(1800)  # Slightly shorter than dialog duration
            self.progress_animation.valueChanged.connect(self.update_progress)
        
        # Add widgets to container layout
        container_layout.addWidget(status_widget)
        container_layout.addWidget(message_label)
        container_layout.addWidget(progress_bar)
        
        # Only add button if requested
        if show_button:
            # Button based on state
            if connecting:
                close_button = QPushButton("CANCEL")
            else:
                close_button = QPushButton("CLOSE")
                
            close_button.setObjectName("dialogCloseBtn")
            close_button.clicked.connect(self.close)
            close_button.setFixedSize(100, 30)
            
            # Center the close button
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            button_layout.addStretch()
            
            container_layout.addSpacing(5)
            container_layout.addLayout(button_layout)
        
        # Add container to main layout
        self.layout.addWidget(container)
        
        # Set style for the dialog
        self.setStyleSheet(f"""
            QWidget#dialogContainer {{
                background-color: rgba(10, 15, 30, 230);
                border: 1px solid {self.border_color};
                border-radius: 8px;
            }}
            QLabel#statusLabel {{
                color: {self.status_color};
                font-weight: bold;
                font-family: 'Segoe UI';
                font-size: 14px;
                background-color: transparent;
            }}
            QLabel#messageLabel {{
                color: #d2e6ff;
                font-weight: normal;
                font-family: 'Segoe UI';
                font-size: 12px;
                background-color: transparent;
            }}
            QLabel#hexIndicator {{
                background-color: {self.status_color};
                border-radius: 6px;
            }}
            QWidget#progressBar {{
                background-color: rgba(255, 255, 255, 50);
                border-radius: 2px;
            }}
            QPushButton#dialogCloseBtn {{
                background-color: rgba(30, 40, 80, 200);
                border: 1px solid {self.border_color};
                border-radius: 4px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px 15px;
                font-family: 'Segoe UI';
                font-size: 11px;
            }}
            QPushButton#dialogCloseBtn:hover {{
                background-color: rgba(40, 55, 100, 220);
                border: 1px solid #0078ff;
            }}
            QPushButton#dialogCloseBtn:pressed {{
                background-color: rgba(20, 30, 60, 200);
            }}
        """)
        
        # Create progress bar fill
        self.progress_fill = QWidget(progress_bar)
        self.progress_fill.setObjectName("progressFill")
        self.progress_fill.setFixedHeight(4)
        self.progress_fill.setStyleSheet(f"background-color: {self.status_color}; border-radius: 2px;")
        self.progress_fill.setFixedWidth(0)  # Start with width 0
        
        # For connecting state, we don't auto-close
        if not connecting:
            # Fade-in animation
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)
            self.opacity_effect.setOpacity(0)
            
            self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_in.setDuration(300)
            self.fade_in.setStartValue(0)
            self.fade_in.setEndValue(1)
            self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # Fade-out animation
            self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_out.setDuration(300)
            self.fade_out.setStartValue(1)
            self.fade_out.setEndValue(0)
            self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
            self.fade_out.finished.connect(self.close)
            
            # Setup auto-close timer
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.start_fade_out)
            self.timer.setSingleShot(True)
        else:
            # For connecting dialog, we don't need fade effects
            self.opacity_effect = None
        
        # Center the dialog on the parent
        if parent:
            self.move(parent.rect().center() - self.rect().center())
    
    def restart_progress_animation(self):
        """Restart the progress animation to create a continuous loop"""
        self.progress_animation.start()
    
    def toggle_indicator(self):
        """Toggle the indicator for connecting state"""
        hex_indicator = self.findChild(QLabel, "hexIndicator")
        if self.indicator_on:
            hex_indicator.setStyleSheet(f"background-color: transparent; border: 1px solid {self.status_color}; border-radius: 6px;")
            self.indicator_on = False
        else:
            hex_indicator.setStyleSheet(f"background-color: {self.status_color}; border-radius: 6px;")
            self.indicator_on = True
    
    def update_connecting_progress(self, value):
        """
        Update progress bar for connecting animation with the new behavior:
        1. Start width = 0
        2. Grow to 30% width
        3. Move right
        4. Shrink to 0 at right edge
        5. Repeat
        """
        progress_bar = self.findChild(QWidget, "progressBar")
        if not progress_bar:
            return
            
        bar_width = progress_bar.width()
        max_indicator_width = bar_width * (self.max_width_percent / 100.0)  # 30% of total width
        
        # Divide the animation into 3 phases: growing (0-33), moving (33-66), shrinking (66-100)
        if value <= 33:  # Growing phase (0% -> 30% width)
            phase_progress = value / 33.0  # 0 to 1
            indicator_width = max_indicator_width * phase_progress
            position = 0  # Fixed at left edge
        elif value <= 66:  # Moving phase (maintains 30% width but moves right)
            phase_progress = (value - 33) / 33.0  # 0 to 1
            indicator_width = max_indicator_width
            # Move from left edge to position where right edge will touch end (bar_width - indicator_width)
            position = phase_progress * (bar_width - max_indicator_width)
        else:  # Shrinking phase (30% -> 0% width while at right edge)
            phase_progress = (value - 66) / 34.0  # 0 to 1
            indicator_width = max_indicator_width * (1 - phase_progress)
            # Position needs to be updated as width shrinks to keep right edge fixed
            position = bar_width - indicator_width
        
        # Set width and position
        self.progress_fill.setFixedWidth(int(indicator_width))
        self.progress_fill.move(int(position), 0)
            
    def showEvent(self, event):
        """Override showEvent to start animations when dialog appears"""
        super().showEvent(event)
        
        # Start appropriate animations based on dialog type
        if hasattr(self, 'fade_in'):
            self.fade_in.start()
            
        self.progress_animation.start()
        
        if hasattr(self, 'timer'):
            self.timer.start(2000)  # 2000 milliseconds = 2 seconds
        
    def update_progress(self, value):
        """Update progress bar width based on animation value"""
        progress_bar_width = self.findChild(QWidget, "progressBar").width()
        progress_width = int(progress_bar_width * value / 100)
        self.progress_fill.setFixedWidth(progress_width)
        
    def start_fade_out(self):
        """Start fade out animation"""
        if hasattr(self, 'fade_out'):
            self.fade_out.start()
    
    def closeEvent(self, event):
        if hasattr(self, 'blink_timer') and self.blink_timer.isActive():
            self.blink_timer.stop()
            
        super().closeEvent(event)

class BlueHorizon(QMainWindow):
    def create_title_bar(self, parent_layout):
        # Create title bar widget
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setObjectName("titleBar")
        
        # Title bar layout
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(5)
        
        # Add logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/logo.png")
        scaled_logo = logo_pixmap.scaled(24, 24,Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(scaled_logo)
        logo_label.setObjectName("logoLabel")
        
        # Title label
        title_label = QLabel("BlueHorizon")
        title_label.setObjectName("titleLabel")
        
        # Add components to title layout
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        
        # Add connect button
        connect_btn = QPushButton("Connect")
        connect_btn.setObjectName("connectBtn")
        connect_btn.setFixedSize(80, 20)
        connect_btn.setToolTip("Connect to MAVLink")
        connect_btn.clicked.connect(self.connect_mavlink)
        
        # Add some space between title and connect button
        title_layout.addSpacing(10)
        title_layout.addWidget(connect_btn)
        
        # Add stretch to push minimize/close buttons to the right
        title_layout.addStretch()
        
        # Create minimize button
        minimize_btn = QPushButton()
        minimize_btn.setObjectName("minimizeBtn")
        minimize_btn.setFixedSize(20, 20)
        minimize_btn.setText("—")
        minimize_btn.setToolTip("Minimize")
        minimize_btn.clicked.connect(self.showMinimized)
        
        # Create close button
        close_btn = QPushButton()
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(20, 20)
        close_btn.setText("✕")
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close)
        
        # Add buttons to title layout
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(close_btn)
        
        # Add title bar to parent layout
        parent_layout.addWidget(title_bar)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        title_bar.mouseDoubleClickEvent = self.title_bar_double_click

    def connect_mavlink(self):
        """Attempt to connect to MAVLink and show appropriate dialog"""
        # First show a connecting dialog (no button)
        self.connecting_dialog = FuturisticDialog(self, connecting=True, show_button=False)
        self.connecting_dialog.show()
        
        # Create and start connection thread
        self.connection_thread = ConnectionThread("tcp:127.0.0.1:5763", 10)
        self.connection_thread.connection_result.connect(self.handle_connection_result)
        self.connection_thread.start()
        
    def handle_connection_result(self, success, result):
        """Handle the result of the connection attempt"""
        # Close the connecting dialog
        self.connecting_dialog.close()
        
        if success:
            # If successful, result is the connection object
            self.mavlink_connection = result
            
            # Show success dialog (no button)
            dialog = FuturisticDialog(self, success=True, show_button=False)
            dialog.exec()
            
            self.monitoring_thread = MonitoringThread(self.mavlink_connection)
            
            self.monitoring_thread.data_updated.connect(self.telemetry.update_from_telemetry)
            self.monitoring_thread.data_updated.connect(self.hud.update_hud)
            self.messages.connect_to_mavlink(self.mavlink_connection)
            self.gauges.connect_monitoring_thread(self.monitoring_thread)
            self.monitoring_thread.data_updated.connect(self.map.update_from_telemetry)
            self.monitoring_thread.start()
        else:
            # If failed, result is the exception
            print(f"Connection failed: {result}")
            
            # Show failure dialog (no button)
            dialog = FuturisticDialog(self, success=False, show_button=False)
            dialog.exec()

    def update_waypoints(self, waypoints):
        """Update waypoints on the map when received from vehicle"""
        if waypoints:
            self.map.add_waypoints(waypoints)
            self.map.fit_waypoints()

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def title_bar_mouse_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def title_bar_double_click(self, event):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("BlueHorizon")
        self.resize(1200, 800)
        
        self.dragging = False
        self.mavlink_connection = None
        
        self.apply_cyberpunk_theme()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        root_layout = QVBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.create_title_bar(root_layout)
        content_widget = QWidget()
        
        main_layout = QHBoxLayout(content_widget)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.telemetry = TelemetryWidget()
        
        middle_column = QWidget()
        middle_layout = QVBoxLayout(middle_column)
        middle_layout.setSpacing(2)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        

        self.hud = EnhancedHUDWidget()
        self.hud.setStyleSheet("border-radius : 20px")
        self.messages = MessagesWidget()
        middle_layout.addWidget(self.hud)
        middle_layout.addWidget(self.messages)
        
        middle_layout.setStretch(0, 6)  # HUD
        middle_layout.setStretch(1, 7)  # Messages
        
        self.map = MapWidget()
        self.gauges = GaugesWidget()
        self.map.add_overlay(self.gauges)
        
        main_layout.addWidget(self.telemetry) 
        main_layout.addWidget(middle_column) 
        main_layout.addWidget(self.map)
        
        main_layout.setStretch(0, 1)  # Left column
        main_layout.setStretch(1, 2)  # Middle column
        main_layout.setStretch(2, 2)  # Right column (MAP)

        main_layout.setContentsMargins(2, 2, 2, 2)
        root_layout.addWidget(content_widget)
        self.apply_widget_styles()
    
    def apply_cyberpunk_theme(self):
        palette = QPalette()
        dark_blue_black = QColor(10, 12, 25)
        lighter_blue = QColor(30, 40, 80)
        accent_blue = QColor(0, 123, 255)
        neon_cyan = QColor(0, 255, 255)
        text_color = QColor(210, 230, 255)
        
        palette.setColor(QPalette.ColorRole.Window, dark_blue_black)
        palette.setColor(QPalette.ColorRole.WindowText, text_color)
        palette.setColor(QPalette.ColorRole.Base, QColor(15, 20, 30))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 25, 40))
        palette.setColor(QPalette.ColorRole.Button, lighter_blue)
        palette.setColor(QPalette.ColorRole.ButtonText, text_color)
        palette.setColor(QPalette.ColorRole.Link, neon_cyan)
        palette.setColor(QPalette.ColorRole.Highlight, accent_blue)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, text_color)
        
        QApplication.instance().setPalette(palette)
        
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                stop:0 #0a0c19, stop:1 #101832);
                color: #d2e6ff;
            }
            QFrame, QLabel {
                border: 0px solid #1e3060;
                border-radius: 3px;
                padding: 2px;
                background-color: rgba(15, 20, 35, 180);
            }
            QLabel {
                border: none;
                background-color: transparent;
            }
            QWidget#centralWidget {
                border: 0px solid #0078ff;
                border-radius: 5px;
            }
            QWidget#titleBar {
                background-color: rgba(10, 15, 30, 220);
                border-bottom: 0.5px solid #023670;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QLabel#titleLabel {
                font-weight: bold;
                font-size: 12px;
                color: #00aaff;
            }
            QPushButton#connectBtn {
                background-color: rgba(0, 123, 255, 180);
                border: 1px solid #0078ff;
                border-radius: 3px;
                font-weight: bold;
                color: #ffffff;
                font-size: 10px;
            }
            QPushButton#connectBtn:hover {
                background-color: #0078ff;
            }
            QPushButton#connectBtn:pressed {
                background-color: #0050aa;
            }
            QPushButton#minimizeBtn, QPushButton#closeBtn {
                background-color: rgba(30, 40, 80, 180);
                border: 1px solid #1e3060;
                border-radius: 3px;
                font-weight: bold;
                color: #d2e6ff;
            }
            QPushButton#minimizeBtn:hover {
                background-color: #1e3060;
            }
            QPushButton#closeBtn:hover {
                background-color: #aa0000;
            }
            QPushButton#minimizeBtn:pressed {
                background-color: #0078ff;
            }
            QPushButton#closeBtn:pressed {
                background-color: #ff0000;
            }
        """)
    
    def apply_widget_styles(self):
        self.centralWidget().setObjectName("centralWidget")
        self.telemetry.setObjectName("telemetryWidget")
        self.hud.setObjectName("hudWidget")
        self.messages.setObjectName("messagesWidget")
        self.map.setObjectName("mapWidget")
        
        widget_styles = """
            QWidget#telemetryWidget,
            QWidget#hudWidget, QWidget#messagesWidget,
            QWidget#onlineStatusWidget, QWidget#mapWidget {
                border: 0px solid #0078ff;
                border-radius: 3px;
                background-color: rgba(10, 12, 25, 200);
            }
            
            QWidget#hudWidget {
                border-color: #00aaff;
                background-color: rgba(10, 15, 30, 180);
            }
            QWidget#mapWidget {border-color: #00ffff;}
            QLabel {
                color: #d2e6ff;
                font-weight: bold;
            }
            QFrame#onlineStatusWidget {
                background-color: rgba(10, 20, 40, 180);
                border: 0px solid #0078ff;
                border-radius: 5px;
            }
        """
        self.setStyleSheet(self.styleSheet() + widget_styles)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)
    window = BlueHorizon()
    window.showMaximized()
    sys.exit(app.exec())
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QComboBox,
    QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt,QThread , pyqtSignal, QObject
from PyQt6.QtGui import QFont 
import traceback

class MAVLinkMessageListener(QThread):
    """Thread that listens for various important MAVLink messages"""
    new_status_text = pyqtSignal(int, str, datetime)
    new_mission_item_reached = pyqtSignal(int, datetime)
    new_system_status = pyqtSignal(str, datetime)
    new_gps_info = pyqtSignal(dict, datetime)
    
    def __init__(self, mavlink_connection):
        super().__init__()
        self._conn = mavlink_connection
        self._running = False
        
    def run(self):
        self._running = True
        message_types = [
            'STATUSTEXT', 
            'MISSION_ITEM_REACHED',
            'HEARTBEAT',   
            'COMMAND_ACK', 
            'GPS_RAW_INT',  
            'GLOBAL_POSITION_INT',
            'SYS_STATUS',     
            'PARAM_VALUE',    
        ]
        
        while self._running:
            try:
                try:
                    msg = self._conn.recv_match(type=message_types, blocking=True, timeout=0.5)
                except TypeError as e:
                    if "'NoneType' object does not support item assignment" in str(e):
                        self.msleep(10)
                        continue
                    else:
                        raise 
                
                if msg:
                    # Use get_type() instead of accessing .name attribute
                    msg_type = msg.get_type()
                    ts = datetime.now()
                    
                    # Process message based on its type
                    if msg_type == 'STATUSTEXT':
                        # Handle status text messages
                        sev = msg.severity
                        text = (
                            msg.text.decode('utf-8', errors='ignore')
                            if isinstance(msg.text, (bytes, bytearray)) else msg.text
                        )
                        text = text.strip('\0')
                        # print(f"[STATUSTEXT] ({sev}) {text}")
                        self.new_status_text.emit(sev, text, ts)
                        
                    elif msg_type == 'MISSION_ITEM_REACHED':
                        # Handle waypoint reached notifications
                        seq = msg.seq
                        # print(f"[WAYPOINT] Reached waypoint #{seq}")
                        self.new_mission_item_reached.emit(seq, ts)
                        
                    elif msg_type == 'HEARTBEAT':
                        # Extract system status (armed/disarmed)
                        if hasattr(msg, 'base_mode'):
                            armed = bool(msg.base_mode & 0x80)  # Check if armed bit is set
                            status = "ARMED" if armed else "DISARMED"
                            # print(f"[SYSTEM] Status: {status}")
                            self.new_system_status.emit(status, ts)
                    
                    elif msg_type == 'GPS_RAW_INT' or msg_type == 'GLOBAL_POSITION_INT':
                        try:
                            gps_data = {}
                            
                            if msg_type == 'GPS_RAW_INT':
                                safe_attrs = ['time_usec', 'fix_type', 'lat', 'lon', 'alt', 
                                             'eph', 'epv', 'vel', 'cog', 'satellites_visible']
                            elif msg_type == 'GLOBAL_POSITION_INT':
                                safe_attrs = ['time_boot_ms', 'lat', 'lon', 'alt', 'relative_alt',
                                             'vx', 'vy', 'vz', 'hdg']
                            
                            for attr in safe_attrs:
                                if hasattr(msg, attr):
                                    gps_data[attr] = getattr(msg, attr)
                            
                            # Add the message type for reference
                            gps_data['msg_type'] = msg_type
                                        
                            # print(f"[GPS] Type: {msg_type}, Fix: {gps_data.get('fix_type', 'N/A')}")
                            self.new_gps_info.emit(gps_data, ts)
                        except Exception as gps_error:
                            # print(f"[ERROR] Exception processing GPS data: {gps_error}")
                            traceback.print_exc()
                        
                    # Handle other message types as needed
                    # print(f"[RECEIVED] Message type: {msg_type}")
                    
            except Exception as e:
                traceback.print_exc()
                self.msleep(10)
    
    def stop(self):
        """Stop the listener thread."""
        self._running = False
        self.wait()

class MessagesWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("MessagesWidget")
        self.setStyleSheet("""
            #MessagesWidget {
                background-color: rgba(10, 15, 30, 80);
                border-radius: 20px;
                border: 1px solid rgba(0, 204, 255, 30);
            }
        """)
        self.setup_ui()
        self._messages = []
        
        # Define severities for different message types
        self.SEVERITY = {
            0: ("EMERGENCY", "#ff0000"),  # Red
            1: ("ALERT", "#ff5500"),      # Orange-red
            2: ("CRITICAL", "#ff8800"),   # Orange
            3: ("ERROR", "#ffbb00"),      # Yellow-orange
            4: ("WARNING", "#ffff00"),    # Yellow
            5: ("NOTICE", "#88ff00"),     # Green-yellow
            6: ("INFO", "#00ff88"),       # Green
            7: ("DEBUG", "#00ffff"),      # Cyan
            # Custom severity levels for different message types
            100: ("WAYPOINT", "#88aaff"), # Light blue
            101: ("SYSTEM", "#ff88ff"),   # Pink
            102: ("GPS", "#aaaaff"),      # Light purple
            103: ("POSITION", "#ccccff"), # Very light purple
        }
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header_layout = QHBoxLayout()

        title_label = QLabel("Messages")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Add a clear button to clear message history
        clear_button = QPushButton("Clear")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 60, 120, 150);
                color: white;
                border-radius: 4px;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 100, 200, 150);
            }
            QPushButton:pressed {
                background-color: rgba(0, 80, 160, 150);
            }
        """)
        # clear_button.clicked.connect(self.clear_messages)
        # header_layout.addWidget(clear_button)
        
        main_layout.addLayout(header_layout)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 10, 20, 120);
                border: 1px solid rgba(0, 204, 255, 30);
                border-radius: 20px;
                color: white;
            }
        """)
        main_layout.addWidget(self.list_widget, stretch=1)

    def connect_to_mavlink(self, mavlink_connection):
        """Connect this widget to a MAVLink connection - creates the listener thread"""
        try:
            # Create and start the MAVLink message listener thread
            self.mavlink_listener = MAVLinkMessageListener(mavlink_connection)
            
            # Connect to all the signals from the MAVLinkMessageListener
            self.mavlink_listener.new_status_text.connect(self.handle_status_text)
            self.mavlink_listener.new_mission_item_reached.connect(self.handle_waypoint)
            self.mavlink_listener.new_system_status.connect(self.handle_system_status)
            self.mavlink_listener.new_gps_info.connect(self.handle_gps_info)
            
            # Start the listener thread
            self.mavlink_listener.start()
            
            self.add_message(6, "MAVLink message listener connected successfully")
        except Exception as e:
            self.add_message(3, f"Failed to connect MAVLink listener: {e}")

    def handle_status_text(self, severity, text, timestamp):
        """Handle regular STATUSTEXT messages"""
        self.add_message(severity, text, timestamp)
    
    def handle_waypoint(self, seq, timestamp):
        """Handle waypoint reached notifications"""
        self.add_message(100, f"Waypoint #{seq} reached", timestamp)
    
    def handle_system_status(self, status, timestamp):
        """Handle system status changes (armed/disarmed)"""
        pass
        # self.add_message(101, f"System status: {status}", timestamp)
    
    def handle_gps_info(self, gps_data, timestamp):
        """Handle GPS information updates"""
        # Extract important GPS data - modify this to show what's important for your application
        if 'fix_type' in gps_data:
            fix_type = gps_data['fix_type']
            fix_desc = {
                0: "No GPS",
                1: "No Fix",
                2: "2D Fix",
                3: "3D Fix",
                4: "DGPS",
                5: "RTK Float",
                6: "RTK Fixed",
            }.get(fix_type, f"Unknown ({fix_type})")
            
            # self.add_message(102, f"GPS Fix: {fix_desc}", timestamp)
        
        # Add position data if available
        if all(k in gps_data for k in ['lat', 'lon', 'alt']):
            lat = gps_data['lat'] / 1e7  # Convert from int32 to degrees
            lon = gps_data['lon'] / 1e7
            alt = gps_data['alt'] / 1000  # Convert from mm to meters
            # self.add_message(103, f"Position: Lat: {lat:.6f}° Lon: {lon:.6f}° Alt: {alt:.1f}m", timestamp)

    def add_message(self, severity, text, timestamp=None):
        """Add a new message to the list"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self._messages.append((severity, text, timestamp))
        self._add_item_widget(severity, text, timestamp)

    def _add_item_widget(self, severity, text, timestamp):
        """Create and add a styled widget for the message"""
        label, color = self.SEVERITY.get(severity, ("UNKNOWN", "#ffffff"))
        ts_str = timestamp.strftime("%H:%M:%S")

        html = (f'<span style="color:#ffffff">[{ts_str}] </span>'
            f'<span style="color:{color}">[{label}]</span> '
            f'<span style="color:#ffffff">{text}</span>')
        item = QListWidgetItem()
        widget = QLabel(html)
        widget.setTextFormat(Qt.TextFormat.RichText)
        widget.setStyleSheet("background: transparent;")
        widget.setFont(QFont("Consolas", 10))
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        self.list_widget.scrollToBottom()
        
    # def clear_messages(self):
    #     """Clear all messages in the list"""
    #     self._messages.clear()
    #     self.list_widget.clear()
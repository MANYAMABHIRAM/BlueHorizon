from PyQt6.QtWidgets import QLabel, QFrame, QHBoxLayout, QProgressBar, QVBoxLayout, QWidget , QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class FuturisticProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(8)  # Make bars smaller
        self.setMaximumWidth(150)
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar {
                border-radius: 3px;
                background-color: rgba(0,105,146,0.25);
                margin-right: 10px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                              stop:0 #00ccff, stop:0.5 #00aaff, stop:1 #0066ff);
                border-radius: 3px;
            }
        """)

class DataItem(QFrame):
    def __init__(self, label_text, unit="", has_progress=True, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 20, 35, 100);
                border-radius: 10px;
                border: 1px solid rgba(0, 204, 255, 40);
            }
        
        """)
        
        layout = QHBoxLayout(self) 
        layout.setContentsMargins(10, 2, 10, 2)
        
        # Label
        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: #7af7ff; background: transparent; border: none;")
        self.label.setFixedWidth(80)
        
        # Value
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setStyleSheet("color: #ffffff; background: transparent; border: none; font-size: 14px; font-weight: bold;")
        
        layout.addWidget(self.label)
        
        # Progress Bar (only for items that need it)
        if has_progress:
            self.progress_bar = FuturisticProgressBar()
            layout.addWidget(self.progress_bar, 1)
            self.value_label.setFixedWidth(50)
        else:
            # For non-progress items, make value label larger
            self.value_label.setFixedWidth(120)
            layout.addStretch(1)
        
        layout.addWidget(self.value_label)
        
        # Unit
        if unit:
            self.unit_label = QLabel(unit)
            self.unit_label.setStyleSheet("color: #7af7ff; background: transparent; border: none;")
            self.unit_label.setFixedWidth(30)
            self.unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(self.unit_label)
    
    def update_value(self, value, max_value=100):
        # Format float values to show one decimal place
        if isinstance(value, float):
            self.value_label.setText(f"{value:.1f}")
        else:
            # String values need to be displayed directly (like "0/10" for waypoints)
            self.value_label.setText(f"{value}")
            
        # Handle progress bar updates if it exists
        if hasattr(self, 'progress_bar'):
            # For waypoint format like "0/10", don't try to update progress bar
            if isinstance(value, str) and '/' in value:
                try:
                    current, total = value.split('/')
                    if current.isdigit() and total.isdigit():
                        current_int = int(current)
                        total_int = int(total)
                        if total_int > 0:  # Avoid division by zero
                            self.progress_bar.setMaximum(total_int)
                            self.progress_bar.setValue(current_int)
                except:
                    pass  # If parsing fails, don't update progress bar
            # QProgressBar accepts only integers, so convert floats
            elif isinstance(value, float):
                # Scale float values to integers (multiply by 10)
                int_value = int(value * 10)
                int_max = int(max_value * 10)
                self.progress_bar.setMaximum(int_max)
                self.progress_bar.setValue(int_value)
            else:
                self.progress_bar.setMaximum(max_value)
                self.progress_bar.setValue(value)

class TelemetryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TelemetryWidget")
        self.setStyleSheet("""
            #TelemetryWidget {
                background-color: rgba(10, 15, 30, 80);
                border-radius: 8px;
                border: 1px solid rgba(0, 204, 255, 30);
            }
        """)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 10, 5)
        self.main_layout.setSpacing(12)
        
        # Add header label for telemetry section
        self.telemetry_header = QLabel("TELEMETRY")
        self.telemetry_header.setStyleSheet("color: #00ccff; font-weight: bold; background: transparent; border: none;")
        self.telemetry_header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addWidget(self.telemetry_header)
        
        # Add all telemetry items
        self.altitude = DataItem("Altitude", "m")
        self.speed = DataItem("Speed", "m/s")
        self.heading = DataItem("Heading", "°")
        self.battery = DataItem("Battery", "%")
        self.airspeed = DataItem("AirSpeed", "m/s")
        self.distance = DataItem("Distance", "m")
        self.roll = DataItem("Roll", "°")
        self.pitch = DataItem("Pitch", "°")
        self.yaw = DataItem("Yaw", "°")
        
        # Add telemetry items to layout
        self.main_layout.addWidget(self.altitude)
        self.main_layout.addWidget(self.speed)
        self.main_layout.addWidget(self.heading)
        self.main_layout.addWidget(self.battery)
        self.main_layout.addWidget(self.airspeed)
        self.main_layout.addWidget(self.distance)
        self.main_layout.addWidget(self.roll)
        self.main_layout.addWidget(self.pitch)
        self.main_layout.addWidget(self.yaw)
        
        # Add separator between telemetry and controls
        # self.separator = QFrame()
        # self.separator.setFrameShape(QFrame.Shape.HLine)
        # self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        # self.separator.setStyleSheet("background-color: rgba(0, 204, 255, 50); border: none; max-height: 1px; margin: 10px 0px;")
        # self.main_layout.addWidget(self.separator)
        
        # Add header label for controls section 
        self.controls_header = QLabel("FLIGHT CONTROLS")
        self.controls_header.setStyleSheet("color: #00ccff; font-weight: bold; background: transparent; border: none;")
        self.controls_header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addWidget(self.controls_header)
        
        # Add all control items
        self.flying_type = DataItem("Flying Type", "", has_progress=False)
        self.flight_mode = DataItem("Flight Mode", "", has_progress=False)
        self.waypoint = DataItem("Waypoint", "", has_progress=False)
        self.throttle = DataItem("Throttle", "%", has_progress=True)
        self.climbrate = DataItem("Climbrate", "m/s", has_progress=True)
        
        # Add control items to layout
        self.main_layout.addWidget(self.flying_type)
        self.main_layout.addWidget(self.flight_mode)
        self.main_layout.addWidget(self.waypoint)
        self.main_layout.addWidget(self.throttle)
        self.main_layout.addWidget(self.climbrate)
        
        # Add some stretching at the bottom
        self.main_layout.addStretch(1)
        self.home_position = None
        self.calculate_distance_flag = False   
        
        # Set initial values (for demonstration)
        # self.update_demo_values()
    
    def set_home_position(self, lat, lon):
        self.home_position = {'lat': lat, 'lon': lon}
        self.calculate_distance_flag = True
        print(f"Home position set to: {lat}, {lon}")
    
    def update_from_telemetry(self, data):
        """Update telemetry values from actual MAVLink data"""
        # Update telemetry values from the data dict
        if 'alt' in data:  # Changed from 'relative_alt' to 'alt'
            self.altitude.update_value(data['alt'], 10000)
        
        if 'groundspeed' in data:
            # Keep as m/s
            self.speed.update_value(data['groundspeed'], 100)
        
        if 'heading' in data:
            self.heading.update_value(data['heading'], 360)
        
        if 'battery' in data:
            self.battery.update_value(data['battery'], 100)
        
        if 'airspeed' in data:
            # Keep as m/s
            self.airspeed.update_value(data['airspeed'], 100)
        
        if 'distance' in data:
            self.distance.update_value(data['distance'], 10000)
        
        if 'roll' in data:
            self.roll.update_value(data['roll'], 30)
        
        if 'pitch' in data:
            self.pitch.update_value(data['pitch'], 30)
        
        if 'yaw' in data:
            self.yaw.update_value(data['yaw'], 360)
        
        if 'climb' in data:
            self.climbrate.update_value(data['climb'], 10)
        
        # Update flight mode if available
        if 'mode' in data:
            self.flight_mode.update_value(data['mode'])
        
        if 'flying_type' in data:
            self.flying_type.update_value(data['flying_type'])
            
        if 'waypoint' in data:
            current_wp = data['waypoint']
            total_wp = data.get('total_waypoints', 0)
            self.update_waypoint(current_wp, total_wp)
            
        if 'throttle' in data:
            self.throttle.update_value(data['throttle'], 100)
    
    # For the create_section_header method:
    def create_section_header(self, text, color_scheme="blue"):
        """Create styled section header with futuristic design"""
        header_frame = QFrame()
        header_frame.setMaximumHeight(30)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 0, 5, 0)
        
        # Color for icons based on section
        color = "#00ccff" if color_scheme == "blue" else "#00ff99"
        
        # Decorative left element
        left_decor = QLabel("◢")
        left_decor.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent; border: none;")
        
        # Header text
        header_label = QLabel(text)
        header_label.setStyleSheet(f"""
            color: {color}; 
            font-weight: bold; 
            background: transparent; 
            border: none; 
            font-size: 13px;
            letter-spacing: 2px;
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Decorative right element
        right_decor = QLabel("◣")
        right_decor.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent; border: none;")
        
        # Add to layout
        header_layout.addWidget(left_decor)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(right_decor)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        
        # Fix the QColor creation
        if color_scheme == "blue":
            shadow.setColor(QColor(0, 204, 255, 120))
        else:  # purple
            shadow.setColor(QColor(128, 0, 128, 120))
            
        shadow.setOffset(0, 0)
        header_label.setGraphicsEffect(shadow)
        
        self.main_layout.addWidget(header_frame)
    
    def create_separator(self):
        """Create a simple separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setMaximumHeight(1)
        separator.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 rgba(0, 204, 255, 10), 
                                      stop:0.5 rgba(0, 204, 255, 80), 
                                      stop:1 rgba(0, 204, 255, 10));
            border: none;
            margin: 5px 10px;
        """)
        
        self.main_layout.addWidget(separator)
    
    def get_waypoint_current(self):
        """Extract current waypoint number from display"""
        try:
            current = self.waypoint.value_label.text().split('/')[0]
            return int(current) if current.isdigit() else 0
        except:
            return 0
    
    # Methods for direct value updates (can be called externally)
    def update_flying_type(self, value):
        self.flying_type.update_value(value)
    
    def update_flight_mode(self, value):
        self.flight_mode.update_value(value)
    def update_waypoint(self, current, total):
        # Ensure both values are integers and format as string
        current_str = str(int(current)) if isinstance(current, (int, float)) else current
        total_str = str(int(total)) if isinstance(total, (int, float)) else total 
        self.waypoint.update_value(f"{current_str}")
    
    def update_throttle(self, value, max_value=100):
        self.throttle.update_value(value, max_value)
    
    def update_climbrate(self, value, max_value=10):
        self.climbrate.update_value(value, max_value)
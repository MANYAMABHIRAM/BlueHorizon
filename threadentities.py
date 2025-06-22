import math
from PyQt6.QtCore import QThread, pyqtSignal

import time
import math
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from pymavlink import mavutil

class MonitoringThread(QThread):
    data_updated = pyqtSignal(dict)
    status_text_received = pyqtSignal(int, str)
    waypoints_updated = pyqtSignal(list)
    connection_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, mavlink_connection):
        super().__init__()
        self.mavlink_connection = mavlink_connection
        self.running = False
        self.waypoints = []
        self.home_lat = None
        self.home_lon = None
        self.home_alt = None
        self.current_waypoint = 0
        self.total_waypoints = 0
        self.home_emitted = False
        self.messages_widget = None
        self.connection_healthy = True
        self.reconnect_attempts = 0
        self.last_heartbeat_time = time.time()
        
    def connect_mavlink_messages(self, messages_widget):
        self.messages_widget = messages_widget
    
    def run(self):
        self.running = True
        self.connection_status_changed.emit(True, "Connected")
        self.request_waypoints()
        self.request_home_position()
        
        while self.running:
            try:
                if time.time() - self.last_heartbeat_time > 5:
                    if self.connection_healthy:
                        self.connection_healthy = False
                        self.connection_status_changed.emit(False, "Connection lost - waiting for heartbeat")
                        if self.messages_widget:
                            self.messages_widget.add_message(3, "Connection lost - waiting for heartbeat")
                msg = self.mavlink_connection.recv_match(blocking=True, timeout=0.5)
                
                if msg:
                    msg_type = msg.get_type()
                    if msg_type == 'HEARTBEAT':
                        self.last_heartbeat_time = time.time()
                        if not self.connection_healthy:
                            self.connection_healthy = True
                            self.connection_status_changed.emit(True, "Connection restored")
                            if self.messages_widget:
                                self.messages_widget.add_message(7, "Connection restored")
                    self.process_message(msg, msg_type)
                    
            except ConnectionError as e:
                self.handle_connection_error(str(e))
            except TimeoutError:
                pass
            except Exception as e:
                if self.messages_widget:
                    self.messages_widget.add_message(3, f"Error in monitoring thread: {str(e)}")
                self.msleep(100)
    
    def process_message(self, msg, msg_type):
        """Process a MAVLink message based on its type"""
        data = {}
        
        if msg_type == 'STATUSTEXT':
            self.process_statustext(msg)
            
        elif msg_type == 'GPS_RAW_INT':
            data['lat'], data['lon'], data['alt'] = msg.lat / 1e7, msg.lon / 1e7, msg.alt / 1000.0
            
        elif msg_type == 'GLOBAL_POSITION_INT':
            data['lat'], data['lon'], data['alt'], data['relative_alt'] = msg.lat / 1e7, msg.lon / 1e7, msg.alt / 1000.0, msg.relative_alt / 1000.0
            
        elif msg_type == 'ATTITUDE':
            data['roll'], data['pitch'], data['yaw'] = math.degrees(msg.roll), math.degrees(msg.pitch), math.degrees(msg.yaw) 
            
        elif msg_type == 'VFR_HUD':
            data['heading'], data['alt'], data['groundspeed'], data['airspeed'], data['climb'], data['throttle'] = msg.heading, msg.alt, msg.groundspeed, msg.airspeed, msg.climb, msg.throttle
            
        elif msg_type == 'SYS_STATUS':
            self.process_sys_status(msg, data)
        
        elif msg_type == 'HEARTBEAT':
            self.process_heartbeat(msg, data)
            
        elif msg_type == 'MISSION_CURRENT':
            data['waypoint'] = msg.seq
            self.current_waypoint = msg.seq
            # Always include the total waypoints when we send current waypoint
            data['total_waypoints'] = self.total_waypoints
            
        elif msg_type == 'MISSION_COUNT':
            data['total_waypoints'] = msg.count
            self.total_waypoints = msg.count
            # Also include the current waypoint when we send total waypoints
            data['waypoint'] = self.current_waypoint
            if msg.count > 0:
                self.request_waypoint_details()
        elif msg_type in ['MISSION_ITEM', 'MISSION_ITEM_INT']:
            seq = msg.seq
            lat = msg.x if msg_type == 'MISSION_ITEM' else msg.x / 1e7
            lng = msg.y if msg_type == 'MISSION_ITEM' else msg.y / 1e7
            alt = msg.z
            self.process_waypoint(seq, lat, lng, alt)
        elif msg_type == 'HOME_POSITION':
            self.process_home_position(msg, data)
        self.check_and_add_home_position(data)
        self.calculate_distance_from_home(data)
        if data:
            self.data_updated.emit(data)
        if 'waypoint' in data and 'total_waypoints' not in data:
            data['total_waypoints'] = self.total_waypoints
        elif 'total_waypoints' in data and 'waypoint' not in data:
            data['waypoint'] = self.current_waypoint
    
    def process_statustext(self, msg):
        """Process a STATUSTEXT message"""
        severity = msg.severity
        text = msg.text
        if isinstance(text, bytes):
            text = text.decode('utf-8', 'ignore')
        text = text.strip('\0')
        if self.messages_widget:
            self.messages_widget.add_message(severity, text)
    
    def process_sys_status(self, msg, data):
        """Process a SYS_STATUS message"""
        if hasattr(msg, 'battery_remaining'):
            data['battery'] = msg.battery_remaining  
        elif hasattr(msg, 'voltage_battery'):
            voltage = msg.voltage_battery / 1000.0 
            cell_count = 3 
            min_voltage = 3.2 * cell_count
            max_voltage = 4.2 * cell_count
            if voltage > min_voltage:
                battery_pct = ((voltage - min_voltage) / (max_voltage - min_voltage)) * 100
                data['battery'] = min(100, max(0, battery_pct)) 
            else:
                data['battery'] = 0
    
    def process_heartbeat(self, msg, data):
        """Process a HEARTBEAT message"""
        if hasattr(msg, 'custom_mode'):
            mode_mapping = {0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO", 4: "GUIDED", 5: "LOITER", 6: "RTL", 7: "CIRCLE", 8: "POSITION", 9: "LAND", 10: "OF_LOITER",
                        11: "DRIFT", 12: "SPORT", 13: "FLIP", 14: "AUTOTUNE", 15: "POSHOLD", 16: "BRAKE", 17: "THROW", 18: "AVOID_ADSB", 19: "GUIDED_NOGPS",
                        20: "SMART_RTL", 21: "FLOWHOLD", 22: "FOLLOW", 23: "ZIGZAG", 24: "SYSTEMID", 25: "AUTOROTATE", 26: "AUTO_RTL"}
            mode = mode_mapping.get(msg.custom_mode, f"UNKNOWN_{msg.custom_mode}")
            data['mode'] = mode
            
            if mode in ["AUTO", "GUIDED", "RTL", "SMART_RTL", "AUTO_RTL"]:
                data['flying_type'] = "Auto"
            elif mode in ["LOITER", "CIRCLE", "POSHOLD"]:
                data['flying_type'] = "Assisted"
            elif mode == "RTL":
                data['flying_type'] = "Return"
            else:
                data['flying_type'] = "Manual"
    
    def process_home_position(self, msg, data):
        """Process a HOME_POSITION message"""
        self.home_lat = msg.latitude / 1e7
        self.home_lon = msg.longitude / 1e7
        self.home_alt = msg.altitude / 1000.0
        data['home_lat'] = self.home_lat
        data['home_lon'] = self.home_lon
        data['home_alt'] = self.home_alt
        self.home_emitted = True
    
    def check_and_add_home_position(self, data):
        """Check if we need to add home position to the data"""
        if ('lat' in data and 'lon' in data and 
            self.home_lat is not None and self.home_lon is not None and not self.home_emitted):
            data['home_lat'] = self.home_lat
            data['home_lon'] = self.home_lon
            data['home_alt'] = self.home_alt
            self.home_emitted = True
    
    def calculate_distance_from_home(self, data):
        """Calculate distance from home if we have position data"""
        if ('lat' in data and 'lon' in data and 
            self.home_lat is not None and self.home_lon is not None):
            try:
                R = 6371000 
                lat1 = math.radians(self.home_lat)
                lon1 = math.radians(self.home_lon)
                lat2 = math.radians(data['lat'])
                lon2 = math.radians(data['lon'])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance = R * c
                data['distance'] = distance
            except Exception as e:
                print(f"Error calculating distance: {e}")
    
    def request_home_position(self):
        try:
            self.mavlink_connection.mav.command_long_send(
                self.mavlink_connection.target_system,
                self.mavlink_connection.target_component,
                512, 
                0,   
                242, 
                0, 0, 0, 0, 0, 0
            )
        except Exception as e:
            print(f"Error requesting home position: {e}")
            if self.messages_widget:
                self.messages_widget.add_message(3, f"Error requesting home position: {str(e)}")
        
    def request_waypoints(self):
        try:
            self.mavlink_connection.mav.mission_request_list_send(
                self.mavlink_connection.target_system,
                self.mavlink_connection.target_component
            )
        except Exception as e:
            print(f"Error requesting waypoints: {e}")
            if self.messages_widget:
                self.messages_widget.add_message(3, f"Error requesting waypoints: {str(e)}")
    
    def request_waypoint_details(self):
        for i in range(self.total_waypoints):
            try:
                self.mavlink_connection.mav.mission_request_send(
                    self.mavlink_connection.target_system,
                    self.mavlink_connection.target_component,
                    i
                )
                self.msleep(50)
            except Exception as e:
                print(f"Error requesting waypoint {i}: {e}")
                if self.messages_widget:
                    self.messages_widget.add_message(3, f"Error requesting waypoint {i}: {str(e)}")
    
    def process_waypoint(self, seq, lat, lng, alt):
        while len(self.waypoints) <= seq:
            self.waypoints.append(None)
        
        self.waypoints[seq] = {
            'lat': lat,
            'lng': lng,
            'alt': alt
        }
        
        if None not in self.waypoints and len(self.waypoints) == self.total_waypoints:
            self.waypoints_updated.emit(self.waypoints)
    
    def handle_connection_error(self, error_message):
        if self.connection_healthy:
            self.connection_healthy = False
            self.connection_status_changed.emit(False, f"Connection error: {error_message}")
            if self.messages_widget:
                self.messages_widget.add_message(3, f"Connection error: {error_message}")
        self.reconnect_attempts += 1
        if self.reconnect_attempts > 3:
            self.msleep(2000)
        else:
            self.msleep(500)
    
    def attempt_reconnect(self):
        try:
            if hasattr(self.mavlink_connection, 'close'):
                self.mavlink_connection.close()
            connection_string = self.mavlink_connection.address
            self.mavlink_connection = mavutil.mavlink_connection(connection_string)
            self.last_heartbeat_time = time.time()
            self.connection_healthy = True
            self.reconnect_attempts = 0
            if self.messages_widget:
                self.messages_widget.add_message(6, f"Attempting to reconnect to {connection_string}")
            self.request_waypoints()
            self.request_home_position()
            return True
        except Exception as e:
            if self.messages_widget:
                self.messages_widget.add_message(3, f"Reconnection failed: {str(e)}")
            print(f"Reconnection failed: {e}")
            return False
    
    def stop(self):
        self.running = False
        self.wait()

class ConnectionThread(QThread):
    connection_result = pyqtSignal(bool, object)
    
    def __init__(self, connection_string, timeout):
        super().__init__()
        self.connection_string = connection_string
        self.timeout = timeout
        
    def run(self):
        try:
            connection = mavutil.mavlink_connection(self.connection_string, timeout=self.timeout)
            self.connection_result.emit(True, connection)
        except Exception as e:
            self.connection_result.emit(False, e)
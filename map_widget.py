# from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QStackedLayout, QWidget
# from PyQt6.QtCore import Qt, QUrl, pyqtSlot
# from PyQt6.QtWebEngineWidgets import QWebEngineView
# from PyQt6.QtWebEngineCore import QWebEngineSettings


# class MapWidget(QFrame):
#     def __init__(self):
#         super().__init__()
#         self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
#         self.waypoints = []
#         self.current_waypoint_index = 0
#         self.covered_path_points = []
#         self.setup_ui()
        
#     def setup_ui(self):
#         # Main layout
#         self.layout = QVBoxLayout(self)
#         self.layout.setContentsMargins(0, 0, 0, 0)
        
#         # Container widget to hold map and overlays
#         self.container = QWidget()
#         self.container_layout = QVBoxLayout(self.container)
#         self.container_layout.setContentsMargins(0, 0, 0, 0)
        
#         # Create web view for the map
#         self.web_view = QWebEngineView()
#         self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
#         self.container_layout.addWidget(self.web_view)
        
#         # Add container to main layout
#         self.layout.addWidget(self.container)
        
#         # Load the Leaflet map
#         self.load_map()
        
#     def load_map(self, center_lat=51.505, center_lng=-0.09, zoom=13):
#         html = """
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="utf-8" />
#             <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
#             <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
#             <style>
#                 body { margin: 0; padding: 0; }
#                 #map { position: absolute; top: 0; bottom: 0; width: 100%; height: 100%; border-radius: 6px; background-color: #0f1525; }
                
#                 /* Custom styling for controls */
#                 .leaflet-control-attribution {
#                     background-color: rgba(10, 15, 30, 0.8);
#                     color: #00aaff;
#                     border-radius: 4px;
#                     padding: 4px 8px;
#                     font-weight: bold;
#                 }
                
#                 .leaflet-control-zoom a {
#                     background-color: rgba(20, 35, 75, 0.8);
#                     color: #00ccff;
#                     border: 1px solid rgba(0, 150, 255, 0.6);
#                 }
                
#                 .leaflet-control-zoom a:hover {
#                     background-color: rgba(30, 45, 95, 0.9);
#                 }
                
#                 /* Make the grid lines more futuristic */
#                 .grid-lines {
#                     stroke: rgba(0, 170, 255, 0.3);
#                     stroke-width: 1px;
#                     stroke-dasharray: 5, 5;
#                 }
                
#                 /* Custom marker style */
#                 .drone-marker {
#                     filter: drop-shadow(0 0 6px rgba(0, 255, 255, 0.8));
#                 }
                
#                 /* Custom waypoint marker style */
#                 .waypoint-marker {
#                     filter: drop-shadow(0 0 4px rgba(255, 165, 0, 0.8));
#                 }
                
#                 /* Active waypoint marker style */
#                 .active-waypoint-marker {
#                     filter: drop-shadow(0 0 8px rgba(255, 0, 0, 0.9));
#                 }
                
#                 @keyframes pulse {
#                     0% { transform: scale(0.8); opacity: 1; }
#                     70% { transform: scale(1.5); opacity: 0.3; }
#                     100% { transform: scale(0.8); opacity: 1; }
#                 }
#             </style>
#         </head>
#         <body>
#             <div id="map"></div>
#             <script>
#                 const map = L.map('map', {
#                     zoomControl: true,
#                     dragging: true,
#                     scrollWheelZoom: true,
#                     attributionControl: false
#                 }).setView([16.2729081, 80.4367779], 16);

#                 // More stylish map with slightly darkened tiles
#                 L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
#                     maxZoom: 19,
#                     opacity: 0.85
#                 }).addTo(map);
                
#                 // Add drone marker with pulsating effect
#                 const droneIcon = L.divIcon({
#                     html: `<div style="display:flex;justify-content:center;align-items:center;width:40px;height:40px;">
#                             <div style="width:20px;height:20px;background-color:rgba(0,255,255,0.8);border-radius:50%;
#                                         box-shadow:0 0 15px rgba(0,255,255,0.8);animation:pulse 2s infinite;">
#                             </div>
#                         </div>`,
#                     className: 'drone-marker',
#                     iconSize: [40, 40],
#                     iconAnchor: [20, 20]
#                 });
                
#                 const droneMarker = L.marker([16.2729081, 80.4367779], {icon: droneIcon}).addTo(map);
                
#                 // Create waypoint icon
#                 const waypointIcon = L.divIcon({
#                     html: `<div style="display:flex;justify-content:center;align-items:center;width:30px;height:30px;">
#                             <div style="width:12px;height:12px;background-color:rgba(255,165,0,0.8);border-radius:50%;
#                                         box-shadow:0 0 10px rgba(255,165,0,0.8);">
#                             </div>
#                         </div>`,
#                     className: 'waypoint-marker',
#                     iconSize: [30, 30],
#                     iconAnchor: [15, 15]
#                 });
                
#                 // Create active waypoint icon
#                 const activeWaypointIcon = L.divIcon({
#                     html: `<div style="display:flex;justify-content:center;align-items:center;width:36px;height:36px;">
#                             <div style="width:16px;height:16px;background-color:rgba(255,0,0,0.8);border-radius:50%;
#                                         box-shadow:0 0 15px rgba(255,0,0,0.8);animation:pulse 1.5s infinite;">
#                             </div>
#                         </div>`,
#                     className: 'active-waypoint-marker',
#                     iconSize: [36, 36],
#                     iconAnchor: [18, 18]
#                 });
                
#                 // Initialize path variables
#                 const coveredPath = L.polyline([], {
#                     color: 'rgba(0, 255, 255, 0.7)', 
#                     weight: 3,
#                     dashArray: '5, 7'
#                 }).addTo(map);
                
#                 const plannedPath = L.polyline([], {
#                     color: 'rgba(255, 165, 0, 0.7)', 
#                     weight: 3
#                 }).addTo(map);
                
#                 // Store waypoints for later use
#                 const waypoints = [];
#                 const waypointMarkers = [];
#                 let currentWaypointIndex = 0;
                
#                 // Function to update the drone position
#                 window.updateDronePosition = function(lat, lng) {
#                     droneMarker.setLatLng([lat, lng]);
                    
#                     // Add point to covered path
#                     const path = coveredPath.getLatLngs();
#                     path.push([lat, lng]);
#                     coveredPath.setLatLngs(path);
                    
#                     // Center map on drone with smooth animation
#                     map.panTo([lat, lng], {
#                         animate: true,
#                         duration: 1.0,
#                         easeLinearity: 0.5
#                     });
#                 }
                
#                 // Function to add waypoints to the map
#                 window.addWaypoints = function(waypointsArray) {
#                     // Clear existing waypoints
#                     waypointMarkers.forEach(marker => map.removeLayer(marker));
#                     waypointMarkers.length = 0;
#                     waypoints.length = 0;
                    
#                     // Add new waypoints
#                     waypointsArray.forEach((wp, index) => {
#                         const waypointPos = [wp.lat, wp.lng];
#                         waypoints.push(waypointPos);
                        
#                         // Create marker with appropriate icon
#                         const isActive = index === currentWaypointIndex;
#                         const icon = isActive ? activeWaypointIcon : waypointIcon;
#                         const marker = L.marker(waypointPos, {icon: icon})
#                             .addTo(map)
#                             .bindPopup(`Waypoint ${index + 1}`);
                        
#                         waypointMarkers.push(marker);
#                     });
                    
#                     // Update planned path
#                     if (waypoints.length > 0) {
#                         plannedPath.setLatLngs(waypoints);
#                     }
#                 }
                
#                 // Function to set current waypoint
#                 window.setCurrentWaypoint = function(index) {
#                     // Update current waypoint index
#                     currentWaypointIndex = index;
                    
#                     // Update markers
#                     waypointMarkers.forEach((marker, idx) => {
#                         map.removeLayer(marker);
#                         const icon = idx === currentWaypointIndex ? activeWaypointIcon : waypointIcon;
#                         waypointMarkers[idx] = L.marker(waypoints[idx], {icon: icon})
#                             .addTo(map)
#                             .bindPopup(`Waypoint ${idx + 1}`);
#                     });
#                 }
                
#                 // Function to zoom in/out
#                 window.zoomIn = function() {
#                     map.zoomIn(1, {animate: true});
#                 }
                
#                 window.zoomOut = function() {
#                     map.zoomOut(1, {animate: true});
#                 }
                
#                 // Function to fit all waypoints
#                 window.fitWaypoints = function() {
#                     if (waypoints.length > 0) {
#                         const bounds = L.latLngBounds(waypoints);
#                         // Add drone position to bounds if available
#                         const droneLatLng = droneMarker.getLatLng();
#                         if (droneLatLng) {
#                             bounds.extend(droneLatLng);
#                         }
#                         map.fitBounds(bounds, {padding: [50, 50]});
#                     }
#                 }
#             </script>
#         </body>
#         </html>
#         """
#         self.web_view.setHtml(html)
    
#     def add_marker(self, lat, lng, popup_text="Marker"):
#         js = f"""
#         L.marker([{lat}, {lng}]).addTo(map)
#             .bindPopup('{popup_text}');
#         """
#         self.web_view.page().runJavaScript(js)
    
#     @pyqtSlot(dict)
#     def update_from_telemetry(self, data):
#         """Update map with telemetry data"""
#         if 'lat' in data and 'lon' in data:
#             # Update drone position on map
#             self.update_drone_position(data['lat'], data['lon'])
            
#             # Add current position to covered path
#             self.covered_path_points.append({'lat': data['lat'], 'lon': data['lon']})
            
#             # Update current waypoint if available
#             if 'waypoint' in data:
#                 self.set_current_waypoint(data['waypoint'])
    
#     def update_drone_position(self, lat, lon):
#         """Update the drone position on the map"""
#         js = f"window.updateDronePosition({lat}, {lon});"
#         self.web_view.page().runJavaScript(js)
    
#     def add_waypoints(self, waypoint_list):
#         """Add waypoints to the map
#         waypoint_list should be a list of dicts with 'lat' and 'lng' keys
#         """
#         self.waypoints = waypoint_list
#         js = f"window.addWaypoints({self.waypoints});"
#         self.web_view.page().runJavaScript(js)
    
#     def set_current_waypoint(self, index):
#         """Set the currently active waypoint"""
#         if 0 <= index < len(self.waypoints):
#             self.current_waypoint_index = index
#             js = f"window.setCurrentWaypoint({index});"
#             self.web_view.page().runJavaScript(js)
    
#     def fit_waypoints(self):
#         """Fit the map view to include all waypoints"""
#         js = "window.fitWaypoints();"
#         self.web_view.page().runJavaScript(js)
    
#     def add_overlay(self, widget):
#         widget.setParent(self.container)
#         widget.setAutoFillBackground(False)
#         widget.raise_()
#         widget.move(5, 547)
#         widget.show()



from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QStackedLayout, QWidget
from PyQt6.QtCore import Qt, QUrl, pyqtSlot
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings


class MapWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.waypoints = []
        self.current_waypoint_index = 0
        self.covered_path_points = []
        self.home_position = None
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Container widget to hold map and overlays
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view for the map
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.container_layout.addWidget(self.web_view)
        
        # Add container to main layout
        self.layout.addWidget(self.container)
        
        # Load the Leaflet map
        self.load_map()
        
    def load_map(self, center_lat=51.505, center_lng=-0.09, zoom=13):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
            <style>
                body { margin: 0; padding: 0;  background-color: #0A0A0A;}
                #map { position: absolute; top: 0; bottom: 0; width: 100%; height: 100%; border-radius: 20px; background-color: #0A0A0A; }
                
                /* Custom styling for controls */
                .leaflet-control-attribution {
                    background-color: rgba(10, 15, 30, 0.8);
                    color: #00aaff;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
                
                .leaflet-control-zoom a {
                    background-color: rgba(20, 35, 75, 0.8);
                    color: #00ccff;
                    border: 1px solid rgba(0, 150, 255, 0.6);
                }
                
                .leaflet-control-zoom a:hover {
                    background-color: rgba(30, 45, 95, 0.9);
                }
                
                /* Make the grid lines more futuristic */
                .grid-lines {
                    stroke: rgba(0, 170, 255, 0.3);
                    stroke-width: 1px;
                    stroke-dasharray: 5, 5;
                }
                
                /* Custom marker style */
                .drone-marker {
                    filter: drop-shadow(0 0 6px rgba(0, 255, 255, 0.8));
                }
                
                /* Custom waypoint marker style */
                .waypoint-marker {
                    filter: drop-shadow(0 0 4px rgba(0, 100, 255, 0.8));
                }
                
                /* Active waypoint marker style */
                .active-waypoint-marker {
                    filter: drop-shadow(0 0 8px rgba(0, 150, 255, 0.9));
                }
                
                /* Home marker style */
                .home-marker {
                    filter: drop-shadow(0 0 10px rgba(255, 0, 0, 0.9));
                }
                
                @keyframes pulse {
                    0% { transform: scale(0.8); opacity: 1; }
                    70% { transform: scale(1.5); opacity: 0.3; }
                    100% { transform: scale(0.8); opacity: 1; }
                }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                const map = L.map('map', {
                    zoomControl: true,
                    dragging: true,
                    scrollWheelZoom: true,
                    attributionControl: false
                }).setView([16.2729081, 80.4367779], 16);

                // More stylish map with slightly darkened tiles
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    maxZoom: 19,
                    opacity: 0.85
                }).addTo(map);
                
                // Add drone marker with pulsating effect
                const droneIcon = L.divIcon({
                    html: `<div style="display:flex;justify-content:center;align-items:center;width:40px;height:40px;">
                            <div style="width:20px;height:20px;background-color:rgba(0,255,255,0.8);border-radius:50%;
                                        box-shadow:0 0 15px rgba(0,255,255,0.8);animation:pulse 2s infinite;">
                            </div>
                        </div>`,
                    className: 'drone-marker',
                    iconSize: [40, 40],
                    iconAnchor: [20, 20]
                });
                
                const droneMarker = L.marker([16.2729081, 80.4367779], {icon: droneIcon}).addTo(map);
                
                // Create waypoint icon (blue color)
                const waypointIcon = L.divIcon({
                    html: `<div style="display:flex;justify-content:center;align-items:center;width:30px;height:30px;">
                            <div style="width:12px;height:12px;background-color:rgba(0,100,255,0.8);border-radius:50%;
                                        box-shadow:0 0 10px rgba(0,100,255,0.8);">
                            </div>
                        </div>`,
                    className: 'waypoint-marker',
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                });
                
                // Create active waypoint icon (blue color)
                const activeWaypointIcon = L.divIcon({
                    html: `<div style="display:flex;justify-content:center;align-items:center;width:36px;height:36px;">
                            <div style="width:16px;height:16px;background-color:rgba(0,150,255,0.8);border-radius:50%;
                                        box-shadow:0 0 15px rgba(0,150,255,0.8);animation:pulse 1.5s infinite;">
                            </div>
                        </div>`,
                    className: 'active-waypoint-marker',
                    iconSize: [36, 36],
                    iconAnchor: [18, 18]
                });
                
                // Create home point icon (red with 'H')
                const homeIcon = L.divIcon({
                    html: `<div style="display:flex;justify-content:center;align-items:center;width:40px;height:40px;">
                            <div style="width:24px;height:24px;background-color:rgba(255,0,0,0.8);border-radius:50%;
                                      box-shadow:0 0 15px rgba(255,0,0,0.8);display:flex;justify-content:center;align-items:center;">
                                <span style="color:white;font-weight:bold;font-size:14px;">H</span>
                            </div>
                        </div>`,
                    className: 'home-marker',
                    iconSize: [40, 40],
                    iconAnchor: [20, 20]
                });
                
                // Initialize path variables
                const coveredPath = L.polyline([], {
                    color: 'rgba(0, 255, 255, 0.7)', 
                    weight: 3,
                    dashArray: '5, 7'
                }).addTo(map);
                
                const plannedPath = L.polyline([], {
                    color: 'rgba(0, 100, 255, 0.7)', 
                    weight: 3
                }).addTo(map);
                
                // Home to waypoints connections (dotted lines)
                const homeToFirstWaypoint = L.polyline([], {
                    color: 'rgba(0, 100, 255, 0.5)', 
                    weight: 2,
                    dashArray: '3, 6'
                }).addTo(map);
                
                const homeToLastWaypoint = L.polyline([], {
                    color: 'rgba(0, 100, 255, 0.5)', 
                    weight: 2,
                    dashArray: '3, 6'
                }).addTo(map);
                
                // Store home position
                let homePosition = null;
                let homeMarker = null;
                
                // Store waypoints for later use
                const waypoints = [];
                const waypointMarkers = [];
                let currentWaypointIndex = 0;
                
                // Function to update the drone position
                window.updateDronePosition = function(lat, lng) {
                    droneMarker.setLatLng([lat, lng]);
                    
                    // Add point to covered path
                    const path = coveredPath.getLatLngs();
                    path.push([lat, lng]);
                    coveredPath.setLatLngs(path);
                    
                    // Center map on drone with smooth animation
                    map.panTo([lat, lng], {
                        animate: true,
                        duration: 1.2,
                        easeLinearity: 0.5
                    });
                }
                
                // Function to set home position
                window.setHomePosition = function(lat, lng) {
                    homePosition = [lat, lng];
                    
                    // Remove existing home marker if any
                    if (homeMarker) {
                        map.removeLayer(homeMarker);
                    }
                    
                    // Add new home marker
                    homeMarker = L.marker(homePosition, {icon: homeIcon})
                        .addTo(map)
                        .bindPopup('Home');
                    
                    // Update connections if we have waypoints
                    updateHomeConnections();
                }
                
                // Function to add waypoints to the map
                window.addWaypoints = function(waypointsArray) {
                    // Clear existing waypoints
                    waypointMarkers.forEach(marker => map.removeLayer(marker));
                    waypointMarkers.length = 0;
                    waypoints.length = 0;
                    
                    // Add new waypoints
                    waypointsArray.forEach((wp, index) => {
                        const waypointPos = [wp.lat, wp.lng];
                        waypoints.push(waypointPos);
                        
                        // Create marker with appropriate icon
                        const isActive = index === currentWaypointIndex;
                        const icon = isActive ? activeWaypointIcon : waypointIcon;
                        const marker = L.marker(waypointPos, {icon: icon})
                            .addTo(map)
                            .bindPopup(`Waypoint ${index + 1}`);
                        
                        waypointMarkers.push(marker);
                    });
                    
                    // Update planned path
                    if (waypoints.length > 0) {
                        plannedPath.setLatLngs(waypoints);
                        
                        // Update home connections
                        updateHomeConnections();
                    }
                }
                
                // Function to update home connections
                function updateHomeConnections() {
                    if (homePosition && waypoints.length > 0) {
                        // Connect home to first waypoint
                        homeToFirstWaypoint.setLatLngs([homePosition, waypoints[0]]);
                        
                        // Connect home to last waypoint
                        homeToLastWaypoint.setLatLngs([homePosition, waypoints[waypoints.length - 1]]);
                    }
                }
                
                // Function to set current waypoint
                window.setCurrentWaypoint = function(index) {
                    // Update current waypoint index
                    currentWaypointIndex = index;
                    
                    // Update markers
                    waypointMarkers.forEach((marker, idx) => {
                        map.removeLayer(marker);
                        const icon = idx === currentWaypointIndex ? activeWaypointIcon : waypointIcon;
                        waypointMarkers[idx] = L.marker(waypoints[idx], {icon: icon})
                            .addTo(map)
                            .bindPopup(`Waypoint ${idx + 1}`);
                    });
                }
                
                // Function to zoom in/out
                window.zoomIn = function() {
                    map.zoomIn(1, {animate: true});
                }
                
                window.zoomOut = function() {
                    map.zoomOut(1, {animate: true});
                }
                
                // Function to fit all waypoints and home
                window.fitAllPoints = function() {
                    const points = [...waypoints];
                    
                    // Add home position if available
                    if (homePosition) {
                        points.push(homePosition);
                    }
                    
                    // Add drone position
                    const droneLatLng = droneMarker.getLatLng();
                    if (droneLatLng) {
                        points.push([droneLatLng.lat, droneLatLng.lng]);
                    }
                    
                    if (points.length > 0) {
                        const bounds = L.latLngBounds(points);
                        map.fitBounds(bounds, {padding: [50, 50]});
                    }
                }
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html)
    
    def add_marker(self, lat, lng, popup_text="Marker"):
        js = f"""
        L.marker([{lat}, {lng}]).addTo(map)
            .bindPopup('{popup_text}');
        """
        self.web_view.page().runJavaScript(js)
    
    @pyqtSlot(dict)
    def update_from_telemetry(self, data):
        """Update map with telemetry data"""
        if 'lat' in data and 'lon' in data:
            # Update drone position on map
            self.update_drone_position(data['lat'], data['lon'])
            
            # Add current position to covered path
            self.covered_path_points.append({'lat': data['lat'], 'lon': data['lon']})
            
            # Update current waypoint if available
            if 'waypoint' in data:
                self.set_current_waypoint(data['waypoint'])
                
        # Check for home position updates
        if 'home_lat' in data and 'home_lon' in data:
            self.set_home_position(data['home_lat'], data['home_lon'])
    
    def update_drone_position(self, lat, lon):
        """Update the drone position on the map"""
        js = f"window.updateDronePosition({lat}, {lon});"
        self.web_view.page().runJavaScript(js)
    
    def set_home_position(self, lat, lon):
        """Set the home position on the map"""
        self.home_position = {'lat': lat, 'lng': lon}
        js = f"window.setHomePosition({lat}, {lon});"
        self.web_view.page().runJavaScript(js)
    
    def add_waypoints(self, waypoint_list):
        """Add waypoints to the map
        waypoint_list should be a list of dicts with 'lat' and 'lng' keys
        """
        # Convert any waypoints that might use 'lon' instead of 'lng'
        formatted_waypoints = []
        for wp in waypoint_list:
            formatted_wp = wp.copy()
            if 'lon' in formatted_wp and 'lng' not in formatted_wp:
                formatted_wp['lng'] = formatted_wp['lon']
            formatted_waypoints.append(formatted_wp)
            
        self.waypoints = formatted_waypoints
        js = f"window.addWaypoints({self.waypoints});"
        self.web_view.page().runJavaScript(js)
    
    def set_current_waypoint(self, index):
        """Set the currently active waypoint"""
        if 0 <= index < len(self.waypoints):
            self.current_waypoint_index = index
            js = f"window.setCurrentWaypoint({index});"
            self.web_view.page().runJavaScript(js)
    
    def fit_all_points(self):
        """Fit the map view to include all waypoints, home, and drone position"""
        js = "window.fitAllPoints();"
        self.web_view.page().runJavaScript(js)
    
    def add_overlay(self, widget):
        widget.setParent(self.container)
        widget.setAutoFillBackground(False)
        widget.raise_()
        widget.move(10, 660)
        widget.show()
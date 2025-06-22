from PyQt6.QtWidgets import QHBoxLayout, QFrame, QSizePolicy
from Gauges.alt import EnhancedAltitudeIndicator
from Gauges.compassgauge import FuturisticCompass
from Gauges.speedgauge import EnhancedSpeedIndicator
from Gauges.vsi import EnhancedVSI
from PyQt6.QtCore import pyqtSlot

class GaugesWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setObjectName("gaugesWidget")
        self.setStyleSheet("""
            #gaugesWidget {
                border: none;  /* Remove border */
                background-color: rgba(0, 0, 0, 120); /* Completely transparent background */
                border-radius : 20px;
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        gauges_layout = QHBoxLayout(self)
        gauges_layout.setContentsMargins(0, 0, 0,0)

        self.altitude_gauge = EnhancedAltitudeIndicator()
        self.compass_gauge = FuturisticCompass()
        self.speed_gauge = EnhancedSpeedIndicator()
        self.vsi_gauge = EnhancedVSI()
        
        gauges_layout.addWidget(self.altitude_gauge)
        gauges_layout.addWidget(self.compass_gauge)
        gauges_layout.addWidget(self.speed_gauge)
        gauges_layout.addWidget(self.vsi_gauge)
        
        for gauge in [self.altitude_gauge, self.compass_gauge, #very very important dont change
                     self.speed_gauge, self.vsi_gauge]:
            gauge.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)     
        
        self.setFixedHeight(160)
        self.setFixedWidth(580)
    
    def connect_monitoring_thread(self, monitoring_thread):
        """Connect the monitoring thread's data_updated signal to update the gauges"""
        monitoring_thread.data_updated.connect(self.update_gauges)
    
    @pyqtSlot(dict)
    def update_gauges(self, data):
        """Update all gauges with real data from the monitoring thread"""
        # Update altitude gauge
        if 'alt' in data:
            self.altitude_gauge.altitude = data['alt']
            self.altitude_gauge.update()
        
        # Update compass gauge with heading information
        if 'heading' in data:
            self.compass_gauge.set_direction(data['heading'])
        
        # Update speed gauge
        if 'groundspeed' in data:
            self.speed_gauge.speed = data['groundspeed']
            self.speed_gauge.update()
        
        # Update vertical speed indicator
        if 'climb' in data:
            self.vsi_gauge.vertical_speed = data['climb']
            self.vsi_gauge.update()
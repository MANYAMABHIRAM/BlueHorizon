import sys
import random
import math
from PyQt6.QtCore import ( Qt, QRect, QTimer, pyqtProperty, QPropertyAnimation, QEasingCurve, QPoint, QPointF, QUrl, QRectF, QMargins,QEvent )
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QPushButton, QFrame, QComboBox, QLineEdit, QScrollArea, QTextEdit, 
                             QGroupBox, QSizePolicy, QProgressBar,QStackedLayout,QSizePolicy )
from PyQt6.QtGui import ( QPalette, QColor, QFont, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient, QPolygon, QFontMetrics, QPainterPath, QTransform, QCursor)

class EnhancedHUDWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setMaximumSize(600, 400)
        self.setStyleSheet("background-color: #0A0A0A;")

        self.arm_state          = "DISARMED" 
        self.heading            = 5          
        self.pitch              = 0          
        self.roll               = 0    
        self.battery_percent    = 90.0
        self.battery_current    = 0.4
        self.battery_voltage    = 11.9
        self.airspeed           = 0.0
        self.groundspeed        = 0.0
        self.gps_status         = "No GPS"
        self.altitude           = 0
        self.altitude_max       = 250 
        self.airspeed_max       = 50 
        self.hori_bar_left      = self.airspeed
        self.hori_bar_right     = self.altitude
        self.bottom_status      = "Not Ready to Arm"
        self.bottom_vibe        = "Vibe"
        self.bottom_ekf         = "EKF"
        self.bottom_alt_info    = "Unknown"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.randomUpdate)
        self.timer.start(110)
        self.heading_offset = 0
        self.glow_counter = 0

    def randomUpdate(self):
        self.heading = (self.heading + random.uniform(-2, 2)) % 360
        self.heading_offset = (self.heading_offset + random.uniform(-5, 5)) % 100
        self.pitch = max(-20, min(20, self.pitch + random.uniform(-1, 1)))
        self.roll = max(-45, min(45, self.roll + random.uniform(-2, 2)))
        self.hori_bar_left = max(-self.airspeed_max, min(self.airspeed_max, self.hori_bar_left + random.uniform(-5, 5)))
        self.hori_bar_right = max(-self.altitude_max, min(self.altitude_max, self.hori_bar_right + random.uniform(-5, 5)))
        self.airspeed = self.hori_bar_left
        self.groundspeed = self.airspeed * 0.95
        self.altitude = self.hori_bar_right
        self.glow_counter = (self.glow_counter + 1) % 100
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.contentsRect()

        # === 1. DRAW STATIC BACKGROUND (Sky + Ground) ===
        p.save()

        diagonal = math.sqrt(r.width()**2 + r.height()**2)
        extended_w = int(diagonal)
        extended_h = int(diagonal)
        ext_x = r.center().x() - extended_w // 2
        ext_y = r.center().y() - extended_h // 2
        extended_rect = QRect(ext_x, ext_y, extended_w, extended_h)

        # Sky (Top Half)
        sky_rect = QRect(extended_rect.left(), extended_rect.top(), extended_rect.width(), extended_rect.height() // 2)
        sky_grad = QLinearGradient(QPointF(sky_rect.topLeft()), QPointF(sky_rect.bottomLeft()))
        sky_grad.setColorAt(0, QColor(30, 100, 180))
        sky_grad.setColorAt(0.4, QColor(66, 161, 198))
        sky_grad.setColorAt(1, QColor(100, 190, 220))
        p.fillRect(sky_rect, sky_grad)

        # Ground (Bottom Half)
        ground_rect = QRect(extended_rect.left(), extended_rect.center().y(), extended_rect.width(), extended_rect.height() // 2)
        ground_grad = QLinearGradient(QPointF(ground_rect.topLeft()), QPointF(ground_rect.bottomLeft()))
        ground_grad.setColorAt(0, QColor(60, 150, 60))
        ground_grad.setColorAt(0.6, QColor(40, 130, 40))
        ground_grad.setColorAt(1, QColor(20, 100, 20))
        p.fillRect(ground_rect, ground_grad)

        p.restore()

        # === 2. DRAW ATTITUDE INDICATORS (Move with Roll and Pitch) ===
        p.save()

        p.translate(r.center())
        p.rotate(-self.roll)
        pitch_shift = self.pitch * 4  # You can adjust sensitivity
        p.translate(0, pitch_shift)
        p.translate(-r.center())

        # Draw artificial horizon line (after pitch & roll applied)
        horizon_y = r.center().y()
        p.setPen(QPen(QColor(255, 30, 30), 2))
        p.drawLine(r.left(), horizon_y, r.right(), horizon_y)

        # Draw pitch ladder (example simple lines every 10 degrees)
        p.setPen(QPen(QColor(255, 255, 255), 1))
        for pitch in range(-90, 91, 10):
            offset = pitch * 4
            y = r.center().y() + offset
            if r.top() < y < r.bottom():
                p.drawLine(r.center().x() - 40, y, r.center().x() + 40, y)

        p.restore()

        # === 3. DRAW STATIC OTHER STUFF (HUD elements like crosshair, heading scale, bars) ===
        p.save()

        # Draw center crosshair
        crosshair_size = 20
        p.setPen(QPen(QColor(0, 220, 255), 2))
        p.drawLine(r.center().x() - crosshair_size, r.center().y(), r.center().x() + crosshair_size, r.center().y())
        p.drawLine(r.center().x(), r.center().y() - crosshair_size, r.center().x(), r.center().y() + crosshair_size)

        # Draw heading scale, battery, altitude bars, etc. (like your old code here)

        p.restore()

        # 2) Top Heading Bar with Horizontal Circular Scale
        top_bar_h = 50
        top_bar_rect = QRect(r.left(), r.top()-8, r.width(), top_bar_h)
        pointer_x = top_bar_rect.center().x()

        # Create a horizontal heading scale & background
        scale_width = int(r.width() * 0.55)
        scale_height = 25 - 5
        scale_rect = QRect(int(pointer_x - scale_width/2), int(top_bar_rect.top() + 15), scale_width, scale_height)
        p.setBrush(QColor(0, 30, 50, 200))
        p.setPen(QPen(QColor(0, 200, 255), 2))
        p.drawRoundedRect(scale_rect, 3, 3)

        visible_range = 140  
        center_heading = self.heading
        pixels_per_degree = scale_width / visible_range
        half_range = visible_range / 2
        start_degree , end_degree = int(center_heading - half_range) , int(center_heading + half_range)

        for degree in range(start_degree, end_degree + 1):
            angle = degree % 360
            rel_angle = ((degree - center_heading + 540) % 360) - 180

            if abs(rel_angle) > half_range:
                continue
            x_pos = pointer_x + rel_angle * pixels_per_degree / (visible_range / 360)
            if x_pos < scale_rect.left() or x_pos > scale_rect.right():
                continue
            if angle % 10 == 0: # Major tick
                p.setPen(QPen(QColor(255, 255, 255), 2))
                p.drawLine(int(x_pos), scale_rect.top() + 5, int(x_pos), scale_rect.bottom() - 5)
                p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                label = f"{angle:03d}" if angle > 0 else "000"
                p.drawText(int(x_pos - 12), scale_rect.top() + 15, 24, 20, Qt.AlignmentFlag.AlignCenter, label)
            elif angle % 5 == 0:  # Medium tick
                p.setPen(QPen(QColor(0, 180, 220), 1))
                p.drawLine(int(x_pos), scale_rect.top() + 5, int(x_pos), scale_rect.bottom() - 5)
            half_angle = angle + 2.5
            if half_angle < 360:
                rel_half_angle = ((half_angle - center_heading + 540) % 360) - 180
                if abs(rel_half_angle) <= half_range:
                    x_half = pointer_x + rel_half_angle * pixels_per_degree / (visible_range / 360)
                    if scale_rect.left() <= x_half <= scale_rect.right():
                        p.setPen(QPen(QColor(100, 100, 100), 1))
                        p.drawLine(int(x_half), scale_rect.top() + 8, int(x_half), scale_rect.bottom() - 8)

        digital_heading = f"{int(self.heading):03d}°"
        p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        heading_width = QFontMetrics(p.font()).horizontalAdvance(digital_heading)
        center_x , center_y= int(pointer_x - heading_width/2) , int(scale_rect.top() + 12)
        heading_box = QRect(center_x - 10, center_y - 10, heading_width + 20, 16)
        heading_gradient = QLinearGradient(QPointF(heading_box.topLeft()), QPointF(heading_box.bottomLeft()))
        heading_gradient.setColorAt(0, QColor(0, 40, 70))
        heading_gradient.setColorAt(1, QColor(0, 30, 50))
        p.setBrush(heading_gradient)
        p.setPen(QPen(QColor(0, 200, 255), 1))
        p.drawRoundedRect(heading_box, 3, 3)
        p.setPen(QPen(QColor(220, 255, 255)))
        p.drawText(heading_box, Qt.AlignmentFlag.AlignCenter, digital_heading)

        # 3) Central Attitude Indicator with Enhanced Pitch Lines
        circle_center = QPointF(r.center())
        dial_radius = min(r.width(), r.height()) * 0.4
        arc_center_y = horizon_y - dial_radius * 0.3
        
        # Fixed arc position that doesn't move with pitch
        arc_offset = 20
        arc_rect = QRect( int(circle_center.x() - dial_radius), int(circle_center.y() - dial_radius + arc_offset),int(dial_radius * 2), int(dial_radius * 2) )
        
        dial_radius = arc_rect.width() / 2 
        arc_path = QPainterPath()

        arc_path.moveTo(arc_rect.center().x() + dial_radius * math.cos(math.radians(30)), arc_rect.center().y() - dial_radius * math.sin(math.radians(30)))
        arc_path.arcTo(QRectF(arc_rect), 30, 120)
        
        p.setFont(QFont("Consolas", 7))
        
        arc_center_x = arc_rect.center().x()
        arc_center_y = arc_rect.center().y()
        
        p.save()
        p.translate(arc_center_x, arc_center_y)
        p.rotate(-self.roll)
        p.translate(-arc_center_x, -arc_center_y)

        p.setPen(QPen(QColor(255, 255, 255), 2.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(arc_path)

        p.setFont(QFont("Consolas", 7))

        for angle in range(30, 151, 10):
            rad_angle = math.radians(angle)
            
            outer_x = arc_center_x - dial_radius * math.cos(rad_angle)
            outer_y = arc_center_y - dial_radius * math.sin(rad_angle)
            
            if angle % 30 == 0:
                inner_x = arc_center_x - (dial_radius - 12) * math.cos(rad_angle) 
                inner_y = arc_center_y - (dial_radius - 12) * math.sin(rad_angle) 
                p.setPen(QPen(QColor(255, 255, 255), 2))
                
                if angle != 90:
                    text_x = arc_center_x - (dial_radius - 25) * math.cos(rad_angle)
                    text_y = arc_center_y - (dial_radius - 25) * math.sin(rad_angle)
                    angle_text = f"{abs(angle - 90):d}°"
                    
                    text_width = QFontMetrics(p.font()).horizontalAdvance(angle_text)
                    p.drawText(int(text_x - text_width/2), int(text_y + 4), angle_text)
            else:
                inner_x = arc_center_x - (dial_radius - 8) * math.cos(rad_angle)
                inner_y = arc_center_y - (dial_radius - 8) * math.sin(rad_angle) 
                p.setPen(QPen(QColor(200, 200, 200), 1))
            p.drawLine(int(outer_x), int(outer_y), int(inner_x), int(inner_y)) 
        p.restore()

        # Draw fixed triangular marker at top of arc
        fixed_marker = QPainterPath()
        top_x = arc_center_x
        top_y = arc_center_y - dial_radius

        fixed_marker.moveTo(top_x, top_y)
        fixed_marker.lineTo(top_x - 8, top_y - 8)
        fixed_marker.lineTo(top_x + 8, top_y - 8)
        fixed_marker.closeSubpath()

        p.setPen(QPen(QColor(255, 30, 30), 1))
        p.setBrush(QBrush(QColor(255, 30, 30, 220)))
        p.drawPath(fixed_marker)

        # Draw the ARM/DISARM status with enhanced visibility
        arm_font = QFont("Consolas", 17, QFont.Weight.Bold)
        p.setFont(arm_font)
        arm_text = self.arm_state
        arm_width = QFontMetrics(arm_font).horizontalAdvance(arm_text)
        circle_center = QPointF(r.center()) 
        if self.arm_state == "ARMED":
            p.setBrush(QBrush(QColor(40, 0, 0, 150)))
        else:
            p.setBrush(QBrush(QColor(30, 0, 0, 120)))
            
        arm_path = QPainterPath()
        arm_path.addText(int(circle_center.x() - arm_width/2), int(circle_center.y() + 100), arm_font, arm_text)
        
        p.setPen(QPen(QColor(255, 250, 250, 80), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(arm_path)
        # p.setPen(QPen(QColor(255, 50, 50)))
        # p.setBrush(QBrush(QColor(255, 50, 50)))
        # p.drawPath(arm_path)

        # 4) Enhanced Futuristic Left and Right Bars
        left_bar_width = 35
        left_bar_rect = QRect(r.left() + 5, r.top() + 50 + 20 - 40, left_bar_width, r.height() - 50 - 80 + 40)
        # Right vertical bar (altitude)
        right_bar_width = 35
        right_bar_rect = QRect(r.right() - right_bar_width - 10, r.top() + 50 + 20 - 40, right_bar_width,  r.height() - 50 - 80 +40)
        # Draw advanced backgrounds for bars with multi-layer effect
        for bar_rect in [left_bar_rect, right_bar_rect]:
            # Main background
            p.setPen(QPen(QColor(0, 100, 150, 200), 1))
            grad = QLinearGradient(QPointF(bar_rect.topLeft()), QPointF(bar_rect.bottomLeft()))
            grad.setColorAt(0, QColor(0, 30, 60, 190))
            grad.setColorAt(1, QColor(0, 15, 40, 190))
            p.setBrush(grad)
            p.drawRoundedRect(bar_rect, 5, 5)
            # Draw advanced technical grid lines on the bars
            p.setPen(QPen(QColor(0, 100, 180, 50), 1, Qt.PenStyle.DotLine))
            grid_spacing_v = 20
            for y in range(bar_rect.top(), bar_rect.bottom(), grid_spacing_v):
                p.drawLine(bar_rect.left() + 2, y, bar_rect.right() - 2, y)     
            # Vertical center line
            p.setPen(QPen(QColor(0, 120, 200, 80), 1, Qt.PenStyle.DashLine))
            p.drawLine( bar_rect.left() + bar_rect.width() // 2,bar_rect.top() + 2,bar_rect.left() + bar_rect.width() // 2,bar_rect.bottom() - 2)           
        # Draw left bar content (airspeed) with enhanced styling
        left_bar_title = "AIRSPEED"
        left_bar_unit = "m/s"
        left_value_str = f"{self.airspeed:.1f}"
        # Top Label with neon style
        p.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        label_width = QFontMetrics(p.font()).horizontalAdvance(left_bar_title)
        title_bg_rect = QRect(left_bar_rect.left() + (left_bar_rect.width() - label_width) // 2 + 5, left_bar_rect.top() - 25, label_width + 20, 20)
        # Label background with glow effect
        p.setPen(QPen(QColor(0, 150, 255, 50), 3))
        p.setBrush(QBrush(QColor(0, 20, 40, 180)))
        p.drawRoundedRect(title_bg_rect, 5, 5)
        p.setPen(QPen(QColor(0, 200, 255), 1))
        p.drawRoundedRect(title_bg_rect, 5, 5)
        p.setPen(QPen(QColor(0, 220, 255)))
        p.drawText(title_bg_rect, Qt.AlignmentFlag.AlignCenter, left_bar_title)
        # Define airspeed limits (similar to altitude limits)
        airspeed_max = 50  # Upper limit
        airspeed_min = -50  # Lower limit
        # Add center line to indicate zero airspeed
        center_y = left_bar_rect.top() + left_bar_rect.height() // 2
        p.setPen(QPen(QColor(255, 255, 255, 120), 1))
        p.drawLine(left_bar_rect.left() + 2, center_y, left_bar_rect.right() - 2, center_y)
        # Calculate bar height relative to center
        max_half_height = left_bar_rect.height() // 2
        normalized_speed = max(min(self.airspeed, airspeed_max), airspeed_min)
        is_negative = normalized_speed < 0
        # Calculate the proportion of height relative to the full range
        bar_height = int(abs(normalized_speed) / airspeed_max * max_half_height)
        # Determine bar position based on sign of airspeed
        if is_negative:
            # For negative values, bar extends downward from center
            bar_height_total = bar_height
            # Red gradient for negative values
            bar_grad = QLinearGradient(QPointF(left_bar_rect.left(), center_y), QPointF(left_bar_rect.left(), center_y + bar_height))
            bar_grad.setColorAt(0, QColor(255, 100, 100))
            bar_grad.setColorAt(0.5, QColor(255, 50, 50))
            bar_grad.setColorAt(1, QColor(200, 0, 0))
        else:
            # For positive values, bar extends upward from center
            bar_height_total = bar_height
            # Blue gradient for positive values (existing colors)
            bar_grad = QLinearGradient(QPointF(left_bar_rect.left(), center_y), QPointF(left_bar_rect.left(), center_y - bar_height))
            bar_grad.setColorAt(0, QColor(0, 150, 255))
            bar_grad.setColorAt(0.5, QColor(0, 200, 255))
            bar_grad.setColorAt(1, QColor(100, 220, 255))

        # Inner bar fill
        p.setBrush(bar_grad)
        p.setPen(Qt.PenStyle.NoPen)
        if is_negative:
            # For negative values, draw from center downward
            inner_bar = QRect(left_bar_rect.left() + 4, center_y, left_bar_rect.width() - 8, bar_height_total)
        else:
            # For positive values, draw from (center - bar_height) upward
            inner_bar = QRect(left_bar_rect.left() + 4, center_y - bar_height_total,left_bar_rect.width() - 8, bar_height_total)
        p.drawRoundedRect(inner_bar, 3, 3)

        # Top/bottom bar cap with modern indicator (depends on whether positive or negative)
        cap_height = 6
        if is_negative:
            # For negative values, cap at the bottom of the bar
            cap_y = center_y + bar_height_total - cap_height // 2
            cap_color = QColor(255, 50, 50)
        else:
            # For positive values, cap at the top of the bar
            cap_y = center_y - bar_height_total - cap_height // 2
            cap_color = QColor(0, 220, 255)

        cap_rect = QRect(left_bar_rect.left() + 2, cap_y, left_bar_rect.width() - 4, cap_height)
        p.setBrush(QBrush(cap_color))
        p.drawRoundedRect(cap_rect, 2, 2)

        # Value display with enhanced background
        value_font = QFont("Consolas", 6, QFont.Weight.Bold)
        p.setFont(value_font)
        value_width = QFontMetrics(value_font).horizontalAdvance(left_value_str)

        # Position the value display next to the indicator cap
        if is_negative:
            value_y = center_y + bar_height_total - 10  # Near the bottom cap for negative values
        else:
            value_y = center_y - bar_height_total - 10  # Near the top cap for positive values

        value_rect = QRect(left_bar_rect.right() + 5, 
                        value_y,
                        value_width + 20, 20)

        p.setPen(QPen(QColor(255, 255, 255, 40), 3))
        p.setBrush(QBrush(QColor(0, 20, 40, 180)))
        p.drawRoundedRect(value_rect, 5, 5)
        p.setPen(QPen(QColor(0, 200, 255) if not is_negative else QColor(255, 100, 100), 1))
        p.drawRoundedRect(value_rect, 5, 5)
        p.setPen(QPen(QColor(255, 220, 255) if not is_negative else QColor(255, 200, 200)))
        p.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, left_value_str)
        # Add unit at the bottom
        unit_font = QFont("Consolas", 8)
        p.setFont(unit_font)
        unit_width = QFontMetrics(unit_font).horizontalAdvance(left_bar_unit)
        unit_rect = QRect(left_bar_rect.left() + (left_bar_rect.width() - unit_width) // 2, left_bar_rect.bottom() + 5, unit_width, 20)
        p.setPen(QPen(QColor(255, 255, 255), 3))
        p.drawText(unit_rect, Qt.AlignmentFlag.AlignCenter, left_bar_unit)
        
        # Draw right bar content (altitude) with enhanced styling
        right_bar_title = "ALTITUDE"
        right_bar_unit = "m"
        right_value_str = f"{self.altitude:.1f}"
        # Top Label with neon style
        p.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        label_width = QFontMetrics(p.font()).horizontalAdvance(right_bar_title)
        title_bg_rect = QRect(right_bar_rect.left() + (right_bar_rect.width() - label_width) // 2 -15,right_bar_rect.top() - 25,label_width + 20,20)
        p.setPen(QPen(QColor(0, 150, 255, 50), 3))
        p.setBrush(QBrush(QColor(0, 20, 40, 180)))
        p.drawRoundedRect(title_bg_rect, 5, 5)
        p.setPen(QPen(QColor(0, 200, 255), 1))
        p.drawRoundedRect(title_bg_rect, 5, 5)
        p.setPen(QPen(QColor(0, 220, 255)))
        p.drawText(title_bg_rect, Qt.AlignmentFlag.AlignCenter, right_bar_title)

        altitude_max , altitude_min = 100 , -100  # Limits
        
        center_y = right_bar_rect.top() + right_bar_rect.height() // 2 # Add center line to indicate zero altitude
        p.setPen(QPen(QColor(255, 255, 255, 120), 1))
        p.drawLine(right_bar_rect.left() + 2, center_y, right_bar_rect.right() - 2, center_y)
        
        max_half_height = right_bar_rect.height() // 2 # Calculate bar height relative to center
        normalized_alt = max(min(self.altitude, altitude_max), altitude_min)
        is_negative = normalized_alt < 0
        
        bar_height = int(abs(normalized_alt) / altitude_max * max_half_height) # Calculate the proportion of height relative to the full range
        
        if is_negative: # Determine bar position based on sign of altitude
            bar_height_total = bar_height
            bar_grad = QLinearGradient(QPointF(right_bar_rect.left(), center_y), QPointF(right_bar_rect.left(), center_y + bar_height)) # Red gradient for negative values
            bar_grad.setColorAt(0, QColor(255, 100, 100))
            bar_grad.setColorAt(0.5, QColor(255, 50, 50))
            bar_grad.setColorAt(1, QColor(200, 0, 0))
        else:
            bar_height_total = bar_height # For positive values, bar extends upward from center
            bar_grad = QLinearGradient(QPointF(right_bar_rect.left(), center_y),QPointF(right_bar_rect.left(), center_y - bar_height)) # Blue gradient for positive values (existing colors)
            bar_grad.setColorAt(0, QColor(0, 150, 255))
            bar_grad.setColorAt(0.5, QColor(0, 200, 255))
            bar_grad.setColorAt(1, QColor(100, 220, 255))

        # Inner bar fill
        p.setBrush(bar_grad)
        p.setPen(Qt.PenStyle.NoPen)
        if is_negative:  # For negative values, draw from center downward     
            inner_bar = QRect(right_bar_rect.left() + 4, center_y, right_bar_rect.width() - 8, bar_height_total)
        else:   # For positive values, draw from (center - bar_height) upward
            inner_bar = QRect(right_bar_rect.left() + 4, center_y - bar_height_total, right_bar_rect.width() - 8, bar_height_total)
        p.drawRoundedRect(inner_bar, 3, 3)

        cap_height = 6 # Top/bottom bar cap with modern indicator (depends on whether positive or negative)
        if is_negative: # For negative values, cap at the bottom of the bar
            cap_y = center_y + bar_height_total - cap_height // 2
            cap_color = QColor(255, 50, 50)
        else:  # For positive values, cap at the top of the bar
            cap_y = center_y - bar_height_total - cap_height // 2
            cap_color = QColor(0, 220, 255)
        cap_rect = QRect(right_bar_rect.left() + 2, cap_y, right_bar_rect.width() - 4, cap_height)
        p.setBrush(QBrush(cap_color))
        p.drawRoundedRect(cap_rect, 2, 2)

        value_font = QFont("Consolas", 6, QFont.Weight.Bold) # Value display with enhanced background
        p.setFont(value_font)
        value_width = QFontMetrics(value_font).horizontalAdvance(right_value_str)
        
        if is_negative:  # Position the value display next to the indicator cap
            value_y = center_y + bar_height_total - 10  # Near the bottom cap for negative values
        else:
            value_y = center_y - bar_height_total - 10  # Near the top cap for positive values
        value_rect = QRect(right_bar_rect.left() - value_width - 25, value_y,value_width + 20, 20)

        p.setPen(QPen(QColor(255, 255, 255, 40), 3))
        p.setBrush(QBrush(QColor(0, 20, 40, 180)))
        p.drawRoundedRect(value_rect, 5, 5)
        p.setPen(QPen(QColor(0, 200, 255) if not is_negative else QColor(255, 100, 100), 1))
        p.drawRoundedRect(value_rect, 5, 5)
        p.setPen(QPen(QColor(255, 220, 255) if not is_negative else QColor(255, 200, 200)))
        p.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, right_value_str)   
        unit_font = QFont("Consolas", 8)
        p.setFont(unit_font)
        unit_width = QFontMetrics(unit_font).horizontalAdvance(right_bar_unit)
        unit_rect = QRect(right_bar_rect.left() + (right_bar_rect.width() - unit_width) // 2,right_bar_rect.bottom() + 5,unit_width,20)
        p.setPen(QPen(QColor(255, 255, 255),3))
        p.drawText(unit_rect, Qt.AlignmentFlag.AlignCenter, right_bar_unit)

        # 5) Bottom Status Bar with Enhanced Design
        bottom_height = 30
        bottom_rect = QRect( r.left(), r.bottom() - bottom_height,r.width(), bottom_height)
        
        bottom_gradient = QLinearGradient(QPointF(bottom_rect.left(), bottom_rect.top()),QPointF(bottom_rect.left(), bottom_rect.bottom()))
        bottom_gradient.setColorAt(0, QColor(10, 20, 30, 220))
        bottom_gradient.setColorAt(1, QColor(5, 10, 15, 220))
        p.fillRect(bottom_rect, bottom_gradient)
        
        # Add top edge highlight
        p.setPen(QPen(QColor(0, 200, 255), 1))
        p.drawLine(bottom_rect.left(), bottom_rect.top(), bottom_rect.right(), bottom_rect.top())
        
        # Add subtle grid pattern overlay
        p.setPen(QPen(QColor(0, 100, 200, 20), 1, Qt.PenStyle.DotLine))
        grid_spacing = 10
        for x in range(0, r.width(), grid_spacing):
            p.drawLine(x, bottom_rect.top(), x, bottom_rect.bottom())
        
        # Divide into sections with futuristic separators
        section_width = bottom_rect.width() / 4
        
        divider_gradient = QLinearGradient(QPointF(0, bottom_rect.top() + 5),QPointF(0, bottom_rect.bottom() - 5))
        divider_gradient.setColorAt(0, QColor(0, 150, 200, 0))
        divider_gradient.setColorAt(0.5, QColor(0, 150, 200, 120))
        divider_gradient.setColorAt(1, QColor(0, 150, 200, 0))
        
        for i in range(1, 4):
            x_pos = int(bottom_rect.left() + i * section_width)
            divider_rect = QRect(x_pos - 1, bottom_rect.top() + 5, 2, bottom_rect.height() - 10)
            p.fillRect(divider_rect, divider_gradient)
            
            p.setPen(QPen(QColor(0, 200, 255), 1))
            p.drawLine(x_pos - 3, bottom_rect.top() + 2, x_pos + 3, bottom_rect.top() + 2)
            p.drawLine(x_pos - 3, bottom_rect.bottom() - 2, x_pos + 3, bottom_rect.bottom() - 2)
        
        section_rects = []
        for i in range(4):
            section_rects.append(QRect(int(bottom_rect.left() + i * section_width + 5),bottom_rect.top() + 5,int(section_width - 10),bottom_rect.height() - 10))
        
        # Draw content for each section with enhanced styling
        status_font = QFont("Consolas", 7, QFont.Weight.Bold)
        p.setFont(status_font)
        
        # Section 1: Status
        status_text = self.bottom_status
        p.setPen(QPen(QColor(0, 200, 255)))
        p.drawText(section_rects[0], Qt.AlignmentFlag.AlignCenter, status_text)
        
        
        if "Arm" in status_text:
            light_color = QColor(255, 50, 50, 150 + int(105 * math.sin(self.glow_counter * 0.1)))
        else:
            light_color = QColor(0, 255, 100, 150 + int(105 * math.sin(self.glow_counter * 0.1)))
        
        # Section 2: VIBE
        vibe_text = self.bottom_vibe
        p.setPen(QPen(QColor(0, 200, 255)))
        p.drawText(section_rects[1], Qt.AlignmentFlag.AlignCenter, vibe_text)
        
        # Section 3: EKF
        ekf_text = self.bottom_ekf
        p.setPen(QPen(QColor(0, 200, 255)))
        p.drawText(section_rects[2], Qt.AlignmentFlag.AlignCenter, ekf_text)
        
        # Section 4: Alt Info
        alt_text = self.bottom_alt_info
        p.setPen(QPen(QColor(0, 200, 255)))
        p.drawText(section_rects[3], Qt.AlignmentFlag.AlignCenter, alt_text)
        
        # 6) Add Battery Indicator with Enhanced Futuristic Design
        battery_width  = int(r.width()  * 0.10)
        battery_height = int(r.height() * 0.075)
        # position it at 10% from left, 75% from top
        battery_x = r.left() + int(r.width()  * 0.20)
        battery_y = r.top()  + int(r.height() * 0.559)
        battery_rect = QRect(battery_x, battery_y, battery_width, battery_height)
        
        # Draw battery background with tech detail
        p.setPen(QPen(QColor(0, 150, 220, 40), 4))
        p.setBrush(QBrush(QColor(0, 20, 40, 180)))
        # p.drawRoundedRect(battery_rect, 8, 8)
        
        p.setPen(QPen(QColor(0, 180, 255), 1))
        p.drawRoundedRect(battery_rect, 8, 8)
        
        # Battery level fill with enhanced styling
        fill_width = int((battery_rect.width() - 10) * (self.battery_percent / 100))
        fill_rect = QRect(battery_rect.left() + 5,battery_rect.top() + 5,fill_width,battery_rect.height() - 10)
        
        # Battery level gradient based on charge
        battery_grad = QLinearGradient(QPointF(fill_rect.left(), fill_rect.top()),QPointF(fill_rect.right(), fill_rect.top()))
         
        if self.battery_percent < 20:
            # Red for low battery
            battery_grad.setColorAt(0, QColor(255, 40, 40))
            battery_grad.setColorAt(1, QColor(255, 80, 50))
        elif self.battery_percent < 50:
            # Yellow for medium battery
            battery_grad.setColorAt(0, QColor(255, 180, 0))
            battery_grad.setColorAt(1, QColor(255, 220, 0))
        else:
            # Blue-green for good battery
            battery_grad.setColorAt(0, QColor(0, 180, 200))
            battery_grad.setColorAt(1, QColor(0, 220, 255))
        p.setBrush(battery_grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(fill_rect, 4, 4)
        # Add digital battery readout with enhanced style
        batt_text = f"{self.battery_percent:.1f}%"
        batt_font = QFont("Consolas", 7, QFont.Weight.Bold)
        p.setFont(batt_font)
        # Add a small glow effect if battery is low
        if self.battery_percent < 20:
            p.setPen(QPen(QColor(255, 255, 255)))
        else:
            p.setPen(QPen(QColor(0, 0, 0) if self.battery_percent > 30 else QColor(255, 255, 255)))
        
        p.drawText(battery_rect, Qt.AlignmentFlag.AlignCenter, batt_text)
        # Add voltage and current info below battery
        info_font = QFont("Consolas", 7)
        p.setFont(info_font)
        voltage_text = f"V:{self.battery_voltage:.1f}V" 
        current_text = f"I:{self.battery_current:.1f}A"
        p.setPen(QPen(QColor(255, 0, 0)))
        text_x = battery_rect.left() + 5
        line_height = QFontMetrics(info_font).height()
        text_y = battery_rect.bottom() + 5
        p.setPen(QPen(QColor(255, 255, 255)))
        p.drawText(text_x, text_y + line_height, voltage_text)
        p.drawText(text_x, text_y + 2*line_height + 2, current_text)
        
        # 7) GPS Status Indicator
        gps_width  = int(r.width()  * 0.10)
        gps_height = int(r.height() * 0.075)
        gps_x = r.right() - gps_width - int(r.width() * 0.20)
        gps_y = r.top()   + int(r.height() * 0.55)
        gps_rect = QRect(gps_x, gps_y, gps_width, gps_height)
        p.setPen(QPen(QColor(0, 150, 220, 40), 4))
        p.setBrush(QBrush(QColor(0, 20, 40, 180)))
        p.drawRoundedRect(gps_rect, 8, 8)
        p.setPen(QPen(QColor(0, 180, 255), 1))
        p.drawRoundedRect(gps_rect, 8, 8)
        gps_font = QFont("Consolas", 7, QFont.Weight.Bold)
        p.setFont(gps_font)
        if "No GPS" in self.gps_status:
            p.setPen(QPen(QColor(255, 50, 50)))
        else:
            p.setPen(QPen(QColor(0, 220, 255)))
        p.drawText(gps_rect, Qt.AlignmentFlag.AlignCenter, self.gps_status)
        speed_text = f"GS: {self.groundspeed:.1f} m/s"
        p.setFont(info_font)
        p.setPen(QPen(QColor(255, 255, 255)))
        p.drawText(gps_rect.right() - QFontMetrics(info_font).horizontalAdvance(speed_text) + 7,gps_rect.bottom() + 15,speed_text)
        # draw_futuristic_crosshair(p, r.center().x(), r.center().y())
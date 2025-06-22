from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, QTime
from PyQt6.QtGui import (QPainter, QColor, QFont, QPen, QBrush, QRadialGradient, 
                        QPainterPath, QLinearGradient, QFontMetrics)
import sys
import math
import random

class EnhancedSpeedIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Enhanced Speed Indicator")
        self.resize(300, 300)
        
        self.speed = 0  # Range from 0 to 100
        
        # Create shadow effect for the whole widget
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 120, 255, 70))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        # Set background style
        self.setStyleSheet("""
            background: qradialgradient(cx:0.5, cy:0.5, radius:1.0, fx:0.5, fy:0.5, 
                        stop:0 #0A1225, stop:0.9 #0D1A30, stop:1 #081020);
            border: 1px solid #0077AA;
            border-radius: 10px;
        """)
        
        # Set up timer for random updates
        self.timer = QTimer(self)
        self.timer.start(1500)  # Update every 1.5 seconds
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center and radius
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - 3 # Leave some margin
        
        self.draw_outer_ring(painter, center_x, center_y, radius)
        self.draw_inner_background(painter, center_x, center_y, radius)
        self.draw_scale_and_labels(painter, center_x, center_y, radius)
        self.draw_needle(painter, center_x, center_y, radius)
        self.draw_center_hub(painter, center_x, center_y, radius)
        self.draw_digital_display(painter, center_x, center_y, radius)
        self.draw_title(painter, center_x, center_y, radius)
        
    def draw_outer_ring(self, painter, center_x, center_y, radius):
        # Create pulsating outer ring
        current_time = QTime.currentTime()
        pulse_factor = 0.05 * (1 + math.sin(current_time.msecsSinceStartOfDay() / 1000))
        
        # Draw outer glowing rings
        for i in range(3):
            ring_radius = radius * (1.02 + i * 0.012 + pulse_factor * 0.01)
            outer_ring_rect = QRectF(
                center_x - ring_radius, 
                center_y - ring_radius, 
                2 * ring_radius, 
                2 * ring_radius
            )
            
            alpha = 100 - i * 30
            ring_gradient = QRadialGradient(center_x, center_y, ring_radius)
            ring_gradient.setColorAt(0.85, QColor(15, 35, 75, 0))
            ring_gradient.setColorAt(0.95, QColor(0, 170, 255, alpha))
            ring_gradient.setColorAt(1.0, QColor(0, 238, 255, 0))
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(ring_gradient))
            painter.drawEllipse(outer_ring_rect)
        
        # Main outer ring
        outer_ring_rect = QRectF(
            center_x - radius, 
            center_y - radius, 
            2 * radius, 
            2 * radius
        )
        
        ring_gradient = QRadialGradient(center_x, center_y, radius)
        ring_gradient.setColorAt(0.8, QColor(15, 35, 75))
        ring_gradient.setColorAt(0.9, QColor(0, 170, 255))
        ring_gradient.setColorAt(1.0, QColor(0, 238, 255))
        
        painter.setPen(QPen(QColor(0, 200, 255), 1.5))
        painter.setBrush(QBrush(ring_gradient))
        painter.drawEllipse(outer_ring_rect)
    
    def draw_inner_background(self, painter, center_x, center_y, radius):
        inner_radius = radius * 0.88
        inner_rect = QRectF(
            center_x - inner_radius, 
            center_y - inner_radius, 
            2 * inner_radius, 
            2 * inner_radius
        )
        
        # More dramatic gradient for the inner background
        inner_gradient = QRadialGradient(center_x, center_y, inner_radius)
        inner_gradient.setColorAt(0.0, QColor(8, 18, 35))
        inner_gradient.setColorAt(0.7, QColor(12, 25, 50))
        inner_gradient.setColorAt(1.0, QColor(18, 35, 70))
        
        painter.setBrush(QBrush(inner_gradient))
        painter.setPen(QPen(QColor(0, 180, 255, 130), 0.5))
        painter.drawEllipse(inner_rect)
        
        # Draw subtle grid pattern
        painter.setPen(QPen(QColor(0, 120, 255, 15), 0.5))
        grid_spacing = inner_radius / 8
        
        # Horizontal grid lines
        for i in range(-8, 9):
            y = center_y + i * grid_spacing
            painter.drawLine(
                QPointF(center_x - inner_radius, y),
                QPointF(center_x + inner_radius, y)
            )
        
        # Vertical grid lines
        for i in range(-8, 9):
            x = center_x + i * grid_spacing
            painter.drawLine(
                QPointF(x, center_y - inner_radius),
                QPointF(x, center_y + inner_radius)
            )
    
    def draw_scale_and_labels(self, painter, center_x, center_y, radius):
        # Set up fonts
        label_font = QFont("Arial", int(radius * 0.1), QFont.Weight.Bold)
        small_font = QFont("Arial", int(radius * 0.8))
        
        painter.setFont(label_font)
        
        # Draw scale markings - now covering a 240-degree arc
        for value in range(0, 101, 5):  # 0 to 100 in steps of 5
            # Map speed value to angle (-120 degrees to 120 degrees)
            angle = self.map_speed_to_angle(value)
            
            # Calculate tick positions
            tick_radius = radius * 0.82
            inner_tick = radius * 0.76 if value % 20 == 0 else radius * 0.78
            
            x1 = center_x + tick_radius * math.sin(math.radians(angle))
            y1 = center_y - tick_radius * math.cos(math.radians(angle))
            x2 = center_x + inner_tick * math.sin(math.radians(angle))
            y2 = center_y - inner_tick * math.cos(math.radians(angle))
            
            # Style based on tick importance
            if value % 20 == 0:  # Major ticks
                painter.setPen(QPen(QColor(220, 220, 220), 2))
            else:  # Minor ticks
                painter.setPen(QPen(QColor(180, 180, 180, 150), 1))
            
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
            # Draw labels for main values
            if value % 20 == 0 or value == 100:
                text_radius = inner_tick - radius * 0.1
                x_text = center_x + text_radius * math.sin(math.radians(angle))
                y_text = center_y - text_radius * math.cos(math.radians(angle))
                
                # Adjust text position for better alignment
                font_metrics = QFontMetrics(label_font)
                text = str(value)
                text_width = font_metrics.horizontalAdvance(text)
                text_height = font_metrics.height()
                
                # Center text around point
                text_rect = QRectF(
                    x_text - text_width/2,
                    y_text - text_height/2,
                    text_width,
                    text_height
                )
                
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        
        # Draw speed zones (low, medium, high)
        painter.setFont(small_font)
        
        # Low speed zone label (at around 20)
        low_angle = self.map_speed_to_angle(20)
        x_low = center_x + radius * 0.5 * math.sin(math.radians(low_angle))
        y_low = center_y - radius * 0.5 * math.cos(math.radians(low_angle))
        
        painter.setPen(QPen(QColor(60, 230, 180), 1))
        painter.drawText(QPointF(x_low, y_low), "")
        
        # Medium speed zone label (at around 50)
        med_angle = self.map_speed_to_angle(50)
        x_med = center_x + radius * 0.5 * math.sin(math.radians(med_angle))
        y_med = center_y - radius * 0.5 * math.cos(math.radians(med_angle))
        
        painter.setPen(QPen(QColor(255, 215, 80), 1))
        painter.drawText(QPointF(x_med, y_med), "")
        
        # High speed zone label (at around 80)
        high_angle = self.map_speed_to_angle(80)
        x_high = center_x + radius * 0.5 * math.sin(math.radians(high_angle))
        y_high = center_y - radius * 0.5 * math.cos(math.radians(high_angle))
        
        painter.setPen(QPen(QColor(255, 120, 80), 1))
        painter.drawText(QPointF(x_high, y_high), "")
    
    def draw_needle(self, painter, center_x, center_y, radius):
        painter.save()
        painter.translate(center_x, center_y)
        
        # Calculate needle angle based on current speed
        needle_angle = self.map_speed_to_angle(self.speed)
        painter.rotate(needle_angle)
        
        # Create needle path
        needle_path = QPainterPath()
        needle_length = radius * 0.75
        needle_width = radius * 0.04
        
        needle_path.moveTo(0, -needle_length)
        needle_path.lineTo(needle_width, 0)
        needle_path.lineTo(-needle_width, 0)
        needle_path.closeSubpath()
        
        # Color gradient based on speed value
        if self.speed < 33:  # Low speed - green
            needle_gradient = QLinearGradient(0, -needle_length, 0, 0)
            needle_gradient.setColorAt(0.0, QColor(60, 255, 180))
            needle_gradient.setColorAt(0.5, QColor(80, 230, 160))
            needle_gradient.setColorAt(1.0, QColor(50, 200, 140))
            painter.setPen(QPen(QColor(100, 255, 200), 1))
        elif self.speed < 66:  # Medium speed - yellow
            needle_gradient = QLinearGradient(0, -needle_length, 0, 0)
            needle_gradient.setColorAt(0.0, QColor(255, 215, 80))
            needle_gradient.setColorAt(0.5, QColor(255, 195, 60))
            needle_gradient.setColorAt(1.0, QColor(230, 175, 40))
            painter.setPen(QPen(QColor(255, 220, 100), 1))
        else:  # High speed - red
            needle_gradient = QLinearGradient(0, -needle_length, 0, 0)
            needle_gradient.setColorAt(0.0, QColor(255, 90, 60))
            needle_gradient.setColorAt(0.5, QColor(255, 120, 100))
            needle_gradient.setColorAt(1.0, QColor(200, 80, 50))
            painter.setPen(QPen(QColor(255, 140, 120), 1))
        
        painter.setBrush(QBrush(needle_gradient))
        painter.drawPath(needle_path)
        
        # Draw needle shadow for 3D effect
        shadow_path = QPainterPath()
        shadow_offset = needle_width * 0.5
        
        shadow_path.moveTo(shadow_offset, -needle_length + shadow_offset)
        shadow_path.lineTo(needle_width + shadow_offset, shadow_offset)
        shadow_path.lineTo(-needle_width + shadow_offset, shadow_offset)
        shadow_path.closeSubpath()
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawPath(shadow_path)
        
        painter.restore()
    
    def draw_center_hub(self, painter, center_x, center_y, radius):
        # Outer hub
        hub_radius = radius * 0.12
        hub_gradient = QRadialGradient(center_x, center_y, hub_radius)
        hub_gradient.setColorAt(0.0, QColor(180, 180, 180))
        hub_gradient.setColorAt(0.7, QColor(120, 120, 120))
        hub_gradient.setColorAt(1.0, QColor(80, 80, 80))
        
        painter.setPen(QPen(QColor(200, 200, 200), 0.5))
        painter.setBrush(QBrush(hub_gradient))
        painter.drawEllipse(QPointF(center_x, center_y), hub_radius, hub_radius)
        
        # Inner hub
        inner_hub_radius = hub_radius * 0.7
        inner_hub_gradient = QRadialGradient(center_x, center_y, inner_hub_radius)
        inner_hub_gradient.setColorAt(0.0, QColor(40, 40, 40))
        inner_hub_gradient.setColorAt(0.5, QColor(60, 60, 60))
        inner_hub_gradient.setColorAt(1.0, QColor(30, 30, 30))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(inner_hub_gradient))
        painter.drawEllipse(QPointF(center_x, center_y), inner_hub_radius, inner_hub_radius)
        
        # Add highlight to the hub
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
        painter.drawArc(
            QRectF(
                center_x - inner_hub_radius,
                center_y - inner_hub_radius,
                inner_hub_radius * 2,
                inner_hub_radius * 2
            ),
            30 * 16,  # Start angle in 1/16 degrees
            120 * 16  # Span angle in 1/16 degrees
        )
    
    def draw_digital_display(self, painter, center_x, center_y, radius):
        # Digital value display at the bottom
        display_width = radius * 0.8
        display_height = radius * 0.18
        
        display_rect = QRectF(
            center_x - display_width/2,
            center_y + radius * 0.4,
            display_width,
            display_height
        )
        
        # Display background
        display_gradient = QLinearGradient(
            display_rect.left(),
            display_rect.top(),
            display_rect.right(),
            display_rect.bottom()
        )
        display_gradient.setColorAt(0.0, QColor(10, 25, 50))
        display_gradient.setColorAt(1.0, QColor(15, 35, 65))
        
        painter.setPen(QPen(QColor(0, 180, 255), 1))
        painter.setBrush(QBrush(display_gradient))
        painter.drawRoundedRect(display_rect, 8, 8)
        
        # Display value
        value_text = f"{self.speed:.1f}"
            
        display_font = QFont("Arial", int(radius * 0.1), QFont.Weight.Bold)
        painter.setFont(display_font)
        
        # Set color based on value
        if self.speed < 33:
            painter.setPen(QPen(QColor(60, 230, 180), 1))  # Green for low speed
        elif self.speed < 66:
            painter.setPen(QPen(QColor(255, 215, 80), 1))  # Yellow for medium speed
        else:
            painter.setPen(QPen(QColor(255, 120, 80), 1))  # Red for high speed
            
        painter.drawText(display_rect, Qt.AlignmentFlag.AlignCenter, value_text)
    
    def draw_title(self, painter, center_x, center_y, radius):
        # Draw "SPEED" title at the top
        title_font = QFont("Arial", int(radius * 0.1), QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(0, 180, 255), 1))
        
        title_rect = QRectF(
            center_x - radius,
            center_y - radius * 0.4,
            radius * 2,
            radius * 0.15
        )
        
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "SPEED")
        
    def map_speed_to_angle(self, speed_value):
        """Map speed value (0 to 100) to angle on the scale (-120 to 120 degrees)"""
        # Clamp values to our display range
        speed_value = max(0, min(100, speed_value))
        
        # Map the value to angle:
        # 0 = -120 degrees (bottom left)
        # 50 = 0 degrees (top center) 
        # 100 = 120 degrees (bottom right)
        
        # 0 maps to -120, 100 maps to 120, total of 240 degrees
        return -120 + (speed_value * 2.4)  # 2.4 degrees per unit (240/100)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    speed_gauge = EnhancedSpeedIndicator()
    speed_gauge.show()
    sys.exit(app.exec())
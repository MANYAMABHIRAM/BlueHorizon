from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QRadialGradient, QPainterPath, QLinearGradient
import sys
import math

class FuturisticCompass(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Futuristic Compass")
        self.resize(200, 250)
        
        self.direction = 0
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(10)
        
        self.compass_display = CompassDisplay(self)
        self.compass_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.compass_display)
        
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0A1225, stop:1 #182440);
            border: 1px solid #0077AA;
            border-radius: 10px;
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 100, 255, 60))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def set_direction(self, direction):
        """Set compass direction programmatically"""
        direction = direction % 360
        self.direction = direction
        self.compass_display.set_direction(direction)


class CompassDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.direction = 0 
        self.setMinimumSize(30, 60)
        
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(8)
        glow.setColor(QColor(0, 200, 255, 80))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
    
    def set_direction(self, direction):
        self.direction = direction
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - 3     
        outer_ring_rect = QRectF(center_x - radius, center_y - radius, 2 * radius, 2 * radius)
        
        ring_gradient = QRadialGradient(center_x, center_y, radius)
        ring_gradient.setColorAt(0.8, QColor(15, 35, 75))
        ring_gradient.setColorAt(0.9, QColor(0, 170, 255))
        ring_gradient.setColorAt(1.0, QColor(0, 238, 255))
        
        painter.setPen(QPen(QColor(0, 200, 255), 1))
        painter.setBrush(QBrush(ring_gradient))
        painter.drawEllipse(outer_ring_rect)
        
        inner_radius = radius * 0.85
        inner_rect = QRectF(center_x - inner_radius, center_y - inner_radius, 2 * inner_radius, 2 * inner_radius)
        
        inner_gradient = QRadialGradient(center_x, center_y, inner_radius)
        inner_gradient.setColorAt(0.0, QColor(10, 20, 40))
        inner_gradient.setColorAt(0.7, QColor(15, 30, 60))
        inner_gradient.setColorAt(1.0, QColor(20, 40, 80))
        
        painter.setBrush(QBrush(inner_gradient))
        painter.drawEllipse(inner_rect)
        
        painter.setPen(QPen(QColor(0, 219, 255), 1))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        cardinal_points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        for i, point in enumerate(cardinal_points):
            angle = i * 45
            point_radius = radius * 0.7
            x = center_x + point_radius * math.sin(math.radians(angle))
            y = center_y - point_radius * math.cos(math.radians(angle))
            
            if i % 2 == 0: 
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.setPen(QPen(QColor(0, 238, 255), 2))
            else:
                painter.setFont(QFont("Arial", 8))
                painter.setPen(QPen(QColor(0, 170, 255), 1))
                
            rect = QRectF(x - 10, y - 10, 20, 20)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, point)
        
        tick_radius = radius * 0.80
        for i in range(0, 360, 5):
            if i % 45 != 0:
                angle = i
                inner_tick = radius * 0.75 if i % 15 == 0 else radius * 0.78
                
                x1 = center_x + tick_radius * math.sin(math.radians(angle))
                y1 = center_y - tick_radius * math.cos(math.radians(angle))
                x2 = center_x + inner_tick * math.sin(math.radians(angle))
                y2 = center_y - inner_tick * math.cos(math.radians(angle))
                
                if i % 15 == 0:
                    painter.setPen(QPen(QColor(0, 219, 255), 1.5))
                else:
                    painter.setPen(QPen(QColor(0, 170, 255, 150), 1))
                
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.direction)
        
        needle_path = QPainterPath()
        needle_length = radius * 0.6
        needle_width = radius * 0.1
        
        needle_path.moveTo(0, -needle_length)
        needle_path.lineTo(needle_width/2, 0)
        needle_path.lineTo(-needle_width/2, 0)
        needle_path.closeSubpath()
        
        north_gradient = QLinearGradient(0, -needle_length, 0, 0)
        north_gradient.setColorAt(0.0, QColor(255, 60, 60))
        north_gradient.setColorAt(0.5, QColor(255, 100, 100))
        north_gradient.setColorAt(1.0, QColor(200, 50, 50))
        
        painter.setBrush(QBrush(north_gradient))
        painter.setPen(QPen(QColor(255, 100, 100), 1))
        painter.drawPath(needle_path)
        
        needle_path = QPainterPath()
        needle_path.moveTo(0, needle_length * 0.6)
        needle_path.lineTo(needle_width/2, 0)
        needle_path.lineTo(-needle_width/2, 0)
        needle_path.closeSubpath()
        
        south_gradient = QLinearGradient(0, 0, 0, needle_length * 0.6)
        south_gradient.setColorAt(0.0, QColor(60, 120, 255))
        south_gradient.setColorAt(0.5, QColor(100, 150, 255))
        south_gradient.setColorAt(1.0, QColor(50, 100, 200))
        
        painter.setBrush(QBrush(south_gradient))
        painter.setPen(QPen(QColor(100, 150, 255), 1))
        painter.drawPath(needle_path)
        
        painter.setPen(Qt.PenStyle.NoPen)
        center_gradient = QRadialGradient(0, 0, radius * 0.08)
        center_gradient.setColorAt(0.0, QColor(200, 200, 200))
        center_gradient.setColorAt(0.5, QColor(150, 150, 150))
        center_gradient.setColorAt(1.0, QColor(100, 100, 100))
        
        painter.setBrush(QBrush(center_gradient))
        painter.drawEllipse(QPointF(0, 0), radius * 0.08, radius * 0.08)
        
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        painter.drawArc(QRectF(-radius * 0.08, -radius * 0.08, radius * 0.16, radius * 0.16), 30 * 16, 120 * 16)
        
        painter.restore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    compass = FuturisticCompass()
    # Set a default direction if needed
    compass.set_direction(45)
    compass.show()
    sys.exit(app.exec())
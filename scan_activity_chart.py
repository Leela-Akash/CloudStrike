import pyqtgraph as pg
from PyQt6.QtGui import QColor
from datetime import datetime, timedelta

class ScanActivityChart(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        
        # Chart data: last 7 days
        self.chart_data = [
            {'date': 'Mon', 'critical': 12, 'high': 18, 'medium': 25},
            {'date': 'Tue', 'critical': 8, 'high': 22, 'medium': 30},
            {'date': 'Wed', 'critical': 15, 'high': 20, 'medium': 28},
            {'date': 'Thu', 'critical': 10, 'high': 16, 'medium': 22},
            {'date': 'Fri', 'critical': 18, 'high': 24, 'medium': 32},
            {'date': 'Sat', 'critical': 6, 'high': 12, 'medium': 18},
            {'date': 'Sun', 'critical': 14, 'high': 19, 'medium': 26},
        ]
        
        self.setup_chart()
    
    def setup_chart(self):
        self.setBackground('#0f0a08')
        self.showGrid(x=False, y=True, alpha=0.1)
        
        # Style axes
        axis_color = '#8a7a6a'
        axis_pen = pg.mkPen(color=axis_color, width=1)
        
        self.getAxis('bottom').setPen(axis_pen)
        self.getAxis('left').setPen(axis_pen)
        self.getAxis('bottom').setTextPen(axis_color)
        self.getAxis('left').setTextPen(axis_color)
        
        # Set labels
        self.setLabel('left', 'Findings', color=axis_color)
        self.setLabel('bottom', 'Day', color=axis_color)
        
        # X axis ticks
        x_labels = [(i, day['date']) for i, day in enumerate(self.chart_data)]
        self.getAxis('bottom').setTicks([x_labels])
        
        # Plot stacked bars
        x = list(range(len(self.chart_data)))
        width = 0.6
        
        # Critical (bottom layer)
        critical = [day['critical'] for day in self.chart_data]
        bar1 = pg.BarGraphItem(x=x, height=critical, width=width, brush='#e63c00', pen=None)
        self.addItem(bar1)
        
        # High (middle layer)
        high = [day['high'] for day in self.chart_data]
        high_offset = critical
        bar2 = pg.BarGraphItem(x=x, height=high, width=width, brush='#ff4500', pen=None, y0=high_offset)
        self.addItem(bar2)
        
        # Medium (top layer)
        medium = [day['medium'] for day in self.chart_data]
        medium_offset = [critical[i] + high[i] for i in range(len(x))]
        bar3 = pg.BarGraphItem(x=x, height=medium, width=width, brush='#ff6b35', pen=None, y0=medium_offset)
        self.addItem(bar3)
        
        # Set range
        self.setXRange(-0.5, len(x) - 0.5)
        max_height = max([c + h + m for c, h, m in zip(critical, high, medium)])
        self.setYRange(0, max_height * 1.1)

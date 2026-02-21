import pyqtgraph as pg
from PyQt6.QtGui import QColor
from datetime import datetime, timedelta
import numpy as np

class ScanActivityChart(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.setup_chart()
        self.refresh_chart()
    
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
    
    def refresh_chart(self):
        """Load real scan history and update chart"""
        try:
            from settings_manager import get_scan_history_7days
            history = get_scan_history_7days()

            days = []
            critical_vals = []
            high_vals = []
            medium_vals = []

            for date_str, data in history.items():
                # Show day name (Mon, Tue etc)
                day_name = datetime.strptime(
                    date_str, '%Y-%m-%d'
                ).strftime('%a')
                days.append(day_name)
                critical_vals.append(data['critical'])
                high_vals.append(data['high'])
                medium_vals.append(data['medium'])

            # Update chart with real data
            self.update_chart(days, critical_vals, high_vals, medium_vals)

        except Exception as e:
            import logging
            logging.error(f"Chart refresh failed: {e}")
    
    def update_chart(self, days, critical, high, medium):
        """Update the pyqtgraph bars with new data"""
        self.clear()
        
        if not days:
            return
        
        x = np.arange(len(days))
        width = 0.6
        
        # Stacked bars
        bar_medium = pg.BarGraphItem(
            x=x, height=medium,
            width=width, brush='#ff6b35', pen=None
        )
        bar_high = pg.BarGraphItem(
            x=x,
            height=high,
            width=width,
            brush='#ff4500',
            pen=None,
            y0=medium
        )
        bar_critical = pg.BarGraphItem(
            x=x,
            height=critical,
            width=width,
            brush='#e63c00',
            pen=None,
            y0=[m+h for m,h in zip(medium, high)]
        )
        self.addItem(bar_medium)
        self.addItem(bar_high)
        self.addItem(bar_critical)

        # Update x axis labels
        ticks = [(i, days[i]) for i in range(len(days))]
        self.getAxis('bottom').setTicks([ticks])
        
        # Set range
        self.setXRange(-0.5, len(x) - 0.5)
        max_height = max([c + h + m for c, h, m in zip(critical, high, medium)]) if critical else 10
        self.setYRange(0, max_height * 1.1 if max_height > 0 else 10)

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QTextEdit
from PyQt6.QtCore import Qt

class FindingDetailPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        self.title_label = QLabel("FINDING DETAILS")
        self.title_label.setObjectName("panelTitle")
        layout.addWidget(self.title_label)
        
        scroll = QScrollArea()
        scroll.setObjectName("activityScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def load(self, data):
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new content
        for key, value in data.items():
            if key in ['severity', 'finding', 'resource', 'description', 'fix']:
                label = QLabel(key.upper())
                label.setObjectName("detailLabel")
                self.content_layout.addWidget(label)
                
                if key == 'fix':
                    text = QTextEdit()
                    text.setObjectName("codeBlock")
                    text.setPlainText(value)
                    text.setReadOnly(True)
                    text.setMaximumHeight(150)
                    self.content_layout.addWidget(text)
                else:
                    value_label = QLabel(str(value))
                    value_label.setObjectName("detailValue")
                    value_label.setWordWrap(True)
                    self.content_layout.addWidget(value_label)
        
        self.content_layout.addStretch()

class IncidentDetailPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        self.title_label = QLabel("INCIDENT LOG")
        self.title_label.setObjectName("panelTitle")
        layout.addWidget(self.title_label)
        
        scroll = QScrollArea()
        scroll.setObjectName("activityScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def load(self, data):
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add incident name
        name_label = QLabel(data.get('name', 'Unknown Incident'))
        name_label.setObjectName("detailValue")
        name_label.setWordWrap(True)
        self.content_layout.addWidget(name_label)
        
        # Add steps
        for step in data.get('steps', []):
            step_frame = QFrame()
            step_frame.setObjectName("activityItem")
            step_layout = QVBoxLayout(step_frame)
            step_layout.setContentsMargins(8, 6, 8, 6)
            
            step_label = QLabel(step)
            step_label.setObjectName("activityTitle")
            step_label.setWordWrap(True)
            step_layout.addWidget(step_label)
            
            self.content_layout.addWidget(step_frame)
        
        self.content_layout.addStretch()

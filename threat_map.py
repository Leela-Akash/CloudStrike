from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl
import tempfile

class ThreatMap(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0f0a08; border: none;")
        
        self.regions = [
            {"name": "us-east-1",      "lat": 37.7,  "lon": -78.0,  "severity": "critical", "findings": 12},
            {"name": "eu-west-1",      "lat": 53.3,  "lon": -6.2,   "severity": "high",     "findings": 7},
            {"name": "ap-south-1",     "lat": 19.0,  "lon": 72.8,   "severity": "high",     "findings": 5},
            {"name": "us-west-2",      "lat": 45.5,  "lon": -122.6, "severity": "medium",   "findings": 3},
            {"name": "ap-southeast-1", "lat": 1.3,   "lon": 103.8,  "severity": "critical", "findings": 9},
        ]
        
        # Enable remote content access
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        
        self.load_map()
    
    def update_with_findings(self, findings):
        """Called after scan — updates map dots with real finding data"""
        region_data = {}
        for f in findings:
            region = f.get('region', 'global')
            if region == 'global':
                continue
            if region not in region_data:
                region_data[region] = {'count': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            region_data[region]['count'] += 1
            sev = f.get('severity', 'LOW').lower()
            region_data[region][sev] = region_data[region].get(sev, 0) + 1
        
        def get_color(data):
            if data['critical'] > 0:
                return '#ff0000'
            elif data['high'] > 0:
                return '#ff4500'
            elif data['medium'] > 0:
                return '#ff6b35'
            else:
                return '#888888'
        
        js_updates = []
        for region, data in region_data.items():
            color = get_color(data)
            count = data['count']
            label = f"{region}<br>Findings: {count}<br>Critical: {data['critical']}<br>High: {data['high']}"
            js_updates.append(f"updateMarker('{region}', '{color}', {count}, '{label}');")
        
        if js_updates:
            js = '\n'.join(js_updates)
            self.page().runJavaScript(js)
    
    def load_map(self):
        markers_js = ""
        for r in self.regions:
            color = {"critical": "#ff2200", "high": "#ff6600", "medium": "#cc8800"}.get(r["severity"], "#888")
            markers_js += f"""
        addMarker('{r['name']}', {r['lat']}, {r['lon']}, '{color}', '<b>{r["name"]}</b><br>Findings: {r["findings"]}<br>Severity: {r["severity"].upper()}', {r['findings']});
        """
        
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; }}
  html, body, #map {{ width:100%; height:100%; background:#150e0a; }}
  .leaflet-container {{ background:#150e0a !important; }}
  .custom-tooltip {{
    background:#1a0f0a; color:#ff6600; border:1px solid #ff4500;
    font-family:Segoe UI; font-size:11px; border-radius:3px;
  }}
  .leaflet-control-attribution {{ display:none; }}
  .leaflet-control-zoom a {{
    background: #1a0f0a !important;
    color: #ff6600 !important;
    border: 1px solid #ff4500 !important;
  }}
  .leaflet-control-zoom a:hover {{
    background: #2a1810 !important;
    color: #ff4500 !important;
  }}
</style>
</head>
<body>
<div id="map"></div>
<script>
  var map = L.map('map', {{
    center: [20, 10],
    zoom: 2,
    minZoom: 2,
    maxZoom: 8,
    zoomControl: true,
    attributionControl: false,
    dragging: true,
    scrollWheelZoom: true,
    maxBounds: [[-90,-180],[90,180]],
    maxBoundsViscosity: 1.0
  }});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    maxZoom: 19
  }}).addTo(map);
  
  var markers = {{}};
  
  function addMarker(id, lat, lng, color, label, count) {{
    var size = Math.min(6 + count, 16);
    var marker = L.circleMarker([lat, lng], {{
      radius: size,
      fillColor: color,
      color: color,
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.7
    }}).addTo(map);
    marker.bindTooltip(label, {{permanent: false, direction: 'top', className: 'custom-tooltip'}});
    markers[id] = marker;
    
    var icon = L.divIcon({{
      className: '',
      html: '<div style="color:#ff6b35;font-size:9px;font-family:monospace;white-space:nowrap;margin-top:4px;">' + id + '</div>',
      iconSize: [80, 20],
      iconAnchor: [40, -8]
    }});
    L.marker([lat, lng], {{icon: icon, interactive: false}}).addTo(map);
  }}
  
  function updateMarker(regionId, color, count, label) {{
    if (markers[regionId]) {{
      var size = Math.min(6 + count, 16);
      markers[regionId].setStyle({{
        fillColor: color,
        color: color,
        radius: size
      }});
      markers[regionId].setTooltipContent(label);
      markers[regionId].setStyle({{opacity: 1, fillOpacity: 1}});
      setTimeout(function() {{
        markers[regionId].setStyle({{opacity: 0.9, fillOpacity: 0.7}});
      }}, 500);
    }} else {{
      var regionCoords = {{
        'us-east-1':     [39.0, -77.5],
        'us-east-2':     [40.4, -82.9],
        'us-west-1':     [37.3, -121.9],
        'us-west-2':     [45.5, -122.6],
        'eu-west-1':     [53.3, -6.2],
        'eu-west-2':     [51.5, -0.1],
        'eu-central-1':  [50.1, 8.7],
        'ap-south-1':    [19.0, 72.8],
        'ap-southeast-1':[1.3, 103.8],
        'ap-northeast-1':[35.7, 139.7],
        'ca-central-1':  [45.5, -73.6],
        'sa-east-1':     [-23.5, -46.6]
      }};
      var coords = regionCoords[regionId];
      if (coords) {{
        addMarker(regionId, coords[0], coords[1], color, label, count);
      }}
    }}
  }}
  
  var defaultRegions = [
    {{id:'us-east-1',  lat:39.0,  lng:-77.5}},
    {{id:'us-west-2',  lat:45.5,  lng:-122.6}},
    {{id:'eu-west-1',  lat:53.3,  lng:-6.2}},
    {{id:'ap-south-1', lat:19.0,  lng:72.8}},
    {{id:'ap-southeast-1', lat:1.3, lng:103.8}}
  ];
  defaultRegions.forEach(function(r) {{
    addMarker(r.id, r.lat, r.lng, '#444444', r.id + '<br>No scan data', 3);
  }});
  
  {markers_js}
</script>
</body>
</html>"""
        
        tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
        tmp.write(html)
        tmp.flush()
        tmp.close()
        
        self.tmp_file = tmp.name
        self.load(QUrl.fromLocalFile(tmp.name))

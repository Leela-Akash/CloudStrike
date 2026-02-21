from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PyQt6.QtCore import QUrl
import tempfile

class ThreatMap(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0f0a08; border: none;")
        
        # Use default profile with full network access
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
        
        # Set user agent to avoid blocks
        profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        self.load_map()
    
    def update_with_findings(self, findings):
        """Called after scan — wait for page to be ready then update"""
        region_data = {}
        for f in findings:
            region = f.get('region', 'global')
            if region == 'global':
                continue
            if region not in region_data:
                region_data[region] = {
                    'count': 0, 'critical': 0,
                    'high': 0, 'medium': 0, 'low': 0
                }
            region_data[region]['count'] += 1
            sev = f.get('severity', 'LOW').lower()
            region_data[region][sev] = region_data[region].get(sev, 0) + 1
        
        def get_color(data):
            if data['critical'] > 0:   return '#ff0000'
            elif data['high'] > 0:     return '#ff4500'
            elif data['medium'] > 0:   return '#ff6b35'
            else:                      return '#888888'
        
        js_lines = []
        for region, data in region_data.items():
            color = get_color(data)
            count = data['count']
            label = (
                f"{region}<br>"
                f"Findings: {count}<br>"
                f"Critical: {data['critical']}<br>"
                f"High: {data['high']}"
            )
            js_lines.append(
                f"updateMarker('{region}', '{color}', {count}, '{label}');"
            )
        
        if js_lines:
            js = '\n'.join(js_lines)
            # Add delay to ensure page JS is ready
            wrapped_js = f"""
setTimeout(function() {{
    try {{
        {js}
    }} catch(e) {{
        console.log('Map update error: ' + e);
    }}
}}, 1000);
"""
            self.page().runJavaScript(wrapped_js)
    
    def load_map(self):
        # Write HTML to temp file directly — no Python string formatting
        html_content = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
  * { margin:0; padding:0; }
  html, body, #map { width:100%; height:100%; background:#150e0a; }
  .leaflet-container { background:#150e0a !important; }
  .custom-tooltip {
    background:#1a0f0a; color:#ff6600; border:1px solid #ff4500;
    font-family:Segoe UI; font-size:11px; border-radius:3px;
  }
  .leaflet-control-attribution { display:none; }
  .leaflet-control-zoom a {
    background: #1a0f0a !important;
    color: #ff6600 !important;
    border: 1px solid #ff4500 !important;
  }
</style>
</head>
<body>
<div id="map"></div>
<script>
  var map = L.map('map', {
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
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  var markers = {};

  function addMarker(id, lat, lng, color, label, count) {
    var size = Math.min(6 + count, 16);
    var marker = L.circleMarker([lat, lng], {
      radius: size,
      fillColor: color,
      color: color,
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.7
    }).addTo(map);
    marker.bindTooltip(label, {
      permanent: false,
      direction: 'top',
      className: 'custom-tooltip'
    });
    markers[id] = marker;

    var icon = L.divIcon({
      className: '',
      html: '<div style="color:#ff6b35;font-size:9px;font-family:monospace;white-space:nowrap;margin-top:4px;">' + id + '</div>',
      iconSize: [80, 20],
      iconAnchor: [40, -8]
    });
    L.marker([lat, lng], {icon: icon, interactive: false}).addTo(map);
  }

  function updateMarker(regionId, color, count, label) {
    if (markers[regionId]) {
      var size = Math.min(6 + count, 16);
      markers[regionId].setStyle({
        fillColor: color,
        color: color,
        radius: size
      });
      markers[regionId].setTooltipContent(label);
      setTimeout(function() {
        markers[regionId].setStyle({opacity: 0.9, fillOpacity: 0.7});
      }, 500);
    } else {
      var regionCoords = {
        // AWS Regions
        'us-east-1':      [39.0, -77.5],
        'us-east-2':      [40.4, -82.9],
        'us-west-1':      [37.3, -121.9],
        'us-west-2':      [45.5, -122.6],
        'eu-west-1':      [53.3, -6.2],
        'eu-west-2':      [51.5, -0.1],
        'eu-central-1':   [50.1, 8.7],
        'ap-south-1':     [19.0, 72.8],
        'ap-southeast-1': [1.3, 103.8],
        'ap-northeast-1': [35.7, 139.7],
        'ca-central-1':   [45.5, -73.6],
        'sa-east-1':      [-23.5, -46.6],
        // Azure Regions
        'eastus':         [37.3, -79.8],
        'eastus2':        [36.6, -78.3],
        'westus':         [37.7, -122.4],
        'westus2':        [47.2, -119.8],
        'westeurope':     [52.3, 4.9],
        'northeurope':    [53.3, -6.2],
        'southeastasia':  [1.3, 103.8],
        'eastasia':       [22.3, 114.2],
        'australiaeast':  [-33.8, 151.2],
        'brazilsouth':    [-23.5, -46.6],
        'canadacentral':  [43.7, -79.4],
        'centralindia':   [18.5, 73.9],
        'japaneast':      [35.7, 139.7],
        'uksouth':        [51.5, -0.1],
        // GCP Regions
        'us-central1':    [41.2, -95.9],
        'us-east1':       [33.1, -80.0],
        'us-east4':       [39.0, -77.5],
        'us-west1':       [45.5, -122.6],
        'us-west2':       [34.0, -118.2],
        'europe-west1':   [50.4, 3.8],
        'europe-west2':   [51.5, -0.1],
        'europe-west3':   [50.1, 8.7],
        'asia-south1':    [19.0, 72.8],
        'asia-southeast1':[1.3, 103.8],
        'asia-northeast1':[35.7, 139.7],
        'australia-southeast1':[-33.8, 151.2],
        'southamerica-east1':[-23.5, -46.6],
        // Generic fallbacks
        'global':         [20.0, 10.0],
        'us':             [39.0, -95.0]
      };
      var coords = regionCoords[regionId];
      if (coords) {
        addMarker(regionId, coords[0], coords[1], color, label, count);
      }
    }
  }

  // Default grey markers — updated after real scan
  var defaultRegions = [
    {id:'us-east-1',      lat:39.0, lng:-77.5},
    {id:'us-west-2',      lat:45.5, lng:-122.6},
    {id:'eu-west-1',      lat:53.3, lng:-6.2},
    {id:'ap-south-1',     lat:19.0, lng:72.8},
    {id:'ap-southeast-1', lat:1.3,  lng:103.8}
  ];
  defaultRegions.forEach(function(r) {
    addMarker(r.id, r.lat, r.lng, '#444444', r.id + '<br>No scan data', 3);
  });
</script>
</body>
</html>'''

        tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
        tmp.write(html_content)
        tmp.flush()
        tmp.close()
        self.tmp_file = tmp.name
        self.load(QUrl.fromLocalFile(tmp.name))

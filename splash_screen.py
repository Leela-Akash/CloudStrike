from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, QTimer, pyqtSignal, Qt
import tempfile, os

SPLASH_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:100%; height:100%; background:#020100; font-family:'Share Tech Mono',monospace; overflow:hidden; }

body::after {
  content:''; position:fixed; inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.08) 2px,rgba(0,0,0,0.08) 4px);
  pointer-events:none; z-index:999;
}

/* STAGE A */
#stageA {
  position:fixed; inset:0;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  background:#020503;
  z-index:10;
  transition:opacity 1s ease;
}
#stageA.fade-out { opacity:0; pointer-events:none; }

.terminal-window {
  width:560px;
  border:1px solid #1a3a1a;
  border-radius:8px;
  overflow:hidden;
  box-shadow:0 0 40px rgba(0,80,0,0.2),0 0 80px rgba(0,0,0,0.8);
}
.terminal-titlebar {
  background:#0d1a0d; padding:10px 14px;
  display:flex; align-items:center; gap:8px;
  border-bottom:1px solid #1a3a1a;
}
.tdot{width:11px;height:11px;border-radius:50%;}
.td1{background:#ff5f57;}.td2{background:#febc2e;}.td3{background:#28c840;}
.terminal-title-text{margin-left:8px;font-size:11px;color:#3a6a3a;letter-spacing:2px;}
.terminal-body{background:#020a02;padding:20px 24px 24px;min-height:220px;}
.boot-header{font-size:13px;color:#ff4500;letter-spacing:2px;margin-bottom:6px;opacity:0;animation:fadein 0.3s ease 0.3s forwards;}
.boot-sub{font-size:10px;color:#2a5a2a;letter-spacing:1px;margin-bottom:18px;opacity:0;animation:fadein 0.3s ease 0.6s forwards;}
@keyframes fadein{to{opacity:1}}
.boot-line{display:flex;align-items:center;gap:10px;font-size:12px;margin-bottom:8px;opacity:0;transform:translateX(-8px);transition:opacity 0.4s ease,transform 0.4s ease;}
.boot-line.show{opacity:1;transform:translateX(0);}
.bl-arrow{color:#ff4500;}.bl-text{color:#7a9a7a;flex:1;}.bl-status{font-size:10px;letter-spacing:1px;}
.ok{color:#28c840;}.warn{color:#febc2e;}
.boot-cursor{display:inline-block;width:8px;height:13px;background:#28c840;vertical-align:middle;animation:bcursor 0.7s infinite;}
@keyframes bcursor{0%,100%{opacity:1}50%{opacity:0}}
.final-line{margin-top:14px;font-size:13px;color:#28c840;letter-spacing:3px;opacity:0;transition:opacity 0.6s;}
.final-line.show{opacity:1;}

/* STAGE B */
#stageB {
  position:fixed; inset:0;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  background:radial-gradient(ellipse at center,#0d0500 0%,#020100 70%);
  z-index:9; opacity:0; transition:opacity 1s ease;
}
#stageB.fade-in{opacity:1;}

.radar-wrap{position:relative;width:220px;height:220px;margin-bottom:28px;}
.ring{position:absolute;border-radius:50%;border:1px solid rgba(255,69,0,0.18);top:50%;left:50%;transform:translate(-50%,-50%);}
.rg1{width:55px;height:55px;border-color:rgba(255,69,0,0.5);}
.rg2{width:95px;height:95px;}.rg3{width:145px;height:145px;}.rg4{width:195px;height:195px;}
.crosshair{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;}
.crosshair::before{content:'';position:absolute;width:100%;height:1px;background:rgba(255,69,0,0.15);top:50%;left:0;}
.crosshair::after{content:'';position:absolute;width:1px;height:100%;background:rgba(255,69,0,0.15);left:50%;top:0;}
.sweep{position:absolute;width:110px;height:110px;top:50%;left:50%;transform-origin:0 0;animation:sweeprot 2.5s linear infinite;}
.sweep::before{content:'';position:absolute;width:110px;height:110px;background:conic-gradient(from 0deg,transparent 60%,rgba(255,100,0,0.5) 100%);border-radius:0 110px 0 0;}
@keyframes sweeprot{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
.radar-center-dot{position:absolute;width:8px;height:8px;border-radius:50%;background:#ff4500;top:50%;left:50%;transform:translate(-50%,-50%);box-shadow:0 0 12px #ff4500,0 0 24px #ff450060;}
.blip{position:absolute;border-radius:50%;background:#ff6b35;box-shadow:0 0 8px #ff4500;animation:blippulse 2.5s infinite;}
@keyframes blippulse{0%,100%{opacity:0;transform:scale(0.5);}30%{opacity:1;transform:scale(1);}60%{opacity:0.4;transform:scale(1);}}
.radar-logo{font-family:'Orbitron',sans-serif;font-weight:900;font-size:34px;color:#ff4500;letter-spacing:6px;text-shadow:0 0 30px #ff450060;margin-bottom:6px;}
.radar-logo span{color:#ff6b35;}
.radar-tagline{font-size:10px;letter-spacing:4px;color:#ff450060;margin-bottom:20px;}
.progress-wrap{width:300px;}
.progress-labels{display:flex;justify-content:space-between;font-size:10px;color:#ff450060;letter-spacing:1px;margin-bottom:6px;}
.progress-pct{color:#ff6b35;font-size:12px;}
.progress-bar{width:300px;height:3px;background:#1a0a05;border-radius:2px;overflow:hidden;}
.progress-fill{height:100%;width:0%;background:linear-gradient(90deg,#ff4500,#ff6b35);box-shadow:0 0 8px #ff450080;transition:width 0.1s linear;}

#transitionOverlay{position:fixed;inset:0;background:#020100;z-index:20;opacity:0;pointer-events:none;transition:opacity 0.5s;}
#transitionOverlay.show{opacity:1;}
</style>
</head>
<body>
<div id="transitionOverlay"></div>

<div id="stageA">
  <div class="terminal-window">
    <div class="terminal-titlebar">
      <div class="tdot td1"></div><div class="tdot td2"></div><div class="tdot td3"></div>
      <span class="terminal-title-text">CLOUDSTRIKE — SYSTEM BOOT</span>
    </div>
    <div class="terminal-body">
      <div class="boot-header">CLOUDSTRIKE v1.0</div>
      <div class="boot-sub">// AUTOMATED CLOUD PENTESTING & SECURITY AUDITOR</div>
      <div class="boot-line" id="bl0"><span class="bl-arrow">›</span><span class="bl-text">Initializing core security engine...</span><span class="bl-status ok">✓ LOADED</span></div>
      <div class="boot-line" id="bl1"><span class="bl-arrow">›</span><span class="bl-text">Loading AWS / Azure / GCP SDK modules...</span><span class="bl-status ok">✓ READY</span></div>
      <div class="boot-line" id="bl2"><span class="bl-arrow">›</span><span class="bl-text">Arming attack simulation chains...</span><span class="bl-status ok">✓ ARMED</span></div>
      <div class="boot-line" id="bl3"><span class="bl-arrow">›</span><span class="bl-text">Loading CIS compliance benchmarks...</span><span class="bl-status ok">✓ OK</span></div>
      <div class="boot-line" id="bl4"><span class="bl-arrow">›</span><span class="bl-text">Scanning threat intelligence feeds...</span><span class="bl-status ok">✓ SYNCED</span></div>
      <div class="boot-line" id="bl5"><span class="bl-arrow">›</span><span class="bl-text">Checking vault credentials...</span><span class="bl-status warn">! NEW USER DETECTED</span></div>
      <div class="boot-line" id="bl6"><span class="bl-arrow">›</span><span class="bl-text">Launching radar interface <span class="boot-cursor"></span></span></div>
      <div class="final-line" id="finalLine">██ ALL SYSTEMS OPERATIONAL — LAUNCHING...</div>
    </div>
  </div>
</div>

<div id="stageB">
  <div class="radar-wrap">
    <div class="ring rg1"></div><div class="ring rg2"></div><div class="ring rg3"></div><div class="ring rg4"></div>
    <div class="crosshair"></div>
    <div class="sweep"></div>
    <div class="radar-center-dot"></div>
    <div class="blip" style="width:7px;height:7px;top:34%;left:22%;animation-delay:0.2s"></div>
    <div class="blip" style="width:9px;height:9px;top:48%;left:62%;animation-delay:0.9s"></div>
    <div class="blip" style="width:7px;height:7px;top:65%;left:38%;animation-delay:1.5s"></div>
    <div class="blip" style="width:8px;height:8px;top:28%;left:55%;animation-delay:0.5s"></div>
  </div>
  <div class="radar-logo">CLOUD<span>STRIKE</span></div>
  <div class="radar-tagline">SCANNING CLOUD ENVIRONMENT</div>
  <div class="progress-wrap">
    <div class="progress-labels"><span>INITIALIZING SCAN</span><span class="progress-pct" id="pct">0%</span></div>
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
  </div>
</div>

<script>
var progressInterval = null;

function startSequence() {
  var lines = document.querySelectorAll('.boot-line');
  lines.forEach(function(line, i) {
    setTimeout(function(){ line.classList.add('show'); }, 600 + i * 500);
  });
  var totalA = 600 + lines.length * 500;
  setTimeout(function(){ document.getElementById('finalLine').classList.add('show'); }, totalA + 200);
  setTimeout(function(){
    var overlay = document.getElementById('transitionOverlay');
    overlay.classList.add('show');
    setTimeout(function(){
      document.getElementById('stageA').classList.add('fade-out');
      document.getElementById('stageB').classList.add('fade-in');
      setTimeout(function(){
        overlay.classList.remove('show');
        startRadar();
      }, 600);
    }, 400);
  }, totalA + 1200);
}

function startRadar() {
  var pct = 0;
  var fill = document.getElementById('progressFill');
  var pctEl = document.getElementById('pct');
  progressInterval = setInterval(function(){
    pct += 1;
    fill.style.width = pct + '%';
    pctEl.textContent = pct + '%';
    if (pct >= 100) {
      clearInterval(progressInterval);
      pctEl.textContent = '100% — READY';
      pctEl.style.color = '#28c840';
      // Python timer handles the close automatically
    }
  }, 30);
}

startSequence();
</script>
</body>
</html>
"""

class SplashScreen(QWebEngineView):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.resize(900, 600)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - 900) // 2,
            (screen.height() - 600) // 2
        )
        
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        # Write HTML to temp file and load
        tmp = tempfile.NamedTemporaryFile(
            suffix='.html', delete=False, mode='w', encoding='utf-8'
        )
        tmp.write(SPLASH_HTML)
        tmp.flush()
        tmp.close()
        self._tmp_path = tmp.name
        self.load(QUrl.fromLocalFile(tmp.name))
        
        # Auto-close after 11 seconds (Stage A + transition + Stage B)
        QTimer.singleShot(11000, self._on_finished)

    def _on_finished(self):
        self.close()
        try:
            os.unlink(self._tmp_path)
        except:
            pass
        self.finished.emit()

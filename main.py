import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="A Dance of Fire and Ice - Professional Engine",
    page_icon="🔥",
    layout="centered"
)

# 스트림릿 테마 커스텀 및 가이드 스타일 정의
st.markdown("""
<style>
    /* 전체 배경: 검은색과 남색 그라데이션 */
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #0d1527 100%);
        color: #ffffff;
    }
    h1 {
        text-align: center;
        background: linear-gradient(135deg, #ff3366 0%, #33ccff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        margin-bottom: 1.2rem;
    }
    
    /* 선택 옵션(Selectbox) 라벨 글자색 흰색으로 변경 */
    div[data-baseweb="select"] label, .stSelectbox label p {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    .guide-container {
        background-color: rgba(17, 24, 39, 0.7);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 0.88rem;
        line-height: 1.5;
        backdrop-filter: blur(4px);
    }
    .guide-title {
        font-weight: bold;
        color: #38bdf8;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .guide-tiles {
        display: flex;
        gap: 12px;
        margin-top: 6px;
        flex-wrap: wrap;
    }
    .tile-badge {
        background-color: #1e293b;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔥 A Dance of Fire and Ice ❄️")

# 게임 설명 가이드 상자
st.markdown("""
<div class="guide-container">
    <div class="guide-title">🎮 게임 이용 안내</div>
    <div>• <b>조작 방법:</b> 행성이 다음 타일에 겹치는 순간 <b>화면을 클릭</b>하거나 <b>스페이스바/아무 키</b>를 누르세요.</div>
    <div>• <b>특수 타일 안내:</b></div>
    <div class="guide-tiles">
        <span class="tile-badge"><b style="color: #ff7733;">🚀 >></b> 가속 (속도 증가 & 유지)</span>
        <span class="tile-badge"><b style="color: #a3e635;">🐢 <<</b> 감속 (속도 감소 & 유지)</span>
        <span class="tile-badge"><b style="color: #c084fc;">🌀 ○</b> 회전 방향 반전</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 난이도 및 모드 설정
col1, col2 = st.columns(2)
with col1:
    speed_option = st.selectbox(
        "🎮 시작 회전 속도 (BPM / 난이도)",
        options=[
            "Easy (BPM 110)", 
            "Normal (BPM 150)", 
            "Hard (BPM 200)", 
            "Insane (BPM 260)",
            "Extreme (BPM 320)",
            "Speed Demon (BPM 400)"
        ],
        index=1
    )

with col2:
    tile_mode_option = st.selectbox(
        "⚡ 속도 타일 모드",
        options=[
            "일반 모드 (속도 변동 없음)",
            "특수 타일 모드 (가속/감속 포함)"
        ],
        index=0  # 기본값: 속도 타일 없는 일반 모드
    )

speed_map = {
    "Easy (BPM 110)": 0.040,
    "Normal (BPM 150)": 0.055,
    "Hard (BPM 200)": 0.075,
    "Insane (BPM 260)": 0.098,
    "Extreme (BPM 320)": 0.125,
    "Speed Demon (BPM 400)": 0.155
}
selected_speed = speed_map[speed_option]
enable_speed_tiles = "true" if tile_mode_option == "특수 타일 모드 (가속/감속 포함)" else "false"

game_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            user-select: none;
            overflow: hidden;
        }}
        #gameContainer {{
            position: relative;
            margin-top: 5px;
        }}
        #gameCanvas {{
            border: 2px solid #1a2332;
            border-radius: 20px;
            background: radial-gradient(circle at center, #0f172a 0%, #060913 100%);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 20px rgba(51, 204, 255, 0.1);
            cursor: pointer;
        }}
        #info {{
            margin-top: 12px;
            text-align: center;
        }}
        .stats {{
            font-size: 19px;
            color: #8395a7;
            letter-spacing: 0.5px;
        }}
        .stats span {{
            color: #f8fafc;
            font-weight: bold;
        }}
        .status {{
            font-size: 24px;
            font-weight: 800;
            margin-top: 6px;
            height: 36px;
            text-shadow: 0 0 10px rgba(255,255,255,0.2);
        }}
        #restartBtn {{
            display: none;
            margin-top: 10px;
            padding: 12px 30px;
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            background: linear-gradient(135deg, #ff3366, #ff527b);
            border: none;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 6px 20px rgba(255, 51, 102, 0.4);
            transition: all 0.2s ease;
        }}
        #restartBtn:hover {{
            transform: translateY(-2px) scale(1.03);
            box-shadow: 0 8px 25px rgba(255, 51, 102, 0.6);
        }}
    </style>
</head>
<body>

<div id="gameContainer">
    <canvas id="gameCanvas" width="680" height="390"></canvas>
</div>

<div id="info">
    <div class="stats">점수: <span id="score">0</span> &nbsp;|&nbsp; 콤보: <span id="combo">0</span> &nbsp;|&nbsp; 최고 콤보: <span id="maxCombo">0</span></div>
    <div id="feedback" class="status" style="color: #38bdf8;">화면을 클릭하거나 스페이스바를 누르세요!</div>
    <button id="restartBtn" onclick="initGame()">🔄 다시 도전하기</button>
</div>

<script>
// Canvas & Context
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const comboEl = document.getElementById('combo');
const maxComboEl = document.getElementById('maxCombo');
const feedbackEl = document.getElementById('feedback');
const restartBtn = document.getElementById('restartBtn');

// Web Audio API
const AudioContext = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;

function initAudio() {{
    if (!audioCtx) {{
        audioCtx = new AudioContext();
    }}
}}

function playSound(type) {{
    if (!audioCtx) return;
    
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    const now = audioCtx.currentTime;

    if (type === 'PERFECT') {{
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.exponentialRampToValueAtTime(1046.50, now + 0.12);
        gain.gain.setValueAtTime(0.3, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
        osc.start(now);
        osc.stop(now + 0.12);
    }} else if (type === 'GREAT') {{
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(440, now);
        gain.gain.setValueAtTime(0.25, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
        osc.start(now);
        osc.stop(now + 0.1);
    }} else if (type === 'MISS') {{
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(150, now);
        osc.frequency.linearRampToValueAtTime(60, now + 0.25);
        gain.gain.setValueAtTime(0.4, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
    }} else if (type === 'BEAT') {{
        osc.type = 'sine';
        osc.frequency.setValueAtTime(220, now);
        gain.gain.setValueAtTime(0.05, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now);
        osc.stop(now + 0.05);
    }}
}}

// 게임 상수 및 설정
const R = 46; 
const TILE_W = 62;
const TILE_H = 36;
const enableSpeedTiles = {enable_speed_tiles}; // 속도 타일 모드 여부

// 객체 데이터 구조
let tiles = [];
let currentTileIdx = 0;
let pivotPos = {{ x: 0, y: 0 }};
let activePos = {{ x: 0, y: 0 }};

// 각도 및 회전 제어
let currentAngle = 0;
let targetAngle = 0;
let rotDirection = 1;
const initialSpeedSetting = {selected_speed};
let speedMultiplier = 1.0;
let baseRotSpeed = initialSpeedSetting;

let activePlanetType = 1; // 0: Red, 1: Blue

// 카메라 & 쉐이크 제어
let camX = 0;
let camY = 0;
const camLerpFactor = 0.09; 
let shakeAmount = 0;
let shakeDuration = 0;

// 점수 및 판정
let score = 0;
let combo = 0;
let maxCombo = 0;
let gameState = "READY";

// 그래픽 파티클
let particles = [];
let planetTrails = [];

function addExplosion(x, y, color) {{
    for (let i = 0; i < 24; i++) {{
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 6 + 2;
        particles.push({{
            x: x,
            y: y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            radius: Math.random() * 4 + 2,
            color: color,
            alpha: 1,
            decay: Math.random() * 0.03 + 0.02
        }});
    }}
}}

function addTrail(x, y, color) {{
    planetTrails.push({{
        x: x,
        y: y,
        radius: 12,
        color: color,
        alpha: 0.6,
        decay: 0.05
    }});
}}

// 맵 생성 알고리즘
function generateComplexMap() {{
    tiles = [];
    let cx = 200;
    let cy = 200;
    
    const possibleDirs = [
        {{ x: 1, y: 0 }},
        {{ x: 1, y: 0 }},
        {{ x: 1, y: 0 }},
        {{ x: 0, y: 1 }},
        {{ x: 0, y: -1 }},
        {{ x: 1, y: 1 }},
        {{ x: 1, y: -1 }}
    ];

    tiles.push({{ x: cx, y: cy, isSwirl: false, speedType: 'normal' }});
    let lastDir = possibleDirs[0];
    let specialTileCooldown = 8; 

    for (let i = 0; i < 250; i++) {{
        let d;
        do {{
            d = possibleDirs[Math.floor(Math.random() * possibleDirs.length)];
        }} while (d.x === -lastDir.x && d.y === -lastDir.y);

        lastDir = d;
        cx += d.x * (2 * R);
        cy += d.y * (2 * R);
        
        const isSwirl = Math.random() < 0.12 && i > 4;
        let speedType = 'normal';

        specialTileCooldown--;

        if (enableSpeedTiles && specialTileCooldown <= 0 && !isSwirl) {{
            const rand = Math.random();
            if (rand < 0.30) {{
                const typeRand = Math.random();
                if (typeRand < 0.60) {{
                    speedType = 'fast';
                }} else {{
                    speedType = 'slow';
                }}
                specialTileCooldown = 8;
            }}
        }}

        tiles.push({{ x: cx, y: cy, isSwirl: isSwirl, speedType: speedType }});
    }}
}}

function initGame() {{
    generateComplexMap();
    
    currentTileIdx = 0;
    score = 0;
    combo = 0;
    maxCombo = 0;
    rotDirection = 1;
    speedMultiplier = 1.0;
    baseRotSpeed = initialSpeedSetting;
    gameState = "READY";
    shakeAmount = 0;
    shakeDuration = 0;
    particles = [];
    planetTrails = [];

    pivotPos = {{ x: tiles[0].x, y: tiles[0].y }};
    camX = pivotPos.x;
    camY = pivotPos.y;
    
    const nextTile = tiles[1];
    const targetDirAngle = Math.atan2(nextTile.y - pivotPos.y, nextTile.x - pivotPos.x);
    
    currentAngle = targetDirAngle - Math.PI;
    targetAngle = targetDirAngle;

    activePlanetType = 1;
    updateActivePos();

    scoreEl.innerText = "0";
    comboEl.innerText = "0";
    maxComboEl.innerText = "0";
    feedbackEl.innerText = "클릭하거나 아무 키나 눌러 시작하세요!";
    feedbackEl.style.color = "#38bdf8";
    restartBtn.style.display = "none";
}}

function updateActivePos() {{
    activePos.x = pivotPos.x + Math.cos(currentAngle) * (2 * R);
    activePos.y = pivotPos.y + Math.sin(currentAngle) * (2 * R);
}}

function update() {{
    if (gameState === "PLAYING") {{
        currentAngle += baseRotSpeed * rotDirection;
        updateActivePos();

        const curColor = activePlanetType === 1 ? '#38bdf8' : '#ff3366';
        addTrail(activePos.x, activePos.y, curColor);

        const passed = rotDirection === 1 
            ? (currentAngle > targetAngle + 0.65) 
            : (currentAngle < targetAngle - 0.65);

        if (passed) {{
            triggerGameOver("시간 초과! (MISS)");
        }}

        if (shakeAmount > 0 && shakeDuration === 0) {{
            shakeAmount *= 0.88;
        }}
    }}

    if (gameState === "GAMEOVER") {{
        if (shakeDuration > 0) {{
            shakeDuration--;
            shakeAmount = (shakeDuration / 120) * 10;
        }} else {{
            shakeAmount = 0;
        }}
    }}
}}

function handleInput() {{
    initAudio();

    if (gameState === "READY") {{
        gameState = "PLAYING";
        feedbackEl.innerText = "START!";
        feedbackEl.style.color = "#4ade80";
        playSound('BEAT');
        return;
    }}

    if (gameState === "GAMEOVER") return;

    const diff = Math.abs(currentAngle - targetAngle);

    if (diff < 0.32) {{
        score += 100 + (combo * 15);
        combo++;
        if (combo > maxCombo) maxCombo = combo;
        
        feedbackEl.innerText = "PERFECT!!";
        feedbackEl.style.color = "#4ade80";
        shakeAmount = 4;
        
        const curColor = activePlanetType === 1 ? '#38bdf8' : '#ff3366';
        addExplosion(activePos.x, activePos.y, curColor);
        playSound('PERFECT');
        
        advanceToNextTile();
    }} else if (diff < 0.58) {{
        score += 50;
        combo++;
        if (combo > maxCombo) maxCombo = combo;
        
        feedbackEl.innerText = "GREAT";
        feedbackEl.style.color = "#facc15";
        shakeAmount = 2;
        playSound('GREAT');
        
        advanceToNextTile();
    }} else {{
        triggerGameOver("타이밍 불일치! (MISS)");
    }}

    scoreEl.innerText = score;
    comboEl.innerText = combo;
    maxComboEl.innerText = maxCombo;
}}

function triggerGameOver(reason) {{
    gameState = "GAMEOVER";
    feedbackEl.innerText = `GAME OVER - ${{reason}}`;
    feedbackEl.style.color = "#f87171";
    
    shakeDuration = 120;
    shakeAmount = 10;
    
    playSound('MISS');
    restartBtn.style.display = "inline-block";
}}

function advanceToNextTile() {{
    currentTileIdx++;
    const nextPivot = tiles[currentTileIdx];
    if (!nextPivot) return;

    if (nextPivot.isSwirl) {{
        rotDirection *= -1;
    }}

    if (enableSpeedTiles) {{
        if (nextPivot.speedType === 'fast') {{
            speedMultiplier *= 1.25;
            if (speedMultiplier > 2.2) speedMultiplier = 2.2;
            feedbackEl.innerText = "⚡ SPEED UP!!";
            feedbackEl.style.color = "#ff7733";
        }} else if (nextPivot.speedType === 'slow') {{
            speedMultiplier *= 0.8;
            if (speedMultiplier < 0.45) speedMultiplier = 0.45;
            feedbackEl.innerText = "🐢 SLOW DOWN..";
            feedbackEl.style.color = "#a3e635";
        }}
    }}

    baseRotSpeed = initialSpeedSetting * speedMultiplier;

    pivotPos = {{ x: nextPivot.x, y: nextPivot.y }};
    activePlanetType = activePlanetType === 0 ? 1 : 0;

    const futureTile = tiles[currentTileIdx + 1];
    if (futureTile) {{
        let nextTargetDir = Math.atan2(futureTile.y - pivotPos.y, futureTile.x - pivotPos.x);
        let angleOffset = currentAngle - targetAngle;

        let diff = nextTargetDir - targetAngle;
        while (diff < -Math.PI) diff += Math.PI * 2;
        while (diff > Math.PI) diff -= Math.PI * 2;

        if (rotDirection === 1) {{
            targetAngle = targetAngle + (diff < 0 ? diff + Math.PI * 2 : diff);
            currentAngle = targetAngle - Math.PI + angleOffset;
        }} else {{
            targetAngle = targetAngle + (diff > 0 ? diff - Math.PI * 2 : diff);
            currentAngle = targetAngle + Math.PI + angleOffset;
        }}
    }}
    updateActivePos();
}}

function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    
    camX += (pivotPos.x - camX) * camLerpFactor;
    camY += (pivotPos.y - camY) * camLerpFactor;

    const shakeX = (Math.random() - 0.5) * shakeAmount;
    const shakeY = (Math.random() - 0.5) * shakeAmount;

    ctx.translate(canvas.width / 2 - camX + shakeX, canvas.height / 2 - camY + shakeY);

    // 1. 타일 연결 선
    ctx.beginPath();
    for (let i = 0; i < tiles.length; i++) {{
        if (i === 0) ctx.moveTo(tiles[i].x, tiles[i].y);
        else ctx.lineTo(tiles[i].x, tiles[i].y);
    }}
    ctx.strokeStyle = "rgba(255, 255, 255, 0.07)";
    ctx.lineWidth = 8;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();

    // 2. 직사각형 타일 렌더링
    for (let i = 0; i < tiles.length; i++) {{
        const t = tiles[i];
        
        ctx.save();
        ctx.translate(t.x, t.y);

        ctx.beginPath();
        ctx.roundRect(-TILE_W / 2, -TILE_H / 2, TILE_W, TILE_H, 8);

        if (i < currentTileIdx) {{
            ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
            ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
        }} else if (i === currentTileIdx + 1) {{
            ctx.fillStyle = "#fbbf24";
            ctx.strokeStyle = "#ffffff";
            ctx.shadowColor = "#fbbf24";
            ctx.shadowBlur = 18;
        }} else if (i === currentTileIdx) {{
            ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
            ctx.strokeStyle = "#ffffff";
        }} else {{
            if (t.speedType === 'fast') {{
                ctx.fillStyle = "#9a3412";
                ctx.strokeStyle = "#ff7733";
            }} else if (t.speedType === 'slow') {{
                ctx.fillStyle = "#3f6212";
                ctx.strokeStyle = "#a3e635";
            }} else {{
                ctx.fillStyle = "#1e293b";
                ctx.strokeStyle = "#334155";
            }}
        }}

        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();

        // Swirl 아이콘
        if (t.isSwirl && i >= currentTileIdx) {{
            ctx.beginPath();
            ctx.arc(0, 0, 8, 0, Math.PI * 2);
            ctx.strokeStyle = "#c084fc";
            ctx.lineWidth = 3;
            ctx.stroke();
        }}

        // 속도 변경 아이콘
        if (i >= currentTileIdx) {{
            if (t.speedType === 'fast') {{
                ctx.fillStyle = "#ffaa00";
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(">>", 0, 0);
            }} else if (t.speedType === 'slow') {{
                ctx.fillStyle = "#bef264";
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText("<<", 0, 0);
            }}
        }}

        ctx.restore();
    }}

    // 3. 잔상 트레일
    for (let i = planetTrails.length - 1; i >= 0; i--) {{
        const pt = planetTrails[i];
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, pt.radius, 0, Math.PI * 2);
        ctx.fillStyle = pt.color;
        ctx.globalAlpha = pt.alpha;
        ctx.fill();
        ctx.globalAlpha = 1.0;

        pt.radius *= 0.94;
        pt.alpha -= pt.decay;
        if (pt.alpha <= 0) planetTrails.splice(i, 1);
    }}

    const redPos = activePlanetType === 1 ? pivotPos : activePos;
    const bluePos = activePlanetType === 1 ? activePos : pivotPos;

    // 4. 행성 축 연결선
    ctx.beginPath();
    ctx.moveTo(redPos.x, redPos.y);
    ctx.lineTo(bluePos.x, bluePos.y);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.6)";
    ctx.lineWidth = 4;
    ctx.stroke();

    // 5. 불 행성
    ctx.beginPath();
    ctx.arc(redPos.x, redPos.y, 14, 0, Math.PI * 2);
    ctx.fillStyle = "#ff3366";
    ctx.shadowColor = "#ff3366";
    ctx.shadowBlur = activePlanetType === 0 ? 20 : 8;
    ctx.fill();

    // 6. 얼음 행성
    ctx.beginPath();
    ctx.arc(bluePos.x, bluePos.y, 14, 0, Math.PI * 2);
    ctx.fillStyle = "#38bdf8";
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = activePlanetType === 1 ? 20 : 8;
    ctx.fill();

    // 7. 폭발 파티클
    for (let i = particles.length - 1; i >= 0; i--) {{
        const p = particles[i];
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
        ctx.globalAlpha = 1.0;

        p.x += p.vx;
        p.y += p.vy;
        p.alpha -= p.decay;
        if (p.alpha <= 0) particles.splice(i, 1);
    }}

    ctx.restore();
}}

function loop() {{
    update();
    draw();
    requestAnimationFrame(loop);
}}

window.addEventListener('keydown', (e) => {{
    if (e.code === 'Space' || e.key !== '') {{
        handleInput();
    }}
}});

canvas.addEventListener('mousedown', handleInput);

initGame();
loop();
</script>
</body>
</html>
"""

components.html(game_html, height=580)

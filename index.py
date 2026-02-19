from flask import Flask, jsonify, render_template_string
import random

app = Flask(__name__)

word_bank = [
    "future", "logic", "focus", "pixel", "syntax", "carbon", "rapid", "shift",
    "binary", "gamma", "vector", "matrix", "input", "output", "proxy", "stream",
    "active", "prompt", "stable", "system", "module", "update", "render", "depth",
    "interface", "variable", "function", "array", "object", "string", "boolean"
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SmoothType Pro</title>
    <style>
        :root {
            --bg: #0e0e0e;
            --main: #00ff88;
            --sub: #333;
            --text: #fff;
            --err: #ff4754;
        }
        body {
            background: var(--bg);
            color: var(--sub);
            font-family: 'JetBrains Mono', monospace;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }

        /* Time Selection */
        #settings {
            display: flex;
            gap: 20px;
            margin-bottom: 40px;
            font-size: 14px;
            letter-spacing: 1px;
        }
        .time-opt { cursor: pointer; transition: 0.2s; }
        .time-opt:hover { color: var(--text); }
        .time-opt.active { color: var(--main); }

        #timer {
            font-size: 24px;
            color: var(--main);
            margin-bottom: 10px;
            font-weight: bold;
        }

        #word-wrapper {
            width: 80%;
            max-width: 900px;
            font-size: 32px;
            line-height: 1.6;
            display: flex;
            flex-wrap: wrap;
            position: relative;
            outline: none;
        }

        .letter {
            position: relative;
            color: var(--sub);
            display: inline-block;
        }
        .correct { color: var(--text); }
        .incorrect { color: var(--err); }

        /* The Animated Cursor */
        #cursor {
            position: absolute;
            width: 2px;
            height: 1.2em;
            background: var(--main);
            transition: transform 0.12s cubic-bezier(0.45, 0.05, 0.55, 0.95);
            box-shadow: 0 0 10px var(--main);
            pointer-events: none;
        }

        #results {
            position: fixed; inset: 0; background: var(--bg);
            display: none; flex-direction: column;
            justify-content: center; align-items: center; z-index: 100;
        }
        .stat-val { font-size: 100px; color: var(--main); font-weight: 900; }
        button {
            background: none; border: 1px solid var(--sub);
            color: var(--sub); padding: 12px 30px; margin-top: 40px;
            cursor: pointer; font-family: inherit;
        }
        button:hover { border-color: var(--main); color: var(--main); }
    </style>
</head>
<body>

<div id="settings">
    <span class="time-opt" onclick="updateTime(15, this)">15</span>
    <span class="time-opt active" onclick="updateTime(30, this)">30</span>
    <span class="time-opt" onclick="updateTime(60, this)">60</span>
    <span class="time-opt" onclick="updateTime(120, this)">120</span>
</div>

<div id="timer">30</div>

<div id="word-wrapper" tabindex="0">
    <div id="cursor"></div>
    <div id="words-content" style="display:flex; flex-wrap:wrap;"></div>
</div>

<div id="results">
    <div id="res-wpm" class="stat-val">0</div>
    <div style="color: var(--sub); letter-spacing: 5px;">WORDS PER MINUTE</div>
    <div id="res-acc" style="color: var(--text); margin-top: 10px;">Acc: 0%</div>
    <button onclick="init()">Restart (Esc)</button>
</div>

<script>
let letters = [];
let cursorIdx = 0;
let testDuration = 30;
let timeLeft = 30;
let timer = null;
let active = false;
let totalTyped = 0;
let errors = 0;

const wordsContent = document.getElementById("words-content");
const cursor = document.getElementById("cursor");
const timerEl = document.getElementById("timer");

async function init() {
    clearInterval(timer);
    active = false;
    cursorIdx = 0;
    totalTyped = 0;
    errors = 0;
    timeLeft = testDuration;
    
    document.getElementById("results").style.display = "none";
    timerEl.innerText = timeLeft;
    
    const res = await fetch('/get-words');
    const words = await res.json();
    
    wordsContent.innerHTML = "";
    letters = [];
    
    words.forEach(word => {
        const wordDiv = document.createElement("div");
        wordDiv.style.marginRight = "16px";
        wordDiv.style.display = "flex";
        
        [...word, " "].forEach(char => {
            const span = document.createElement("span");
            span.className = "letter";
            span.innerHTML = char === " " ? "&nbsp;" : char;
            wordDiv.appendChild(span);
            letters.push(span);
        });
        wordsContent.appendChild(wordDiv);
    });

    // Reset Cursor Position
    setTimeout(moveCursor, 0); 
    document.getElementById("word-wrapper").focus();
}

function updateTime(s, el) {
    testDuration = s;
    document.querySelectorAll('.time-opt').forEach(opt => opt.classList.remove('active'));
    el.classList.add('active');
    init();
}

function moveCursor() {
    const target = letters[cursorIdx];
    if (target) {
        // We use transform instead of left/top for 60fps smoothness
        cursor.style.transform = `translate(${target.offsetLeft}px, ${target.offsetTop}px)`;
    }
}

window.addEventListener("keydown", e => {
    if (e.key === "Escape") init();
    if (timeLeft <= 0) return;

    // Start Timer
    if (!active && e.key.length === 1) {
        active = true;
        timer = setInterval(() => {
            timeLeft--;
            timerEl.innerText = timeLeft;
            if (timeLeft <= 0) finish();
        }, 1000);
    }

    if (e.key === "Backspace") {
        if (cursorIdx > 0) {
            cursorIdx--;
            letters[cursorIdx].className = "letter";
            moveCursor();
        }
    } else if (e.key.length === 1) {
        const expected = letters[cursorIdx].innerText.replace(/\\u00a0/g, " ");
        
        if (e.key === expected) {
            letters[cursorIdx].classList.add("correct");
        } else {
            letters[cursorIdx].classList.add("incorrect");
            errors++;
        }
        
        totalTyped++;
        cursorIdx++;
        
        if (cursorIdx >= letters.length) finish();
        else moveCursor();
    }
});

function finish() {
    clearInterval(timer);
    const elapsedMin = testDuration / 60;
    const wpm = Math.round((totalTyped / 5) / elapsedMin);
    const acc = totalTyped > 0 ? Math.round(((totalTyped - errors) / totalTyped) * 100) : 0;

    document.getElementById("res-wpm").innerText = wpm;
    document.getElementById("res-acc").innerText = `Accuracy: ${acc}%`;
    document.getElementById("results").style.display = "flex";
}

document.addEventListener("click", () => document.getElementById("word-wrapper").focus());
window.onload = init;
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/get-words")
def get_words():
    # Large word set to avoid running out
    return jsonify(random.sample(word_bank * 5, 60))

app = app





   


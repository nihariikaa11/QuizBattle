"""
QUIZ BATTLE  -  TY BBA (CA) Project   (single-file desktop application)

Technologies : Python (backend + SQLite database)  +  HTML, CSS, JavaScript (screens)
Needs        : only Python 3.8 or newer. NO pip install, NO Flask, NO extra folders.

HOW TO RUN
    Windows : double-click this file, or open Command Prompt here and type:  python quiz_battle.py
    Mac/Linux: python3 quiz_battle.py

The program opens its own app window (using Chrome or Edge on your computer).
Close that window to stop the program. The database file "quiz_battle.db" is created
automatically next to this file. Demo login:  demo / demo123

FILE MAP (use Ctrl+F to jump to a section)
    SECTION 1  Question bank (75 questions, 5 categories)
    SECTION 2  Settings
    SECTION 3  Database (SQLite)
    SECTION 4  Game logic and API (what the screens talk to)
    SECTION 5  The screens: HTML + CSS + JavaScript (all 10 screens)
    SECTION 6  Web server and app window launcher
"""
import hashlib
import hmac
import json
import os
import random
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import threading
import webbrowser
from contextlib import closing
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# =============================================================================
# SECTION 1 - QUESTION BANK
# =============================================================================
# Each question: ("Question", "CORRECT answer", "wrong 1", "wrong 2", "wrong 3")
# The correct answer is always written first; the game shuffles the options.
# To add questions, add a new line to the right list.
# key -> display details (the "color" is a CSS class used on the category card)
CATEGORIES = {
    "general":   {"name": "General Knowledge", "icon": "🌍", "color": "c-lavender", "desc": "Everyday facts about India and the world"},
    "science":   {"name": "Science",           "icon": "🔬", "color": "c-mint",     "desc": "Space, the human body, atoms and more"},
    "computers": {"name": "Computers & IT",    "icon": "💻", "color": "c-blue",     "desc": "Hardware, web, databases and coding"},
    "geography": {"name": "Geography",         "icon": "🗺️", "color": "c-peach",    "desc": "Countries, rivers, deserts and capitals"},
    "history":   {"name": "History",           "icon": "🏛️", "color": "c-pink",     "desc": "Leaders, battles and Indian history"},
}

QUESTIONS = {
    "general": {
        "easy": [
            ("How many days are there in a week?", "7", "5", "6", "8"),
            ("Which colour do you get by mixing red and white?", "Pink", "Green", "Brown", "Purple"),
            ("Which animal is called the King of the Jungle?", "Lion", "Tiger", "Elephant", "Bear"),
            ("Which festival is known as the Festival of Lights in India?", "Diwali", "Holi", "Eid", "Navratri"),
            ("What is the national animal of India?", "Tiger", "Lion", "Elephant", "Peacock"),
        ],
        "medium": [
            ("Who wrote the Indian national anthem 'Jana Gana Mana'?", "Rabindranath Tagore", "Bankim Chandra Chatterjee", "Sarojini Naidu", "Mahatma Gandhi"),
            ("What is the currency of Japan?", "Yen", "Won", "Yuan", "Dollar"),
            ("Which Indian city is known as the Pink City?", "Jaipur", "Jodhpur", "Udaipur", "Agra"),
            ("How many players of one team play on the field in cricket?", "11", "9", "10", "12"),
            ("How many states are there in India?", "28", "29", "27", "30"),
        ],
        "hard": [
            ("Who was the first Indian woman to win an Olympic medal?", "Karnam Malleswari", "P. V. Sindhu", "Mary Kom", "Saina Nehwal"),
            ("Who was the first Indian to win the Nobel Prize in Literature?", "Rabindranath Tagore", "R. K. Narayan", "Amartya Sen", "Mother Teresa"),
            ("Which Article of the Indian Constitution abolishes untouchability?", "Article 17", "Article 14", "Article 21", "Article 32"),
            ("In which city is the headquarters of the Reserve Bank of India?", "Mumbai", "New Delhi", "Kolkata", "Chennai"),
            ("Who is known as the Missile Man of India?", "A. P. J. Abdul Kalam", "Vikram Sarabhai", "Homi Bhabha", "C. V. Raman"),
        ],
    },
    "science": {
        "easy": [
            ("Which gas do humans breathe in to stay alive?", "Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"),
            ("Which planet is known as the Red Planet?", "Mars", "Venus", "Jupiter", "Saturn"),
            ("What is the chemical formula of water?", "H2O", "CO2", "O2", "NaCl"),
            ("Which part of a plant makes food using sunlight?", "Leaf", "Root", "Stem", "Flower"),
            ("How many legs does a spider have?", "8", "6", "10", "4"),
        ],
        "medium": [
            ("What is the hardest natural substance on Earth?", "Diamond", "Gold", "Iron", "Quartz"),
            ("Which vitamin do we get from sunlight?", "Vitamin D", "Vitamin C", "Vitamin A", "Vitamin B12"),
            ("What is the centre of an atom called?", "Nucleus", "Electron", "Molecule", "Cell"),
            ("Which is the largest planet in our solar system?", "Jupiter", "Saturn", "Neptune", "Earth"),
            ("At what temperature does water boil at sea level?", "100 °C", "90 °C", "120 °C", "80 °C"),
        ],
        "hard": [
            ("What is the chemical symbol for gold?", "Au", "Ag", "Gd", "Go"),
            ("Which organ of the human body produces insulin?", "Pancreas", "Liver", "Kidney", "Stomach"),
            ("What is the approximate speed of light?", "300,000 km/s", "30,000 km/s", "150,000 km/s", "3,000 km/s"),
            ("Which scientist proposed the theory of relativity?", "Albert Einstein", "Isaac Newton", "Niels Bohr", "Galileo Galilei"),
            ("Which gas is the most abundant in Earth's atmosphere?", "Nitrogen", "Oxygen", "Carbon dioxide", "Argon"),
        ],
    },
    "computers": {
        "easy": [
            ("What does CPU stand for?", "Central Processing Unit", "Central Program Unit", "Computer Power Unit", "Control Process Utility"),
            ("Which device is used to type text into a computer?", "Keyboard", "Monitor", "Speaker", "Printer"),
            ("Which of these is an input device?", "Mouse", "Printer", "Monitor", "Speaker"),
            ("What does WWW stand for?", "World Wide Web", "World Web Wide", "Wide World Web", "Web World Window"),
            ("Which of these is a web browser?", "Google Chrome", "Windows", "Python", "Excel"),
        ],
        "medium": [
            ("Which language is used to style web pages?", "CSS", "HTML", "SQL", "Python"),
            ("What does HTML stand for?", "HyperText Markup Language", "High Text Machine Language", "HyperTool Multi Language", "Home Text Markup Language"),
            ("Which of these is a database system?", "MySQL", "Photoshop", "Notepad", "WhatsApp"),
            ("What is the full form of SQL?", "Structured Query Language", "Simple Query Logic", "Standard Question Language", "Sequential Query List"),
            ("Who created the Python programming language?", "Guido van Rossum", "James Gosling", "Dennis Ritchie", "Bjarne Stroustrup"),
        ],
        "hard": [
            ("Which Python framework powers this Quiz Battle project?", "Flask", "Laravel", "Spring", "Angular"),
            ("What does API stand for?", "Application Programming Interface", "Applied Program Integration", "Automated Process Input", "Application Process Interface"),
            ("Which HTTP status code means 'Not Found'?", "404", "200", "500", "301"),
            ("In databases, what does CRUD stand for?", "Create, Read, Update, Delete", "Copy, Run, Upload, Download", "Create, Run, Undo, Delete", "Connect, Read, Use, Disconnect"),
            ("Which data structure follows the FIFO principle?", "Queue", "Stack", "Tree", "Graph"),
        ],
    },
    "geography": {
        "easy": [
            ("What is the capital of India?", "New Delhi", "Mumbai", "Kolkata", "Chennai"),
            ("Which river is the longest in India?", "Ganga", "Yamuna", "Godavari", "Narmada"),
            ("Which is the largest continent?", "Asia", "Africa", "Europe", "Australia"),
            ("In which direction does the Sun rise?", "East", "West", "North", "South"),
            ("Which is the smallest continent by area?", "Australia", "Europe", "Antarctica", "South America"),
        ],
        "medium": [
            ("Which is the largest desert in India?", "Thar Desert", "Gobi Desert", "Sahara Desert", "Kalahari Desert"),
            ("What is the capital of Australia?", "Canberra", "Sydney", "Melbourne", "Perth"),
            ("Which river is called the Sorrow of Bihar?", "Kosi", "Ganga", "Son", "Gandak"),
            ("Mount Everest lies on the border of Nepal and which country?", "China", "India", "Bhutan", "Pakistan"),
            ("Which Indian state has the longest coastline?", "Gujarat", "Maharashtra", "Tamil Nadu", "Kerala"),
        ],
        "hard": [
            ("Which is the deepest ocean trench in the world?", "Mariana Trench", "Java Trench", "Puerto Rico Trench", "Kuril Trench"),
            ("Which is the smallest country in the world by area?", "Vatican City", "Monaco", "San Marino", "Malta"),
            ("Lake Victoria, the largest lake of its continent, is in which continent?", "Africa", "Asia", "South America", "Europe"),
            ("Which strait separates Asia from North America?", "Bering Strait", "Strait of Gibraltar", "Palk Strait", "Strait of Malacca"),
            ("Which is the largest Indian state by area?", "Rajasthan", "Madhya Pradesh", "Maharashtra", "Uttar Pradesh"),
        ],
    },
    "history": {
        "easy": [
            ("Who was the first Prime Minister of India?", "Jawaharlal Nehru", "Sardar Patel", "Mahatma Gandhi", "Indira Gandhi"),
            ("In which year did India gain independence?", "1947", "1950", "1942", "1935"),
            ("Who is known as the Father of the Nation in India?", "Mahatma Gandhi", "Subhas Chandra Bose", "Bhagat Singh", "Lala Lajpat Rai"),
            ("Which monument in Agra is one of the Seven Wonders of the World?", "Taj Mahal", "Red Fort", "Qutub Minar", "India Gate"),
            ("On which date is Republic Day celebrated in India?", "26 January", "15 August", "2 October", "14 November"),
        ],
        "medium": [
            ("Who was the first President of India?", "Dr. Rajendra Prasad", "Dr. S. Radhakrishnan", "Dr. Zakir Husain", "R. Venkataraman"),
            ("In which year was the Quit India Movement launched?", "1942", "1930", "1919", "1857"),
            ("Who built the Taj Mahal?", "Shah Jahan", "Akbar", "Babur", "Aurangzeb"),
            ("Who was the first woman Prime Minister of India?", "Indira Gandhi", "Sarojini Naidu", "Pratibha Patil", "Sonia Gandhi"),
            ("Which battle of 1757 laid the foundation of British rule in India?", "Battle of Plassey", "Battle of Panipat", "Battle of Buxar", "Battle of Haldighati"),
        ],
        "hard": [
            ("Who founded the Maurya Empire?", "Chandragupta Maurya", "Ashoka", "Bindusara", "Harshavardhana"),
            ("At which place did the Revolt of 1857 begin?", "Meerut", "Delhi", "Kanpur", "Jhansi"),
            ("Who was the first Governor-General of independent India?", "Lord Mountbatten", "C. Rajagopalachari", "Lord Wavell", "Lord Curzon"),
            ("In which year was the Indian Constitution adopted by the Constituent Assembly?", "1949", "1950", "1947", "1951"),
            ("Who founded the Mughal Empire in India after the First Battle of Panipat?", "Babur", "Akbar", "Humayun", "Sher Shah Suri"),
        ],
    },
}

# =============================================================================
# SECTION 2 - SETTINGS
# =============================================================================
if getattr(sys, "frozen", False):          # works when converted to .exe too
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "quiz_battle.db")

QUESTIONS_PER_GAME = 5
AVATARS = ["🦊", "🐼", "🐰", "🐱", "🐻", "🦄", "🐧", "🐸"]
BOTS = [("Luna", "🦋"), ("Milo", "🐯"), ("Coco", "🐨"), ("Pixel", "🤖"), ("Daisy", "🐥")]

# time = seconds per question, points = base points per correct answer,
# bot_accuracy = chance that the computer opponent answers correctly
DIFFICULTIES = {
    "easy":   {"label": "Easy",   "icon": "🌱", "time": 20, "points": 10, "bot_accuracy": 0.45,
               "desc": "Relaxed pace. Great for warming up."},
    "medium": {"label": "Medium", "icon": "🔥", "time": 15, "points": 20, "bot_accuracy": 0.65,
               "desc": "Balanced questions and a smarter rival."},
    "hard":   {"label": "Hard",   "icon": "⚡", "time": 10, "points": 30, "bot_accuracy": 0.85,
               "desc": "Tough questions, short timer, sharp opponent."},
}
TIPS = [
    "Faster correct answers earn bonus points, so don't wait until the last second.",
    "Hard battles give the most points per question.",
    "If time runs out, the question counts as a miss.",
    "Your rank is based on your total points across all battles.",
    "Try a new category to improve your overall accuracy.",
    "Keyboard shortcut: press A, B, C or D (or 1-4) to answer during a battle.",
]

SESSIONS = {}   # login token -> user id
QUIZZES = {}    # login token -> the battle that is currently being played

# =============================================================================
# SECTION 3 - DATABASE (SQLite)
# =============================================================================
def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + "$" + digest.hex()


def check_password(password, stored):
    try:
        salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 100_000)
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


def init_db():
    """Create the tables if they do not exist, and add demo players the first time."""
    with closing(connect()) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
                email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                avatar        TEXT NOT NULL DEFAULT '🦊',
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scores (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                category       TEXT NOT NULL,
                difficulty     TEXT NOT NULL,
                player_score   INTEGER NOT NULL,
                opponent_score INTEGER NOT NULL,
                correct        INTEGER NOT NULL,
                total          INTEGER NOT NULL,
                result         TEXT NOT NULL,
                played_at      TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            seed_demo_data(db)
        db.commit()


def seed_demo_data(db):
    """Sample players so the leaderboard is not empty during your presentation."""
    people = [
        ("demo",  "demo@example.com",  "demo123",     "🦊"),
        ("Aarav", "aarav@example.com", "password123", "🐼"),
        ("Diya",  "diya@example.com",  "password123", "🐰"),
        ("Kabir", "kabir@example.com", "password123", "🐻"),
        ("Meera", "meera@example.com", "password123", "🦄"),
        ("Rohan", "rohan@example.com", "password123", "🐧"),
    ]
    for username, email, password, avatar in people:
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash, avatar, created_at) VALUES (?,?,?,?,?)",
            (username, email, hash_password(password), avatar, datetime.now().strftime("%d %b %Y")))
        for _ in range(2 if username == "demo" else random.randint(4, 8)):
            mine, theirs = random.randint(30, 140), random.randint(30, 140)
            db.execute(
                """INSERT INTO scores (user_id, category, difficulty, player_score, opponent_score,
                   correct, total, result, played_at) VALUES (?,?,?,?,?,?,?,?,?)""",
                (cur.lastrowid, random.choice(list(CATEGORIES)), random.choice(list(DIFFICULTIES)),
                 mine, theirs, random.randint(2, 5), QUESTIONS_PER_GAME,
                 "win" if mine > theirs else "loss" if mine < theirs else "draw",
                 datetime.now().strftime("%d %b %Y, %I:%M %p")))


def user_stats(db, user_id):
    row = db.execute("""
        SELECT COUNT(*)                          AS games,
               COALESCE(SUM(player_score), 0)    AS points,
               COALESCE(MAX(player_score), 0)    AS best,
               COALESCE(SUM(result = 'win'), 0)  AS wins,
               COALESCE(SUM(result = 'loss'), 0) AS losses,
               COALESCE(SUM(result = 'draw'), 0) AS draws,
               COALESCE(SUM(correct), 0)         AS correct,
               COALESCE(SUM(total), 0)           AS total
        FROM scores WHERE user_id = ?""", (user_id,)).fetchone()
    stats = dict(row)
    stats["win_rate"] = round(100 * stats["wins"] / stats["games"]) if stats["games"] else 0
    stats["accuracy"] = round(100 * stats["correct"] / stats["total"]) if stats["total"] else 0
    return stats


def recent_games(db, user_id, limit):
    rows = db.execute("SELECT * FROM scores WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                      (user_id, limit)).fetchall()
    return [dict(r) for r in rows]


def leaderboard_rows(db, category=None):
    sql = """SELECT u.id, u.username, u.avatar,
                    SUM(s.player_score) AS points, COUNT(s.id) AS games, SUM(s.result = 'win') AS wins
             FROM users u JOIN scores s ON s.user_id = u.id"""
    params = []
    if category:
        sql += " WHERE s.category = ?"
        params.append(category)
    sql += " GROUP BY u.id ORDER BY points DESC, wins DESC, u.username ASC"
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def rank_of(user_id, rows):
    for position, row in enumerate(rows, start=1):
        if row["id"] == user_id:
            return position
    return None

# =============================================================================
# SECTION 4 - GAME LOGIC AND API
# Every function receives a Req (who is asking + what they sent) and returns
# (status_code, data). The JavaScript in the screens calls these.
# =============================================================================
class Req:
    def __init__(self, token, user, body, query):
        self.token, self.user, self.body, self.query = token, user, body, query


def public_user(u):
    return {"id": u["id"], "username": u["username"], "email": u["email"],
            "avatar": u["avatar"], "created_at": u["created_at"]}


def api_meta(r):
    return 200, {"categories": CATEGORIES, "difficulties": DIFFICULTIES,
                 "avatars": AVATARS, "per_game": QUESTIONS_PER_GAME}


def api_home(r):
    with closing(connect()) as db:
        return 200, {"players": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                     "games": db.execute("SELECT COUNT(*) FROM scores").fetchone()[0],
                     "categories": len(CATEGORIES)}


def api_signup(r):
    b = r.body
    username = str(b.get("username", "")).strip()
    email = str(b.get("email", "")).strip()
    password = str(b.get("password", ""))
    confirm = str(b.get("confirm", ""))
    avatar = b.get("avatar") if b.get("avatar") in AVATARS else AVATARS[0]
    errors = {}
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
        errors["username"] = "Use 3-20 letters, numbers or underscores."
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]{2,}", email):
        errors["email"] = "Enter a valid email address."
    if len(password) < 6:
        errors["password"] = "Password must be at least 6 characters."
    if confirm != password:
        errors["confirm"] = "Passwords do not match."
    with closing(connect()) as db:
        if not errors:
            if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
                errors["username"] = "That username is already taken."
            if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                errors["email"] = "An account with this email already exists."
        if errors:
            return 400, {"errors": errors}
        db.execute("INSERT INTO users (username, email, password_hash, avatar, created_at) VALUES (?,?,?,?,?)",
                   (username, email, hash_password(password), avatar, datetime.now().strftime("%d %b %Y")))
        db.commit()
    return 200, {"ok": True, "username": username}


def api_login(r):
    identifier = str(r.body.get("identifier", "")).strip()
    password = str(r.body.get("password", ""))
    with closing(connect()) as db:
        user = db.execute("SELECT * FROM users WHERE username = ? OR email = ?",
                          (identifier, identifier)).fetchone()
    if not user or not check_password(password, user["password_hash"]):
        return 400, {"error": "Wrong username/email or password. Please try again."}
    token = secrets.token_hex(16)
    SESSIONS[token] = user["id"]
    return 200, {"token": token, "user": public_user(user)}


def api_logout(r):
    SESSIONS.pop(r.token, None)
    QUIZZES.pop(r.token, None)
    return 200, {"ok": True}


def api_me(r):
    with closing(connect()) as db:
        uid = r.user["id"]
        return 200, {"user": public_user(r.user), "stats": user_stats(db, uid),
                     "rank": rank_of(uid, leaderboard_rows(db)),
                     "recent": recent_games(db, uid, 8), "tip": random.choice(TIPS)}


def api_avatar(r):
    avatar = r.body.get("avatar")
    if avatar not in AVATARS:
        return 400, {"error": "Please pick one of the avatars."}
    with closing(connect()) as db:
        db.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, r.user["id"]))
        db.commit()
    return 200, {"ok": True, "avatar": avatar}


# ---- quiz helpers ----------------------------------------------------------
def build_question(cat, diff, bank_index, perm):
    """The bank stores the correct answer first; 'perm' says where each answer is shown."""
    raw = QUESTIONS[cat][diff][bank_index]
    answers = raw[1:]
    return {"text": raw[0], "options": [answers[p] for p in perm], "correct": perm.index(0)}


def quiz_scores(quiz):
    return (sum(i["points"] for i in quiz["log"]), sum(i["bot_points"] for i in quiz["log"]))


def quiz_payload(r, quiz):
    cfg = DIFFICULTIES[quiz["diff"]]
    mine, theirs = quiz_scores(quiz)
    questions = []
    for bank_index, perm in quiz["qs"]:
        q = build_question(quiz["cat"], quiz["diff"], bank_index, perm)
        questions.append({"text": q["text"], "options": q["options"]})   # answers are NOT sent
    return {"total": len(questions), "time": cfg["time"], "current": len(quiz["log"]),
            "questions": questions, "player_score": mine, "opponent_score": theirs,
            "player": {"name": r.user["username"], "avatar": r.user["avatar"]},
            "opponent": {"name": quiz["bot"][0], "avatar": quiz["bot"][1]},
            "category": CATEGORIES[quiz["cat"]], "difficulty": cfg}


def save_result(user_id, quiz):
    mine, theirs = quiz_scores(quiz)
    result = "win" if mine > theirs else "loss" if mine < theirs else "draw"
    with closing(connect()) as db:
        db.execute(
            """INSERT INTO scores (user_id, category, difficulty, player_score, opponent_score,
               correct, total, result, played_at) VALUES (?,?,?,?,?,?,?,?,?)""",
            (user_id, quiz["cat"], quiz["diff"], mine, theirs,
             sum(1 for i in quiz["log"] if i["correct"]), len(quiz["qs"]), result,
             datetime.now().strftime("%d %b %Y, %I:%M %p")))
        db.commit()
    quiz["saved"] = True


def api_start(r):
    cat, diff = r.body.get("category"), r.body.get("difficulty")
    if cat not in CATEGORIES or diff not in DIFFICULTIES:
        return 400, {"error": "Please choose a category and a level."}
    bank_size = len(QUESTIONS[cat][diff])
    qs = []
    for bank_index in random.sample(range(bank_size), min(QUESTIONS_PER_GAME, bank_size)):
        perm = [0, 1, 2, 3]
        random.shuffle(perm)
        qs.append([bank_index, perm])
    QUIZZES[r.token] = {"cat": cat, "diff": diff, "qs": qs, "log": [],
                        "bot": random.choice(BOTS), "saved": False}
    return 200, quiz_payload(r, QUIZZES[r.token])


def api_quiz(r):
    quiz = QUIZZES.get(r.token)
    if not quiz or quiz["saved"]:
        return 400, {"error": "No active battle."}
    return 200, quiz_payload(r, quiz)


def api_answer(r):
    quiz = QUIZZES.get(r.token)
    if not quiz or quiz["saved"]:
        return 400, {"error": "No active battle."}
    position = len(quiz["log"])
    if r.body.get("index") != position:
        return 409, {"error": "Out of sync."}

    cfg = DIFFICULTIES[quiz["diff"]]
    try:
        choice = int(r.body.get("choice", -1))
        time_left = int(r.body.get("time_left", 0))
    except (TypeError, ValueError):
        choice, time_left = -1, 0
    time_left = max(0, min(time_left, cfg["time"]))

    bank_index, perm = quiz["qs"][position]
    q = build_question(quiz["cat"], quiz["diff"], bank_index, perm)

    correct = (choice == q["correct"])                         # the player
    points = cfg["points"] + time_left if correct else 0       # base + speed bonus

    bot_correct = random.random() < cfg["bot_accuracy"]        # the computer opponent
    bot_time = random.randint(int(cfg["time"] * 0.2), int(cfg["time"] * 0.8))
    bot_points = cfg["points"] + bot_time if bot_correct else 0

    quiz["log"].append({"choice": choice, "correct": correct, "points": points,
                        "bot_correct": bot_correct, "bot_points": bot_points})
    finished = len(quiz["log"]) == len(quiz["qs"])
    if finished:
        save_result(r.user["id"], quiz)
    mine, theirs = quiz_scores(quiz)
    return 200, {"correct": correct, "correct_index": q["correct"], "points": points,
                 "bot_correct": bot_correct, "bot_points": bot_points,
                 "player_score": mine, "opponent_score": theirs, "finished": finished}


def api_results(r):
    quiz = QUIZZES.get(r.token)
    if not quiz or len(quiz["log"]) < len(quiz["qs"]):
        return 400, {"error": "Finish a battle to see your results."}
    review = []
    for (bank_index, perm), item in zip(quiz["qs"], quiz["log"]):
        q = build_question(quiz["cat"], quiz["diff"], bank_index, perm)
        review.append({"text": q["text"], "options": q["options"], "correct_index": q["correct"],
                       "choice": item["choice"], "got_it": item["correct"], "points": item["points"],
                       "bot_correct": item["bot_correct"], "bot_points": item["bot_points"]})
    mine, theirs = quiz_scores(quiz)
    with closing(connect()) as db:
        rank = rank_of(r.user["id"], leaderboard_rows(db))
    return 200, {"review": review, "mine": mine, "theirs": theirs,
                 "outcome": "win" if mine > theirs else "loss" if mine < theirs else "draw",
                 "right": sum(1 for i in quiz["log"] if i["correct"]), "total": len(review),
                 "rank": rank, "category_key": quiz["cat"], "category": CATEGORIES[quiz["cat"]],
                 "difficulty": DIFFICULTIES[quiz["diff"]], "bot": list(quiz["bot"])}


def api_leaderboard(r):
    category = (r.query.get("category") or [""])[0]
    if category not in CATEGORIES:
        category = None
    with closing(connect()) as db:
        rows = leaderboard_rows(db, category)
    return 200, {"rows": rows[:10], "my_rank": rank_of(r.user["id"], rows), "total_players": len(rows)}


# (HTTP method, path) -> (function, login needed?)
ROUTES = {
    ("GET",  "/api/meta"):        (api_meta, False),
    ("GET",  "/api/home"):        (api_home, False),
    ("POST", "/api/signup"):      (api_signup, False),
    ("POST", "/api/login"):       (api_login, False),
    ("POST", "/api/logout"):      (api_logout, False),
    ("GET",  "/api/me"):          (api_me, True),
    ("POST", "/api/avatar"):      (api_avatar, True),
    ("POST", "/api/start"):       (api_start, True),
    ("GET",  "/api/quiz"):        (api_quiz, True),
    ("POST", "/api/answer"):      (api_answer, True),
    ("GET",  "/api/results"):     (api_results, True),
    ("GET",  "/api/leaderboard"): (api_leaderboard, True),
}

# =============================================================================
# SECTION 5 - THE SCREENS (HTML + CSS + JavaScript)
# All 10 screens live in this one page; JavaScript switches between them.
#   1 Welcome   2 Sign up   3 Login   4 Profile   5 Dashboard
#   6 Category  7 Level     8 Battle  9 Results   10 Leaderboard
# =============================================================================
PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quiz Battle</title>
<!-- Fonts load only when you are online; offline the app uses your system fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
/* ==========================================================================
   Quiz Battle - pastel theme
   1. Variables  2. Base  3. Layout & nav  4. Buttons & cards  5. Landing
   6. Forms  7. Dashboard & profile  8. Categories & difficulty
   9. Quiz screen  10. Results  11. Leaderboard  12. Animations  13. Responsive
   ========================================================================== */

/* 1. Variables ------------------------------------------------------------ */
:root {
  --lavender: #dccdf7;  --lavender-d: #a98be0;
  --pink:     #ffd3e4;  --pink-d:     #f58fb5;
  --mint:     #c9f3e0;  --mint-d:     #6fd1a5;
  --peach:    #ffdcc4;  --peach-d:    #f5a974;
  --blue:     #c6e4ff;  --blue-d:     #7dbaf0;
  --cream:    #fff8ee;
  --ink:      #46386e;  --ink-soft:   #766b96;
  --white:    #ffffff;
  --radius:   24px;
  --shadow:   0 10px 28px rgba(150, 120, 205, .18);
  --shadow-s: 0 4px 14px rgba(150, 120, 205, .15);
}

/* 2. Base ------------------------------------------------------------------ */
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Nunito', system-ui, -apple-system, 'Segoe UI', sans-serif;
  color: var(--ink);
  background: linear-gradient(135deg, #fff8ee 0%, #f6ecff 48%, #e8f5ff 100%);
  background-attachment: fixed;
  min-height: 100vh;
  display: flex; flex-direction: column;
  overflow-x: hidden;
  line-height: 1.55;
}
h1, h2, h3, .brand, .btn, .score, .timer-num {
  font-family: 'Fredoka', 'Nunito', system-ui, sans-serif;
  line-height: 1.2;
}
h1 { font-size: clamp(2.2rem, 5vw, 3.6rem); font-weight: 700; }
h2 { font-size: clamp(1.5rem, 3vw, 2.1rem); font-weight: 600; }
h3 { font-size: 1.2rem; font-weight: 600; }
a { color: inherit; text-decoration: none; }
button { font: inherit; cursor: pointer; }
:focus-visible { outline: 3px solid var(--lavender-d); outline-offset: 3px; }
.muted { color: var(--ink-soft); }
.lead { font-size: 1.15rem; color: var(--ink-soft); max-width: 34rem; }
.grad {
  background: linear-gradient(90deg, #a98be0, #f58fb5);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

/* Soft floating background shapes */
.blobs { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.blob { position: absolute; border-radius: 50%; filter: blur(46px); opacity: .55; animation: drift 16s ease-in-out infinite alternate; }
.b1 { width: 340px; height: 340px; background: var(--lavender); top: -90px; left: -80px; }
.b2 { width: 300px; height: 300px; background: var(--pink); bottom: 8%; right: -90px; animation-delay: -5s; }
.b3 { width: 260px; height: 260px; background: var(--mint); bottom: -90px; left: 24%; animation-delay: -9s; }

/* 3. Layout & nav ---------------------------------------------------------- */
.container { position: relative; z-index: 1; width: 100%; max-width: 1100px; margin: 0 auto; padding: 18px 20px 48px; flex: 1; }
.navbar {
  position: sticky; top: 12px; z-index: 20;
  display: flex; align-items: center; justify-content: space-between;
  max-width: 1100px; width: calc(100% - 32px); margin: 12px auto 0;
  padding: 10px 14px 10px 22px; border-radius: 999px;
  background: rgba(255, 255, 255, .78); backdrop-filter: blur(12px);
  box-shadow: var(--shadow-s);
}
.brand { font-size: 1.45rem; font-weight: 700; }
.brand span { color: var(--pink-d); }
.nav-links { display: flex; align-items: center; gap: 4px; }
.nav-links a { padding: 8px 15px; border-radius: 999px; font-weight: 700; font-size: .95rem; transition: background .2s, transform .2s; }
.nav-links a:hover { background: var(--lavender); transform: translateY(-1px); }
.nav-links a.active { background: var(--lavender); }
.nav-links .nav-cta { background: linear-gradient(135deg, var(--lavender), var(--pink)); }
.nav-user { display: flex; align-items: center; gap: 6px; margin-left: 6px; padding: 6px 12px; background: var(--cream); border-radius: 999px; font-weight: 700; }
.nav-toggle { display: none; background: var(--lavender); border: 0; border-radius: 14px; padding: 8px 13px; font-size: 1.1rem; color: var(--ink); }
footer { position: relative; z-index: 1; text-align: center; padding: 20px; color: var(--ink-soft); font-size: .9rem; }

.flash-wrap { display: grid; gap: 10px; margin-bottom: 18px; }
.flash {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  padding: 12px 18px; border-radius: 18px; font-weight: 700; box-shadow: var(--shadow-s);
  animation: slideDown .4s ease;
}
.flash-success { background: var(--mint); }
.flash-error   { background: var(--pink); }
.flash-info    { background: var(--blue); }
.flash button  { background: transparent; border: 0; font-size: 1.2rem; color: var(--ink); }

/* 4. Buttons & cards ------------------------------------------------------- */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px 24px; border: 0; border-radius: 999px;
  font-weight: 600; font-size: 1rem; color: var(--ink);
  box-shadow: var(--shadow-s);
  transition: transform .2s, box-shadow .2s, filter .2s;
}
.btn:hover { transform: translateY(-3px); box-shadow: var(--shadow); filter: brightness(1.03); }
.btn:active { transform: translateY(0) scale(.98); }
.btn-primary { background: linear-gradient(135deg, var(--lavender), var(--pink)); }
.btn-mint    { background: linear-gradient(135deg, var(--mint), var(--blue)); }
.btn-peach   { background: linear-gradient(135deg, var(--peach), var(--pink)); }
.btn-blue    { background: linear-gradient(135deg, var(--blue), var(--lavender)); }
.btn-ghost   { background: var(--white); border: 2px solid var(--lavender); }
.btn-lg { padding: 15px 32px; font-size: 1.12rem; }
.btn-block { width: 100%; }

.card { background: rgba(255, 255, 255, .88); border-radius: var(--radius); box-shadow: var(--shadow); padding: 24px; }
.page-head { margin-bottom: 26px; }
.page-head p { color: var(--ink-soft); margin-top: 6px; }
.back-link { display: inline-block; margin-bottom: 14px; font-weight: 700; color: var(--ink-soft); }
.back-link:hover { color: var(--ink); }
.pill { display: inline-block; padding: 6px 16px; border-radius: 999px; background: var(--mint); font-weight: 700; font-size: .9rem; margin-bottom: 16px; }

/* 5. Landing --------------------------------------------------------------- */
.hero { display: grid; grid-template-columns: 1.05fr .95fr; gap: 40px; align-items: center; padding: 34px 0 20px; }
.hero h1 { margin-bottom: 16px; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 14px; margin: 26px 0; }
.hero-stats { display: flex; gap: 28px; flex-wrap: wrap; }
.hero-stats b { display: block; font-family: 'Fredoka', sans-serif; font-size: 1.7rem; }
.hero-stats span { color: var(--ink-soft); font-size: .9rem; }

/* The memorable element: a live-looking battle preview */
.preview { position: relative; padding: 26px; border-radius: 32px; background: var(--white); box-shadow: 0 18px 44px rgba(150, 120, 205, .25); transform: rotate(2deg); animation: bob 5s ease-in-out infinite; }
.preview-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.preview .side { text-align: center; font-weight: 800; }
.preview .side .face { display: grid; place-items: center; width: 62px; height: 62px; margin: 0 auto 4px; border-radius: 50%; font-size: 1.9rem; }
.preview .side small { display: block; color: var(--ink-soft); font-weight: 700; }
.preview .face.f1 { background: var(--pink); }
.preview .face.f2 { background: var(--blue); }
.preview-timer { display: grid; place-items: center; width: 64px; height: 64px; border-radius: 50%; background: conic-gradient(var(--mint-d) 0 70%, var(--mint) 70% 100%); font-family: 'Fredoka', sans-serif; font-weight: 700; font-size: 1.2rem; position: relative; }
.preview-timer::after { content: ''; position: absolute; inset: 7px; background: var(--white); border-radius: 50%; z-index: 0; }
.preview-timer b { position: relative; z-index: 1; }
.preview-q { margin: 22px 0 14px; font-family: 'Fredoka', sans-serif; font-size: 1.15rem; font-weight: 600; }
.preview-opts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.preview-opts span { padding: 11px 14px; border-radius: 16px; background: var(--cream); font-weight: 700; font-size: .95rem; }
.preview-opts .ok { background: var(--mint); }

.section-title { text-align: center; margin: 56px 0 24px; }
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.feature { text-align: center; transition: transform .25s; }
.feature:hover { transform: translateY(-6px); }
.feature .icon { display: grid; place-items: center; width: 64px; height: 64px; margin: 0 auto 12px; border-radius: 22px; font-size: 1.9rem; }
.feature p { color: var(--ink-soft); margin-top: 6px; }
.steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; counter-reset: step; }
.step { text-align: center; padding: 20px 14px; }
.step::before { counter-increment: step; content: counter(step); display: grid; place-items: center; width: 38px; height: 38px; margin: 0 auto 10px; border-radius: 50%; background: var(--lavender); font-family: 'Fredoka', sans-serif; font-weight: 700; }
.step p { color: var(--ink-soft); font-size: .95rem; }

/* Pastel helper colours */
.bg-lav { background: var(--lavender); } .bg-pink { background: var(--pink); }
.bg-mint { background: var(--mint); }    .bg-peach { background: var(--peach); }
.bg-blue { background: var(--blue); }

/* 6. Forms ----------------------------------------------------------------- */
.auth-wrap { display: grid; place-items: center; padding: 20px 0; }
.form-card { width: 100%; max-width: 470px; padding: 34px 30px; }
.form-card h2 { text-align: center; margin-bottom: 4px; }
.form-card .sub { text-align: center; color: var(--ink-soft); margin-bottom: 22px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-weight: 800; margin-bottom: 6px; font-size: .95rem; }
.input-wrap { position: relative; }
.input-wrap input {
  width: 100%; padding: 13px 16px; border-radius: 16px; border: 2px solid transparent;
  background: var(--cream); color: var(--ink); font: inherit; font-weight: 600;
  transition: border-color .2s, box-shadow .2s, background .2s;
}
.input-wrap input:focus { outline: none; border-color: var(--lavender-d); background: var(--white); box-shadow: 0 0 0 4px rgba(169, 139, 224, .18); }
.input-wrap input.invalid { border-color: var(--pink-d); background: #fff4f8; }
.toggle-pass { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: transparent; border: 0; font-size: 1.1rem; padding: 6px 8px; }
.error-text { display: block; min-height: 1.1em; margin-top: 4px; color: #d4568a; font-size: .85rem; font-weight: 700; }
.form-error { background: var(--pink); padding: 11px 16px; border-radius: 16px; font-weight: 700; margin-bottom: 16px; text-align: center; }
.form-foot { text-align: center; margin-top: 18px; color: var(--ink-soft); }
.form-foot a { color: var(--ink); font-weight: 800; text-decoration: underline; text-decoration-color: var(--pink-d); text-underline-offset: 4px; }
.hint-box { margin-top: 16px; padding: 12px 16px; border-radius: 16px; background: var(--blue); font-size: .92rem; text-align: center; }
.avatar-picker { display: grid; grid-template-columns: repeat(8, 1fr); gap: 8px; }
.avatar-option input { position: absolute; opacity: 0; pointer-events: none; }
.avatar-option span { display: grid; place-items: center; aspect-ratio: 1; border-radius: 16px; background: var(--cream); font-size: 1.5rem; cursor: pointer; border: 2px solid transparent; transition: transform .2s, background .2s; }
.avatar-option span:hover { transform: scale(1.12); }
.avatar-option input:checked + span { background: var(--lavender); border-color: var(--lavender-d); transform: scale(1.1); }
.avatar-option input:focus-visible + span { outline: 3px solid var(--lavender-d); outline-offset: 2px; }
.strength { height: 8px; border-radius: 99px; background: var(--cream); margin-top: 8px; overflow: hidden; }
.strength-bar { height: 100%; width: 0; border-radius: 99px; transition: width .3s, background .3s; }

/* 7. Dashboard & profile --------------------------------------------------- */
.welcome { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; padding: 28px 30px; margin-bottom: 22px; background: linear-gradient(135deg, var(--lavender), var(--pink)); }
.welcome h2 { margin-bottom: 4px; }
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 22px; }
.stat { text-align: center; padding: 20px 12px; border-radius: 22px; box-shadow: var(--shadow-s); transition: transform .25s; }
.stat:hover { transform: translateY(-4px); }
.stat .em { font-size: 1.6rem; }
.stat b { display: block; font-family: 'Fredoka', sans-serif; font-size: 1.8rem; }
.stat span { font-size: .9rem; color: var(--ink-soft); font-weight: 700; }
.two-col { display: grid; grid-template-columns: 1.3fr 1fr; gap: 20px; }
.action-grid { display: grid; gap: 12px; }
.action { display: flex; align-items: center; gap: 14px; padding: 16px 18px; border-radius: 20px; font-weight: 800; transition: transform .2s, box-shadow .2s; }
.action:hover { transform: translateX(6px); box-shadow: var(--shadow-s); }
.action small { display: block; font-weight: 600; color: var(--ink-soft); }
.action .em { font-size: 1.6rem; }
.tip { margin-top: 16px; padding: 14px 18px; border-radius: 18px; background: var(--peach); font-weight: 700; }
.game-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 12px 0; border-bottom: 2px dashed var(--cream); }
.game-row:last-child { border-bottom: 0; }
.badge { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: .82rem; font-weight: 800; }
.badge.win { background: var(--mint); } .badge.loss { background: var(--pink); } .badge.draw { background: var(--blue); }
.empty { text-align: center; padding: 22px; color: var(--ink-soft); }

.profile-grid { display: grid; grid-template-columns: 340px 1fr; gap: 20px; align-items: start; }
.profile-card { text-align: center; }
.avatar-xl { display: grid; place-items: center; width: 112px; height: 112px; margin: 0 auto 12px; border-radius: 50%; background: linear-gradient(135deg, var(--lavender), var(--pink)); font-size: 3.4rem; box-shadow: var(--shadow-s); }
.rank-chip { display: inline-block; margin-top: 10px; padding: 6px 16px; border-radius: 999px; background: var(--peach); font-weight: 800; }
.profile-card form { margin-top: 20px; text-align: left; }
.profile-card .avatar-picker { grid-template-columns: repeat(4, 1fr); margin-bottom: 12px; }
.table-wrap { overflow-x: auto; }
table.games { width: 100%; border-collapse: collapse; min-width: 480px; }
table.games th, table.games td { padding: 10px 8px; text-align: left; border-bottom: 2px dashed var(--cream); font-size: .95rem; }
table.games th { color: var(--ink-soft); font-size: .85rem; }

/* 8. Categories & difficulty ----------------------------------------------- */
.cat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; }
.cat-card, .diff-card { display: block; padding: 28px 22px; border-radius: var(--radius); box-shadow: var(--shadow); transition: transform .25s, box-shadow .25s; }
.cat-card:hover, .diff-card:hover { transform: translateY(-8px) rotate(-1deg); box-shadow: 0 16px 36px rgba(150, 120, 205, .28); }
.cat-card .big, .diff-card .big { display: grid; place-items: center; width: 70px; height: 70px; margin-bottom: 14px; border-radius: 24px; background: rgba(255, 255, 255, .7); font-size: 2.2rem; }
.cat-card p, .diff-card p { color: var(--ink-soft); margin: 6px 0 14px; }
.c-lavender { background: var(--lavender); } .c-mint { background: var(--mint); }
.c-blue { background: var(--blue); } .c-peach { background: var(--peach); } .c-pink { background: var(--pink); }
.go { font-weight: 800; }
.chosen { display: inline-flex; align-items: center; gap: 8px; padding: 8px 18px; border-radius: 999px; font-weight: 800; margin-top: 10px; }
.diff-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.d-easy { background: var(--mint); } .d-medium { background: var(--peach); } .d-hard { background: var(--pink); }
.rules { list-style: none; display: grid; gap: 6px; margin-bottom: 16px; font-weight: 700; font-size: .95rem; }

/* 9. Quiz screen ----------------------------------------------------------- */
.quiz-wrap { max-width: 780px; margin: 0 auto; }
.quiz-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.quit { font-weight: 800; color: var(--ink-soft); }
.quit:hover { color: #d4568a; }
.vs-bar { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; padding: 16px 20px; margin-bottom: 14px; }
.player { display: flex; align-items: center; gap: 12px; }
.player.right { flex-direction: row-reverse; text-align: right; }
.player .face { display: grid; place-items: center; width: 54px; height: 54px; border-radius: 50%; font-size: 1.7rem; flex-shrink: 0; }
.player.me .face { background: var(--pink); } .player.opp .face { background: var(--blue); }
.player .name { font-weight: 800; line-height: 1.1; }
.player .score { display: block; font-size: 1.7rem; font-weight: 700; }
.player .score.bump { animation: pop .5s ease; }
.timer { position: relative; width: 84px; height: 84px; }
.timer svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.ring-bg { fill: none; stroke: var(--cream); stroke-width: 8; }
.ring-fg { fill: none; stroke: var(--mint-d); stroke-width: 8; stroke-linecap: round; transition: stroke-dashoffset 1s linear, stroke .3s; }
.timer.warn .ring-fg { stroke: var(--peach-d); }
.timer.danger .ring-fg { stroke: var(--pink-d); }
.timer.danger { animation: pulse .6s ease-in-out infinite; }
.timer-num { position: absolute; inset: 0; display: grid; place-items: center; font-size: 1.7rem; font-weight: 700; }
.progress { height: 12px; border-radius: 99px; background: rgba(255, 255, 255, .8); overflow: hidden; margin-bottom: 8px; }
.progress-fill { height: 100%; width: 0; border-radius: 99px; background: linear-gradient(90deg, var(--lavender-d), var(--pink-d)); transition: width .5s ease; }
.q-meta { display: flex; justify-content: space-between; font-weight: 800; color: var(--ink-soft); margin-bottom: 14px; font-size: .95rem; }
.q-card { padding: 28px; }
.q-card.enter { animation: slideIn .45s ease; }
.q-text { font-family: 'Fredoka', sans-serif; font-size: clamp(1.25rem, 3vw, 1.7rem); font-weight: 600; margin-bottom: 22px; }
.options { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.option {
  display: flex; align-items: center; gap: 12px; text-align: left;
  padding: 14px 16px; border-radius: 20px; border: 2px solid transparent;
  background: var(--cream); color: var(--ink); font-weight: 700; font-size: 1rem;
  transition: transform .2s, background .2s, border-color .2s, opacity .3s;
}
.option:hover:not(:disabled) { transform: translateY(-3px); background: var(--lavender); }
.option .letter { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 12px; background: var(--white); font-family: 'Fredoka', sans-serif; flex-shrink: 0; }
.option.correct { background: var(--mint); border-color: var(--mint-d); animation: pop .5s ease; }
.option.wrong { background: var(--pink); border-color: var(--pink-d); animation: shake .45s ease; }
.option.dim { opacity: .5; }
.option:disabled { cursor: default; }
.feedback { margin-top: 20px; padding: 14px 18px; border-radius: 18px; background: var(--blue); font-weight: 700; animation: slideDown .35s ease; }
.feedback[hidden] { display: none; }
.feedback .row { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.feedback .opp-line { color: var(--ink-soft); font-size: .93rem; margin-top: 4px; }
.feedback.good { background: var(--mint); } .feedback.bad { background: var(--pink); }
.feedback .btn { padding: 9px 20px; }

/* 10. Results -------------------------------------------------------------- */
.winner { text-align: center; padding: 34px 20px; margin-bottom: 20px; }
.winner .trophy { font-size: 4rem; display: inline-block; animation: bob 3s ease-in-out infinite; }
.winner.win { background: linear-gradient(135deg, var(--mint), var(--blue)); }
.winner.loss { background: linear-gradient(135deg, var(--pink), var(--peach)); }
.winner.draw { background: linear-gradient(135deg, var(--lavender), var(--blue)); }
.chips { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 14px; }
.chip { padding: 6px 16px; border-radius: 999px; background: rgba(255, 255, 255, .75); font-weight: 800; font-size: .92rem; }
.duel { display: grid; grid-template-columns: 1fr auto 1fr; gap: 14px; align-items: center; margin-bottom: 20px; }
.duel-side { text-align: center; padding: 22px; border-radius: var(--radius); box-shadow: var(--shadow); }
.duel-side.me { background: var(--pink); } .duel-side.opp { background: var(--blue); }
.duel-side .face { font-size: 2.6rem; }
.duel-side .score { display: block; font-size: 2.6rem; font-weight: 700; }
.duel-side.lead { outline: 4px solid var(--white); box-shadow: 0 0 0 7px var(--peach), var(--shadow); }
.vs-badge { display: grid; place-items: center; width: 54px; height: 54px; border-radius: 50%; background: var(--white); font-family: 'Fredoka', sans-serif; font-weight: 700; box-shadow: var(--shadow-s); }
.actions-row { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin: 22px 0 8px; }
.review-item { padding: 18px 20px; border-radius: 20px; background: var(--cream); margin-bottom: 14px; }
.review-item h3 { font-size: 1.05rem; margin-bottom: 10px; }
.review-item .opts { display: flex; flex-wrap: wrap; gap: 8px; }
.opt-chip { padding: 6px 14px; border-radius: 999px; background: var(--white); font-weight: 700; font-size: .9rem; }
.opt-chip.right { background: var(--mint); } .opt-chip.mine-wrong { background: var(--pink); text-decoration: line-through; }
.review-meta { margin-top: 10px; font-size: .9rem; color: var(--ink-soft); font-weight: 700; }

/* 11. Leaderboard ---------------------------------------------------------- */
.tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
.tab { padding: 8px 18px; border-radius: 999px; background: var(--white); font-weight: 800; box-shadow: var(--shadow-s); transition: transform .2s, background .2s; }
.tab:hover { transform: translateY(-2px); background: var(--lavender); }
.tab.on { background: var(--lavender-d); color: var(--white); }
.my-rank { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; padding: 18px 24px; margin-bottom: 18px; background: linear-gradient(135deg, var(--peach), var(--pink)); }
.lb-row { display: grid; grid-template-columns: 56px 1fr auto; align-items: center; gap: 14px; padding: 14px 18px; margin-bottom: 10px; border-radius: 22px; background: rgba(255, 255, 255, .9); box-shadow: var(--shadow-s); transition: transform .2s; }
.lb-row:hover { transform: scale(1.015); }
.lb-row.me { background: var(--lavender); outline: 3px solid var(--lavender-d); }
.lb-row.top1 { background: linear-gradient(135deg, #fff1c9, var(--peach)); }
.lb-row.top2 { background: linear-gradient(135deg, #eef1f7, var(--blue)); }
.lb-row.top3 { background: linear-gradient(135deg, #ffe5d6, var(--pink)); }
.medal { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 50%; background: var(--white); font-family: 'Fredoka', sans-serif; font-weight: 700; font-size: 1.2rem; }
.lb-user { display: flex; align-items: center; gap: 12px; font-weight: 800; }
.lb-user .face { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 50%; background: var(--cream); font-size: 1.5rem; }
.lb-user small { display: block; color: var(--ink-soft); font-weight: 700; }
.lb-points { text-align: right; font-family: 'Fredoka', sans-serif; font-size: 1.4rem; font-weight: 700; }
.lb-points small { display: block; font-family: 'Nunito', sans-serif; font-size: .8rem; color: var(--ink-soft); }

/* Confetti on a win */
.confetti { position: fixed; top: -40px; z-index: 50; font-size: 1.6rem; pointer-events: none; animation: fall linear forwards; }

/* 12. Animations ----------------------------------------------------------- */
@keyframes drift { to { transform: translate(40px, 30px) scale(1.12); } }
@keyframes bob { 0%, 100% { translate: 0 0; } 50% { translate: 0 -10px; } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: none; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(26px); } to { opacity: 1; transform: none; } }
@keyframes pop { 0% { transform: scale(1); } 45% { transform: scale(1.1); } 100% { transform: scale(1); } }
@keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-7px); } 75% { transform: translateX(7px); } }
@keyframes pulse { 50% { transform: scale(1.07); } }
@keyframes fall { to { transform: translateY(110vh) rotate(540deg); opacity: .8; } }
@keyframes rise { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
/* One orchestrated entrance for the landing hero */
.hero-text > * { animation: rise .6s ease both; }
.hero-text > :nth-child(2) { animation-delay: .08s; } .hero-text > :nth-child(3) { animation-delay: .16s; }
.hero-text > :nth-child(4) { animation-delay: .24s; } .hero-text > :nth-child(5) { animation-delay: .32s; }
.auth-wrap .form-card, .page-head, .welcome { animation: rise .5s ease both; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; scroll-behavior: auto !important; }
}

/* 13. Responsive ----------------------------------------------------------- */
@media (max-width: 900px) {
  .hero, .two-col, .profile-grid { grid-template-columns: 1fr; }
  .features, .steps { grid-template-columns: 1fr 1fr; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .preview { transform: none; max-width: 460px; margin: 0 auto; }
}
@media (max-width: 720px) {
  .navbar { border-radius: 28px; flex-wrap: wrap; }
  .nav-toggle { display: block; }
  .nav-links { display: none; width: 100%; flex-direction: column; align-items: stretch; padding: 10px 0 6px; }
  .nav-links.open { display: flex; }
  .nav-links a, .nav-user { text-align: center; justify-content: center; }
}
@media (max-width: 560px) {
  .features, .steps, .options, .duel { grid-template-columns: 1fr; }
  .vs-bar { grid-template-columns: 1fr auto 1fr; padding: 12px; gap: 6px; }
  .player .face { width: 42px; height: 42px; font-size: 1.3rem; }
  .player .score { font-size: 1.3rem; }
  .player .name { font-size: .85rem; }
  .timer { width: 68px; height: 68px; } .timer-num { font-size: 1.4rem; }
  .q-card { padding: 20px 16px; }
  .vs-badge { margin: 0 auto; }
  .avatar-picker { grid-template-columns: repeat(4, 1fr); }
  .lb-row { grid-template-columns: 46px 1fr auto; padding: 12px; gap: 8px; }
  .form-card { padding: 26px 18px; }
}

/* ---- extras for the single-file app ---- */
.toast-wrap { position: fixed; top: 84px; right: 18px; z-index: 60; display: grid; gap: 10px; width: min(340px, calc(100vw - 36px)); }
.toast { padding: 12px 18px; border-radius: 18px; font-weight: 700; box-shadow: var(--shadow); animation: slideDown .35s ease; transition: opacity .4s, transform .4s; }
.toast.out { opacity: 0; transform: translateX(20px); }
.toast-success { background: var(--mint); } .toast-error { background: var(--pink); } .toast-info { background: var(--blue); }
.loading { text-align: center; padding: 70px 20px; color: var(--ink-soft); font-weight: 800; }
.avatar-option { position: relative; display: block; }
a.tab, a.cat-card, a.diff-card, a.action, a.btn { cursor: pointer; }

</style>
</head>
<body>
<div class="blobs" aria-hidden="true"><span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span></div>

<nav class="navbar">
  <a class="brand" href="#/landing">🎀 Quiz<span>Battle</span></a>
  <button class="nav-toggle" id="navToggle" aria-label="Open menu">☰</button>
  <div class="nav-links" id="navLinks"></div>
</nav>

<main class="container" id="app"><div class="loading">Loading Quiz Battle...</div></main>
<div class="toast-wrap" id="toasts"></div>
<footer>Quiz Battle • TY BBA (CA) project • Python, SQLite, HTML, CSS and JavaScript</footer>

<script>
/* ==========================================================================
   QUIZ BATTLE - screens and behaviour (JavaScript)
   Part A: helpers   Part B: router + menu   Part C: the 10 screens
   ========================================================================== */
(function () {
'use strict';

/* ---------- Part A: helpers ---------- */
var $ = function (sel, el) { return (el || document).querySelector(sel); };
var $$ = function (sel, el) { return Array.prototype.slice.call((el || document).querySelectorAll(sel)); };
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
var store = {
  get: function (k) { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } },
  set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  del: function (k) { try { localStorage.removeItem(k); } catch (e) {} }
};
var S = { token: store.get('qb_token'), user: null, meta: null, category: null,
          cleanup: null, rid: 0, lbCat: '' };
var SCREENS = {};
var PUBLIC = ['landing', 'signup', 'login'];

/* talk to the Python backend */
function api(path, body) {
  var opt = { headers: { 'X-Token': S.token || '' } };
  if (body !== undefined) {
    opt.method = 'POST';
    opt.headers['Content-Type'] = 'application/json';
    opt.body = JSON.stringify(body);
  }
  return fetch(path, opt)
    .then(function (r) { return r.json().then(function (d) { d._status = r.status; return d; }); })
    .catch(function () { return { error: 'Could not reach the game engine.', _status: 0 }; });
}

function toast(msg, kind) {
  var t = document.createElement('div');
  t.className = 'toast toast-' + (kind || 'info');
  t.textContent = msg;
  $('#toasts').appendChild(t);
  setTimeout(function () { t.classList.add('out'); setTimeout(function () { t.remove(); }, 400); }, 3500);
}

function confetti() {
  var pieces = ['🎉', '✨', '🎀', '⭐', '💜', '🌸'];
  for (var i = 0; i < 28; i++) {
    var s = document.createElement('span');
    s.className = 'confetti';
    s.textContent = pieces[i % pieces.length];
    s.style.left = Math.random() * 100 + 'vw';
    s.style.animationDuration = (3 + Math.random() * 3) + 's';
    s.style.animationDelay = (Math.random() * 1.5) + 's';
    document.body.appendChild(s);
    setTimeout((function (el) { return function () { el.remove(); }; })(s), 8000);
  }
}

/* form validation (used by Sign up and Login) */
var RULES = {
  signup: {
    username: function (v) { return /^[A-Za-z0-9_]{3,20}$/.test(v) ? '' : 'Use 3-20 letters, numbers or underscores.'; },
    email: function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) ? '' : 'Enter a valid email address.'; },
    password: function (v) { return v.length >= 6 ? '' : 'Password must be at least 6 characters.'; },
    confirm: function (v, f) { return v === f.elements.password.value ? '' : 'Passwords do not match.'; }
  },
  login: {
    identifier: function (v) { return v.trim() ? '' : 'Enter your username or email.'; },
    password: function (v) { return v ? '' : 'Enter your password.'; }
  }
};
function setErr(form, name, msg) {
  var out = form.querySelector('[data-error-for="' + name + '"]');
  if (out) out.textContent = msg || '';
  if (form.elements[name]) form.elements[name].classList.toggle('invalid', !!msg);
}
function bindValidation(form, mode, onValid) {
  var rules = RULES[mode];
  function check(name) {
    var m = rules[name](form.elements[name].value, form);
    setErr(form, name, m);
    return !m;
  }
  Object.keys(rules).forEach(function (name) {
    var el = form.elements[name];
    el.addEventListener('blur', function () { check(name); });
    el.addEventListener('input', function () { if (el.classList.contains('invalid')) check(name); });
  });
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var ok = true;
    Object.keys(rules).forEach(function (n) { if (!check(n)) ok = false; });
    if (ok) onValid();
  });
}
function wirePasswordToggles(root) {
  $$('.toggle-pass', root).forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = document.getElementById(btn.dataset.target);
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.textContent = show ? '🙈' : '👁️';
    });
  });
}
function avatarPicker(selected) {
  return '<div class="avatar-picker">' + S.meta.avatars.map(function (a) {
    return '<label class="avatar-option"><input type="radio" name="avatar" value="' + a + '"' +
      (a === selected ? ' checked' : '') + '><span>' + a + '</span></label>';
  }).join('') + '</div>';
}
function statCard(color, emoji, value, label) {
  return '<div class="stat ' + color + '"><div class="em">' + emoji + '</div><b>' + esc(value) + '</b><span>' + label + '</span></div>';
}
function catOf(key) { return S.meta.categories[key] || { name: key, icon: '❓' }; }
function badge(result) { return '<span class="badge ' + esc(result) + '">' + esc(result.charAt(0).toUpperCase() + result.slice(1)) + '</span>'; }
function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

/* ---------- Part B: navigation bar and router ---------- */
function renderNav(active) {
  var u = S.user;
  function link(to, label, on) { return '<a href="#/' + to + '" class="' + (on ? 'active' : '') + '">' + label + '</a>'; }
  $('#navLinks').innerHTML = u ? [
    link('dashboard', '🏠 Dashboard', active === 'dashboard'),
    link('categories', '🎮 Play', ['categories', 'difficulty', 'quiz', 'results'].indexOf(active) > -1),
    link('leaderboard', '🏆 Leaderboard', active === 'leaderboard'),
    link('profile', '👤 Profile', active === 'profile'),
    '<span class="nav-user">' + esc(u.avatar) + ' ' + esc(u.username) + '</span>',
    '<a href="#/landing" id="logoutLink">Logout</a>'
  ].join('') : [
    link('landing', 'Home', active === 'landing'),
    link('login', 'Login', active === 'login'),
    '<a href="#/signup" class="nav-cta">Sign up</a>'
  ].join('');
  $('#navLinks').classList.remove('open');
  var lo = $('#logoutLink');
  if (lo) lo.addEventListener('click', function (e) {
    e.preventDefault();
    api('/api/logout', {}).then(function () {
      S.token = ''; S.user = null; store.del('qb_token');
      toast('You have been logged out. See you soon!', 'info');
      if (routeName() === 'landing') render(); else location.hash = '#/landing';
    });
  });
}
$('#navToggle').addEventListener('click', function () { $('#navLinks').classList.toggle('open'); });

function routeName() { return location.hash.replace(/^#\/?/, '') || 'landing'; }

function loadUser() {
  if (!S.token) { S.user = null; return Promise.resolve(); }
  return api('/api/me').then(function (d) { S.user = d.user || null; if (!d.user) { S.token = ''; store.del('qb_token'); } });
}

function render() {
  if (S.cleanup) { S.cleanup(); S.cleanup = null; }
  var my = ++S.rid;
  var alive = function () { return my === S.rid; };
  var name = routeName();
  if (!SCREENS[name]) name = 'landing';
  var ready = S.user ? Promise.resolve() : loadUser();
  return ready.then(function () {
    if (!alive()) return;
    if (PUBLIC.indexOf(name) === -1 && !S.user) {
      toast('Please log in to continue.', 'info');
      location.hash = '#/login';
      return;
    }
    if (S.user && (name === 'signup' || name === 'login')) { location.hash = '#/dashboard'; return; }
    renderNav(name);
    window.scrollTo(0, 0);
    return SCREENS[name]($('#app'), alive);
  });
}
window.addEventListener('hashchange', render);

/* ---------- Part C: the 10 screens ---------- */

/* SCREEN 1 - Welcome / landing */
SCREENS.landing = function (app, alive) {
  return api('/api/home').then(function (h) {
    if (!alive()) return;
    app.innerHTML =
      '<section class="hero"><div class="hero-text">' +
        '<span class="pill">🎀 Quiz against a rival, race the clock</span>' +
        '<h1>Outscore your rival in the <span class="grad">Quiz Battle</span></h1>' +
        '<p class="lead">Pick a category, choose how tough it gets, and answer faster than your opponent. Every correct answer earns points, and the quickest players climb the leaderboard.</p>' +
        '<div class="hero-actions">' + (S.user
          ? '<a class="btn btn-primary btn-lg" href="#/dashboard">🎮 Go to my dashboard</a>'
          : '<a class="btn btn-primary btn-lg" href="#/signup">🚀 Create free account</a><a class="btn btn-ghost btn-lg" href="#/login">🔑 Log in</a>') + '</div>' +
        '<div class="hero-stats"><div><b>' + h.players + '</b><span>players</span></div><div><b>' + h.games +
        '</b><span>battles played</span></div><div><b>' + h.categories + '</b><span>categories</span></div></div>' +
      '</div>' +
      '<div class="preview" aria-hidden="true"><div class="preview-top">' +
        '<div class="side"><div class="face f1">🦊</div>You<small>60 pts</small></div>' +
        '<div class="preview-timer"><b>9</b></div>' +
        '<div class="side"><div class="face f2">🦋</div>Luna<small>45 pts</small></div></div>' +
        '<p class="preview-q">Which planet is known as the Red Planet?</p>' +
        '<div class="preview-opts"><span>A. Venus</span><span class="ok">B. Mars ✓</span><span>C. Jupiter</span><span>D. Saturn</span></div></div>' +
      '</section>' +
      '<h2 class="section-title">Why you will love it</h2><section class="features">' +
        '<div class="card feature"><div class="icon bg-pink">⚔️</div><h3>Beat an opponent</h3><p>Every question is a duel. See your rival\'s score change after each answer.</p></div>' +
        '<div class="card feature"><div class="icon bg-mint">⏱️</div><h3>Race the timer</h3><p>Answer quickly for bonus points. When the clock hits zero, the question is gone.</p></div>' +
        '<div class="card feature"><div class="icon bg-peach">🏆</div><h3>Climb the ranks</h3><p>Your points from every battle add up to your place on the leaderboard.</p></div></section>' +
      '<h2 class="section-title">How a battle works</h2><section class="steps">' +
        '<div class="card step"><h3>Sign up</h3><p>Pick a name and a cute avatar.</p></div>' +
        '<div class="card step"><h3>Choose a topic</h3><p>Five categories to pick from.</p></div>' +
        '<div class="card step"><h3>Pick a level</h3><p>Easy, medium or hard.</p></div>' +
        '<div class="card step"><h3>Battle</h3><p>Answer 5 questions and see who wins.</p></div></section>';
  });
};

/* SCREEN 2 - Sign up */
SCREENS.signup = function (app) {
  app.innerHTML =
    '<div class="auth-wrap"><div class="card form-card"><h2>Create your account 🎀</h2>' +
    '<p class="sub">Choose an avatar and join the battle.</p>' +
    '<form id="signupForm" novalidate>' +
      '<div class="field"><label>Pick your avatar</label>' + avatarPicker(S.meta.avatars[0]) + '</div>' +
      '<div class="field"><label for="username">Username</label><div class="input-wrap"><input type="text" id="username" name="username" placeholder="e.g. quiz_star" autocomplete="username"></div><span class="error-text" data-error-for="username"></span></div>' +
      '<div class="field"><label for="email">Email</label><div class="input-wrap"><input type="email" id="email" name="email" placeholder="you@example.com" autocomplete="email"></div><span class="error-text" data-error-for="email"></span></div>' +
      '<div class="field"><label for="password">Password</label><div class="input-wrap"><input type="password" id="password" name="password" placeholder="At least 6 characters" autocomplete="new-password"><button type="button" class="toggle-pass" data-target="password" aria-label="Show or hide password">👁️</button></div><div class="strength"><div class="strength-bar" id="strengthBar"></div></div><span class="error-text" data-error-for="password"></span></div>' +
      '<div class="field"><label for="confirm">Confirm password</label><div class="input-wrap"><input type="password" id="confirm" name="confirm" placeholder="Type the password again" autocomplete="new-password"><button type="button" class="toggle-pass" data-target="confirm" aria-label="Show or hide password">👁️</button></div><span class="error-text" data-error-for="confirm"></span></div>' +
      '<button type="submit" class="btn btn-primary btn-block btn-lg">✨ Create account</button>' +
    '</form><p class="form-foot">Already have an account? <a href="#/login">Log in</a></p></div></div>';

  var form = $('#signupForm');
  wirePasswordToggles(app);
  $('#password').addEventListener('input', function () {
    var v = this.value, score = 0;
    if (v.length >= 6) score++;
    if (v.length >= 10) score++;
    if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
    if (/\d/.test(v) && /[^A-Za-z0-9]/.test(v)) score++;
    var bar = $('#strengthBar');
    bar.style.width = v ? (score * 25) + '%' : '0';
    bar.style.background = ['#f58fb5', '#f5a974', '#7dbaf0', '#6fd1a5'][Math.max(score - 1, 0)];
  });
  bindValidation(form, 'signup', function () {
    var avatar = form.querySelector('input[name=avatar]:checked');
    api('/api/signup', {
      username: form.elements.username.value.trim(), email: form.elements.email.value.trim(),
      password: form.elements.password.value, confirm: form.elements.confirm.value,
      avatar: avatar ? avatar.value : ''
    }).then(function (d) {
      if (d.errors) { Object.keys(d.errors).forEach(function (n) { setErr(form, n, d.errors[n]); }); return; }
      if (d.error) { toast(d.error, 'error'); return; }
      toast('Account created! Log in to start your first battle.', 'success');
      location.hash = '#/login';
    });
  });
};

/* SCREEN 3 - Login */
SCREENS.login = function (app) {
  app.innerHTML =
    '<div class="auth-wrap"><div class="card form-card"><h2>Welcome back 👋</h2>' +
    '<p class="sub">Log in to continue your battles.</p><div id="loginError"></div>' +
    '<form id="loginForm" novalidate>' +
      '<div class="field"><label for="identifier">Username or email</label><div class="input-wrap"><input type="text" id="identifier" name="identifier" placeholder="Your username or email" autocomplete="username"></div><span class="error-text" data-error-for="identifier"></span></div>' +
      '<div class="field"><label for="password">Password</label><div class="input-wrap"><input type="password" id="password" name="password" placeholder="Your password" autocomplete="current-password"><button type="button" class="toggle-pass" data-target="password" aria-label="Show or hide password">👁️</button></div><span class="error-text" data-error-for="password"></span></div>' +
      '<button type="submit" class="btn btn-primary btn-block btn-lg">🔑 Log in</button>' +
    '</form>' +
    '<div class="hint-box">🎓 Demo account for your presentation:<br><b>demo</b> / <b>demo123</b></div>' +
    '<p class="form-foot">New here? <a href="#/signup">Create an account</a></p></div></div>';
  wirePasswordToggles(app);
  var form = $('#loginForm');
  bindValidation(form, 'login', function () {
    api('/api/login', { identifier: form.elements.identifier.value.trim(), password: form.elements.password.value })
      .then(function (d) {
        if (d.error) { $('#loginError').innerHTML = '<div class="form-error">' + esc(d.error) + '</div>'; return; }
        S.token = d.token; S.user = d.user; store.set('qb_token', d.token);
        toast('Welcome back, ' + d.user.username + '!', 'success');
        location.hash = '#/dashboard';
      });
  });
};

/* SCREEN 5 - Game dashboard */
SCREENS.dashboard = function (app, alive) {
  return api('/api/me').then(function (d) {
    if (!alive() || !d.user) return;
    S.user = d.user;
    var st = d.stats;
    var recent = d.recent.slice(0, 3);
    app.innerHTML =
      '<section class="card welcome"><div><h2>Hi ' + esc(d.user.username) + '! ' + esc(d.user.avatar) + '</h2><p>' +
        (st.games ? 'You have played ' + st.games + ' battle' + (st.games === 1 ? '' : 's') + '. Ready for the next one?' : 'Start your first battle and set a score to beat.') +
        '</p></div><a class="btn btn-ghost btn-lg" href="#/categories">🎮 Start a battle</a></section>' +
      '<section class="stat-grid">' + statCard('bg-pink', '⭐', st.points, 'Total points') + statCard('bg-mint', '🏅', st.wins, 'Wins') +
        statCard('bg-blue', '🎯', st.accuracy + '%', 'Accuracy') + statCard('bg-peach', '🏆', d.rank ? '#' + d.rank : '-', 'Your rank') + '</section>' +
      '<section class="two-col"><div class="card"><h3>Recent battles</h3>' +
        (recent.length ? recent.map(function (g) {
          var c = catOf(g.category);
          return '<div class="game-row"><div><b>' + c.icon + ' ' + esc(c.name) + '</b><div class="muted">' + esc(cap(g.difficulty)) + ' • ' + esc(g.played_at) +
            '</div></div><div style="text-align:right">' + badge(g.result) + '<div class="muted">' + g.player_score + ' - ' + g.opponent_score + '</div></div></div>';
        }).join('') : '<div class="empty">No battles yet. Your first one is a great place to start! 🌟</div>') +
        '<div class="tip">💡 ' + esc(d.tip) + '</div></div>' +
      '<div class="card"><h3 style="margin-bottom:14px">Quick actions</h3><div class="action-grid">' +
        '<a class="action bg-lav" href="#/categories"><span class="em">🎮</span><span>Play a battle<small>Choose category and level</small></span></a>' +
        '<a class="action bg-mint" href="#/leaderboard"><span class="em">🏆</span><span>Leaderboard<small>See who is on top</small></span></a>' +
        '<a class="action bg-peach" href="#/profile"><span class="em">👤</span><span>My profile<small>Stats and avatar</small></span></a>' +
      '</div></div></section>';
    renderNav('dashboard');
  });
};

/* SCREEN 4 - User profile */
SCREENS.profile = function (app, alive) {
  return api('/api/me').then(function (d) {
    if (!alive() || !d.user) return;
    S.user = d.user;
    var st = d.stats, u = d.user;
    app.innerHTML =
      '<div class="page-head"><h2>My profile 👤</h2><p>Your details, stats and battle history.</p></div><div class="profile-grid">' +
      '<div class="card profile-card"><div class="avatar-xl">' + esc(u.avatar) + '</div><h3>' + esc(u.username) + '</h3>' +
        '<p class="muted">' + esc(u.email) + '</p><p class="muted">Joined ' + esc(u.created_at) + '</p>' +
        '<span class="rank-chip">🏆 ' + (d.rank ? 'Rank #' + d.rank : 'Not ranked yet') + '</span>' +
        '<form id="avatarForm"><label class="muted" style="font-weight:800;display:block;margin-bottom:8px">Change avatar</label>' +
        avatarPicker(u.avatar) + '<button class="btn btn-primary btn-block" type="submit">💾 Save avatar</button></form></div>' +
      '<div><section class="stat-grid" style="grid-template-columns:repeat(3,1fr)">' +
        statCard('bg-lav', '🎮', st.games, 'Battles') + statCard('bg-pink', '⭐', st.points, 'Total points') + statCard('bg-mint', '🥇', st.best, 'Best score') +
        statCard('bg-blue', '🏅', st.wins + '/' + st.losses + '/' + st.draws, 'Win / loss / draw') + statCard('bg-peach', '📈', st.win_rate + '%', 'Win rate') +
        statCard('bg-lav', '🎯', st.accuracy + '%', 'Accuracy') + '</section>' +
      '<div class="card"><h3 style="margin-bottom:10px">Battle history</h3>' +
        (d.recent.length ? '<div class="table-wrap"><table class="games"><thead><tr><th>Category</th><th>Level</th><th>Score</th><th>Result</th><th>Date</th></tr></thead><tbody>' +
          d.recent.map(function (g) {
            var c = catOf(g.category), df = S.meta.difficulties[g.difficulty];
            return '<tr><td>' + c.icon + ' ' + esc(c.name) + '</td><td>' + df.icon + ' ' + esc(cap(g.difficulty)) + '</td><td>' +
              g.player_score + ' - ' + g.opponent_score + '</td><td>' + badge(g.result) + '</td><td>' + esc(g.played_at) + '</td></tr>';
          }).join('') + '</tbody></table></div>'
          : '<div class="empty">You have not played yet. <a href="#/categories"><b>Start a battle</b></a></div>') +
      '</div></div></div>';
    renderNav('profile');
    $('#avatarForm').addEventListener('submit', function (e) {
      e.preventDefault();
      var pick = $('#avatarForm input[name=avatar]:checked');
      if (!pick) return;
      api('/api/avatar', { avatar: pick.value }).then(function (r) {
        if (r.error) { toast(r.error, 'error'); return; }
        toast('Your avatar was updated.', 'success');
        S.user.avatar = r.avatar;
        render();
      });
    });
  });
};

/* SCREEN 6 - Select quiz category */
SCREENS.categories = function (app) {
  var cats = S.meta.categories;
  app.innerHTML =
    '<a class="back-link" href="#/dashboard">← Back to dashboard</a>' +
    '<div class="page-head"><h2>Choose a category 🎯</h2><p>Step 1 of 2. What do you want to be quizzed on?</p></div><div class="cat-grid">' +
    Object.keys(cats).map(function (k) {
      var c = cats[k];
      return '<a class="cat-card ' + c.color + '" href="#/difficulty" data-cat="' + k + '"><div class="big">' + c.icon + '</div><h3>' + esc(c.name) +
        '</h3><p>' + esc(c.desc) + '</p><span class="go">Pick this topic ➜</span></a>';
    }).join('') + '</div>';
  $$('.cat-card', app).forEach(function (a) {
    a.addEventListener('click', function () { S.category = a.dataset.cat; });
  });
};

/* SCREEN 7 - Select difficulty level */
SCREENS.difficulty = function (app) {
  if (!S.category) { toast('Pick a category first.', 'info'); location.hash = '#/categories'; return; }
  var c = catOf(S.category), diffs = S.meta.difficulties;
  app.innerHTML =
    '<a class="back-link" href="#/categories">← Change category</a>' +
    '<div class="page-head"><h2>Choose your level ⚡</h2><p>Step 2 of 2. Each battle has ' + S.meta.per_game + ' questions against a computer rival.</p>' +
    '<span class="chosen ' + c.color + '">' + c.icon + ' ' + esc(c.name) + '</span></div><div class="diff-grid">' +
    Object.keys(diffs).map(function (k) {
      var d = diffs[k];
      return '<a class="diff-card d-' + k + '" href="#/quiz" data-diff="' + k + '"><div class="big">' + d.icon + '</div><h3>' + esc(d.label) + '</h3><p>' + esc(d.desc) + '</p>' +
        '<ul class="rules"><li>⏱️ ' + d.time + ' seconds per question</li><li>⭐ ' + d.points + ' points + time bonus</li><li>🤖 Rival gets about ' +
        Math.round(d.bot_accuracy * 100) + '% right</li></ul><span class="go">Start battle ➜</span></a>';
    }).join('') + '</div>';
  $$('.diff-card', app).forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      api('/api/start', { category: S.category, difficulty: a.dataset.diff }).then(function (d) {
        if (d.error) { toast(d.error, 'error'); return; }
        location.hash = '#/quiz';
      });
    });
  });
};

/* SCREEN 8 - Quiz battle (questions, timer, score, opponent) */
SCREENS.quiz = function (app, alive) {
  return api('/api/quiz').then(function (quiz) {
    if (!alive()) return;
    if (quiz.error) { toast('Choose a category and level to start a battle.', 'info'); location.hash = '#/categories'; return; }
    app.innerHTML =
      '<div class="quiz-wrap"><div class="quiz-top"><span class="chosen ' + quiz.category.color + '">' + quiz.category.icon + ' ' + esc(quiz.category.name) +
        ' • ' + quiz.difficulty.icon + ' ' + esc(quiz.difficulty.label) + '</span><a class="quit" id="quitLink" href="#/dashboard">✖ Quit</a></div>' +
      '<div class="card vs-bar"><div class="player me"><div class="face" id="playerFace"></div><div><span class="name" id="playerName"></span><span class="score" id="playerScore">0</span></div></div>' +
        '<div class="timer" id="timer"><svg viewBox="0 0 84 84" aria-hidden="true"><circle class="ring-bg" cx="42" cy="42" r="34"></circle>' +
        '<circle class="ring-fg" id="ringFg" cx="42" cy="42" r="34" stroke-dasharray="213.63" stroke-dashoffset="0"></circle></svg><div class="timer-num" id="timeNum">--</div></div>' +
        '<div class="player opp right"><div class="face" id="oppFace"></div><div><span class="name" id="oppName"></span><span class="score" id="oppScore">0</span></div></div></div>' +
      '<div class="progress"><div class="progress-fill" id="progressFill"></div></div>' +
      '<div class="q-meta"><span id="qCount"></span><span>⭐ Faster answers earn bonus points • press A-D to answer</span></div>' +
      '<div class="card q-card" id="qCard"><h2 class="q-text" id="qText"></h2><div class="options" id="options"></div>' +
        '<div class="feedback" id="feedback" hidden><div class="row"><strong id="fbMain"></strong><button class="btn btn-primary" id="nextBtn" type="button">Next ➜</button></div>' +
        '<div class="opp-line" id="fbOpp"></div></div></div></div>';
    $('#quitLink').addEventListener('click', function (e) {
      if (!confirm('Leave this battle? Your progress will not be saved.')) e.preventDefault();
    });
    runBattle(quiz);
  });
};

function runBattle(quiz) {
  var LETTERS = ['A', 'B', 'C', 'D'];
  var RING = 2 * Math.PI * 34;
  var index = quiz.current, timeLeft = 0, ticker = null, nextTimer = null, locked = false;
  var el = function (id) { return document.getElementById(id); };

  el('playerName').textContent = quiz.player.name;
  el('playerFace').textContent = quiz.player.avatar;
  el('oppName').textContent = quiz.opponent.name;
  el('oppFace').textContent = quiz.opponent.avatar;
  el('playerScore').textContent = quiz.player_score;
  el('oppScore').textContent = quiz.opponent_score;
  el('nextBtn').addEventListener('click', goNext);

  function onKey(e) {
    if (locked) return;
    var k = e.key.toLowerCase(), i = 'abcd'.indexOf(k);
    if (i === -1) i = ['1', '2', '3', '4'].indexOf(k);
    var btn = $$('.option')[i];
    if (btn && !btn.disabled) btn.click();
  }
  document.addEventListener('keydown', onKey);
  S.cleanup = function () {
    clearInterval(ticker); clearTimeout(nextTimer);
    document.removeEventListener('keydown', onKey);
  };

  if (index >= quiz.total) { location.hash = '#/results'; return; }
  showQuestion();

  function showQuestion() {
    locked = false;
    var q = quiz.questions[index];
    el('qCount').textContent = 'Question ' + (index + 1) + ' of ' + quiz.total;
    el('progressFill').style.width = (index / quiz.total * 100) + '%';
    el('qText').textContent = q.text;
    el('feedback').hidden = true;
    el('feedback').className = 'feedback';
    var box = el('options');
    box.innerHTML = '';
    q.options.forEach(function (text, i) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'option';
      var l = document.createElement('span'); l.className = 'letter'; l.textContent = LETTERS[i];
      var t = document.createElement('span'); t.textContent = text;
      b.appendChild(l); b.appendChild(t);
      b.addEventListener('click', function () { submit(i); });
      box.appendChild(b);
    });
    var card = el('qCard');
    card.classList.remove('enter'); void card.offsetWidth; card.classList.add('enter');
    startTimer();
  }

  function startTimer() {
    clearInterval(ticker);
    timeLeft = quiz.time;
    drawTimer(false);
    ticker = setInterval(function () {
      timeLeft--;
      drawTimer(true);
      if (timeLeft <= 0) { clearInterval(ticker); submit(-1); }     /* -1 = time is up */
    }, 1000);
  }
  function drawTimer(animate) {
    var ring = el('ringFg');
    ring.style.transition = animate ? '' : 'none';
    ring.style.strokeDashoffset = RING * (1 - timeLeft / quiz.time);
    el('timeNum').textContent = timeLeft;
    var t = el('timer');
    t.classList.toggle('warn', timeLeft <= quiz.time * 0.5 && timeLeft > quiz.time * 0.25);
    t.classList.toggle('danger', timeLeft <= quiz.time * 0.25);
  }

  function submit(choice) {
    if (locked) return;
    locked = true;
    clearInterval(ticker);
    el('timer').classList.remove('danger');
    $$('.option').forEach(function (b) { b.disabled = true; });
    api('/api/answer', { index: index, choice: choice, time_left: Math.max(timeLeft, 0) }).then(function (res) {
      if (res.error) { location.reload(); return; }
      reveal(choice, res);
    });
  }

  function reveal(choice, res) {
    $$('.option').forEach(function (b, i) {
      if (i === res.correct_index) b.classList.add('correct');
      else if (i === choice) b.classList.add('wrong');
      else b.classList.add('dim');
    });
    setScore('playerScore', res.player_score);
    setScore('oppScore', res.opponent_score);
    var fb = el('feedback');
    var right = quiz.questions[index].options[res.correct_index];
    if (choice === -1) { el('fbMain').textContent = '⏰ Time is up! The answer was ' + right + '.'; fb.classList.add('bad'); }
    else if (res.correct) { el('fbMain').textContent = '🎉 Correct! +' + res.points + ' points'; fb.classList.add('good'); }
    else { el('fbMain').textContent = '😅 Not quite. The answer was ' + right + '.'; fb.classList.add('bad'); }
    el('fbOpp').textContent = quiz.opponent.avatar + ' ' + quiz.opponent.name + ' ' +
      (res.bot_correct ? 'answered correctly (+' + res.bot_points + ')' : 'missed this one');
    el('nextBtn').textContent = res.finished ? 'See results 🏁' : 'Next ➜';
    fb.hidden = false;
    clearTimeout(nextTimer);
    nextTimer = setTimeout(goNext, 3200);          /* moves on by itself; the button is a shortcut */
  }

  function goNext() {
    clearTimeout(nextTimer);
    index++;
    if (index >= quiz.total) { location.hash = '#/results'; return; }
    showQuestion();
  }
  function setScore(id, value) {
    var s = el(id);
    if (s.textContent !== String(value)) {
      s.textContent = value;
      s.classList.remove('bump'); void s.offsetWidth; s.classList.add('bump');
    }
  }
}

/* SCREEN 9 - Results and scoreboard */
SCREENS.results = function (app, alive) {
  return api('/api/results').then(function (d) {
    if (!alive()) return;
    if (d.error) { toast(d.error, 'info'); location.hash = '#/dashboard'; return; }
    S.category = d.category_key;
    var L = 'ABCD', u = S.user;
    var trophy = d.outcome === 'win' ? '🏆' : d.outcome === 'draw' ? '🤝' : '💪';
    var title = d.outcome === 'win' ? 'You won the battle!' : d.outcome === 'draw' ? 'It is a draw!' : esc(d.bot[0]) + ' won this round';
    var sub = d.outcome === 'win' ? 'Fantastic speed and accuracy.' : d.outcome === 'draw' ? 'Evenly matched. Play again to break the tie.' : 'Review the answers below and challenge a rematch.';
    app.innerHTML =
      '<section class="card winner ' + d.outcome + '"><div class="trophy">' + trophy + '</div><h2>' + title + '</h2><p>' + sub + '</p><div class="chips">' +
        '<span class="chip">' + d.category.icon + ' ' + esc(d.category.name) + '</span><span class="chip">' + d.difficulty.icon + ' ' + esc(d.difficulty.label) +
        '</span><span class="chip">🎯 ' + d.right + '/' + d.total + ' correct</span><span class="chip">🏆 ' + (d.rank ? 'Rank #' + d.rank : 'Unranked') + '</span></div></section>' +
      '<section class="duel"><div class="duel-side me ' + (d.mine > d.theirs ? 'lead' : '') + '"><div class="face">' + esc(u.avatar) + '</div><b>' + esc(u.username) +
        ' (you)</b><span class="score">' + d.mine + '</span>points</div><div class="vs-badge">VS</div>' +
      '<div class="duel-side opp ' + (d.theirs > d.mine ? 'lead' : '') + '"><div class="face">' + d.bot[1] + '</div><b>' + esc(d.bot[0]) + '</b><span class="score">' + d.theirs + '</span>points</div></section>' +
      '<div class="actions-row"><a class="btn btn-primary btn-lg" href="#/difficulty">🔁 Play again</a><a class="btn btn-mint btn-lg" href="#/categories">🎯 New category</a>' +
        '<a class="btn btn-peach btn-lg" href="#/leaderboard">🏆 Leaderboard</a><a class="btn btn-ghost btn-lg" href="#/dashboard">🏠 Dashboard</a></div>' +
      '<section class="card" style="margin-top:22px"><h3 style="margin-bottom:14px">Answer review</h3>' +
      d.review.map(function (r, n) {
        var status = r.choice === -1 ? '⏰ You ran out of time' : r.got_it ? '✅ You got it right (+' + r.points + ')' : '❌ Your answer was ' + L[r.choice];
        return '<div class="review-item"><h3>Q' + (n + 1) + '. ' + esc(r.text) + '</h3><div class="opts">' +
          r.options.map(function (o, i) {
            var cls = i === r.correct_index ? 'right' : i === r.choice ? 'mine-wrong' : '';
            return '<span class="opt-chip ' + cls + '">' + L[i] + '. ' + esc(o) + (i === r.correct_index ? ' ✓' : '') + '</span>';
          }).join('') + '</div><p class="review-meta">' + status + ' &nbsp;•&nbsp; ' + d.bot[1] + ' ' + esc(d.bot[0]) + ': ' +
          (r.bot_correct ? 'correct (+' + r.bot_points + ')' : 'missed') + '</p></div>';
      }).join('') + '</section>';
    if (d.outcome === 'win') confetti();
  });
};

/* SCREEN 10 - Leaderboard */
SCREENS.leaderboard = function (app, alive) {
  return api('/api/leaderboard' + (S.lbCat ? '?category=' + encodeURIComponent(S.lbCat) : '')).then(function (d) {
    if (!alive()) return;
    var cats = S.meta.categories;
    app.innerHTML =
      '<div class="page-head"><h2>Leaderboard 🏆</h2><p>Ranked by total points from all battles. Top 10 players are shown.</p></div>' +
      '<div class="tabs"><a class="tab ' + (!S.lbCat ? 'on' : '') + '" href="#/leaderboard" data-cat="">🌈 All topics</a>' +
      Object.keys(cats).map(function (k) {
        return '<a class="tab ' + (S.lbCat === k ? 'on' : '') + '" href="#/leaderboard" data-cat="' + k + '">' + cats[k].icon + ' ' + esc(cats[k].name) + '</a>';
      }).join('') + '</div>' +
      '<div class="card my-rank"><div><b>Your position</b><div class="muted">' + (d.my_rank ? 'out of ' + d.total_players + ' players' : 'Play a battle in this topic to get ranked') +
        '</div></div><div class="lb-points">' + (d.my_rank ? '#' + d.my_rank : '-') + '</div></div>' +
      (d.rows.length ? d.rows.map(function (r, i) {
        var me = r.id === S.user.id;
        var medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : (i + 1);
        return '<div class="lb-row ' + (i < 3 ? 'top' + (i + 1) : '') + ' ' + (me ? 'me' : '') + '"><div class="medal">' + medal + '</div><div class="lb-user"><span class="face">' +
          esc(r.avatar) + '</span><span>' + esc(r.username) + (me ? ' (you)' : '') + '<small>' + r.games + ' battle' + (r.games === 1 ? '' : 's') + ' • ' + r.wins +
          ' win' + (r.wins === 1 ? '' : 's') + '</small></span></div><div class="lb-points">' + r.points + '<small>points</small></div></div>';
      }).join('') : '<div class="card empty">Nobody has played this topic yet. Be the first on the board! 🌟</div>') +
      '<div class="actions-row"><a class="btn btn-primary btn-lg" href="#/categories">🎮 Play a battle</a></div>';
    $$('.tab', app).forEach(function (t) {
      t.addEventListener('click', function (e) { e.preventDefault(); S.lbCat = t.dataset.cat; render(); });
    });
  });
};

/* ---------- Start the app ---------- */
window.addEventListener('pagehide', function () {          /* tell Python the window was closed */
  if (navigator.sendBeacon) navigator.sendBeacon('/api/bye', '{}');
});
api('/api/meta').then(function (m) { S.meta = m; return loadUser(); }).then(render);
})();

</script>
</body>
</html>
'''

# =============================================================================
# SECTION 6 - WEB SERVER AND APP WINDOW
# =============================================================================
SHUTDOWN = {"timer": None, "server": None}


def cancel_shutdown():
    if SHUTDOWN["timer"]:
        SHUTDOWN["timer"].cancel()
        SHUTDOWN["timer"] = None


def schedule_shutdown():
    """Called when the app window closes. A short delay lets a page refresh survive."""
    cancel_shutdown()
    SHUTDOWN["timer"] = threading.Timer(4.0, lambda: SHUTDOWN["server"].shutdown())
    SHUTDOWN["timer"].daemon = True
    SHUTDOWN["timer"].start()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):         # keep the console quiet
        pass

    def _send(self, code, payload, content_type="application/json; charset=utf-8"):
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _handle(self, method):
        cancel_shutdown()
        parsed = urlparse(self.path)
        path = parsed.path
        if method == "GET" and path in ("/", "/index.html"):
            return self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/favicon.ico":
            return self._send(204, b"", "image/x-icon")
        if path == "/api/bye":                      # the window was closed
            schedule_shutdown()
            return self._send(200, {"ok": True})

        route = ROUTES.get((method, path))
        if not route:
            return self._send(404, {"error": "Not found"})
        func, needs_login = route

        body = {}
        if method == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                body = {}
            if not isinstance(body, dict):
                body = {}

        token = self.headers.get("X-Token", "")
        user = None
        if token in SESSIONS:
            with closing(connect()) as db:
                row = db.execute("SELECT * FROM users WHERE id = ?", (SESSIONS[token],)).fetchone()
            user = dict(row) if row else None
        if needs_login and not user:
            return self._send(401, {"error": "Please log in."})
        try:
            code, data = func(Req(token, user, body, parse_qs(parsed.query)))
        except Exception as exc:                     # never crash the whole app
            print("Server error:", exc)
            code, data = 500, {"error": "Something went wrong. Please try again."}
        self._send(code, data)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


def find_app_browser():
    """Find Chrome or Edge so the game can open in its own app-style window."""
    candidates = []
    if sys.platform.startswith("win"):
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                     os.environ.get("LocalAppData")):
            if base:
                candidates += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                               os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    elif sys.platform == "darwin":
        candidates += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                       "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    else:
        candidates += [shutil.which(n) for n in
                       ("google-chrome", "chromium", "chromium-browser", "microsoft-edge")]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def open_window(url):
    exe = find_app_browser()
    if exe:
        try:
            subprocess.Popen([exe, "--app=" + url, "--window-size=1180,820",
                              "--user-data-dir=" + os.path.join(BASE_DIR, "app_window_data"),
                              "--no-first-run", "--no-default-browser-check"])
            return
        except OSError:
            pass
    webbrowser.open(url)                      # fallback: your normal browser


def make_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)   # port 0 = pick any free port
    server.daemon_threads = True
    SHUTDOWN["server"] = server
    return server


def main():
    init_db()
    server = make_server()
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    print("=" * 60)
    print("  Quiz Battle is running  ->  " + url)
    print("  Close the Quiz Battle window to stop (or press Ctrl+C here).")
    print("=" * 60)
    open_window(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    print("Quiz Battle closed. Bye!")


if __name__ == "__main__":
    main()

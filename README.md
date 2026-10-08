# 🎯 Anti-Procrastination Coach (APC)

> A Python desktop application to help you beat procrastination with face detection, voice reminders, Pomodoro timers, and detailed productivity analytics.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Login & Register** | Secure bcrypt-hashed account system |
| 👁️ **Face Detection** | OpenCV Haar Cascade — detects presence & attention |
| 👀 **Eye Tracking** | Drowsiness detection using eye cascade |
| ⌨️ **Activity Monitoring** | Keyboard/mouse/screen activity scoring |
| 🔊 **Voice Reminders** | pyttsx3 offline TTS with smart message pools |
| 🍅 **Pomodoro Timer** | Configurable work/break cycles with audio cues |
| 📊 **Analytics Dashboard** | Matplotlib charts (score trend, focus hours, distractions) |
| 📋 **Reports** | Daily/weekly reports with PDF export via ReportLab |
| 🗄️ **SQLite Storage** | Fully local — no cloud dependency |

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note (Windows):** the optional desktop-toast dependency `win10toast` is
> installed automatically on Windows via its environment marker.

### 2. Run the application

```bash
python main.py
```

### 3. First use
1. Click **"Create Account"** and register.
2. Log in with your credentials.
3. On the Dashboard, click **"▶ Start Focus Session"** — your webcam will activate.
4. The app will monitor your presence, track activity, and speak reminders when you get distracted.

---

## 📂 Project Structure

```
AntiProcrastinationCoach/
│
├── main.py                     ← App entry point
├── validate_imports.py         ← Import smoke-test (pip install check)
├── ruff.toml                   ← Lint configuration
├── apc_data.db                 ← SQLite database (auto-created)
│
├── gui/
│   ├── styles.py               ← Shared dark theme stylesheet
│   ├── preferences.py          ← QSettings-backed user preferences
│   ├── login_window.py         ← Animated login / register screen
│   ├── dashboard.py            ← Main hub (camera, timer, stats)
│   ├── analytics_window.py     ← Productivity charts
│   ├── settings_window.py      ← User preferences
│   └── reports_window.py       ← Daily / weekly reports + PDF export
│
├── face_detection/
│   ├── detector.py             ← Haar Cascade face detector
│   ├── eye_tracking.py         ← Eye/drowsiness detection
│   └── camera_handler.py       ← Thread-safe webcam capture
│
├── activity_monitor/
│   ├── keyboard_tracker.py     ← Keystroke rate (pynput)
│   ├── mouse_tracker.py        ← Click/move tracking (pynput)
│   └── screen_monitor.py       ← Screen pixel-diff activity score
│
├── reminders/
│   ├── voice_reminder.py       ← pyttsx3 TTS reminder engine
│   ├── notification.py         ← Win10 desktop toast notifications
│   └── scheduler.py            ← Periodic job scheduler
│
├── analytics/
│   ├── productivity_score.py   ← Weighted multi-signal scorer
│   ├── report_generator.py     ← Daily/weekly report builder + PDF
│   └── charts.py               ← Matplotlib chart → QPixmap helpers
│
├── database/
│   ├── db_connection.py        ← SQLite connection + table init
│   ├── user_model.py           ← User CRUD + bcrypt auth
│   ├── session_model.py        ← Focus session CRUD + stats
│   └── report_model.py         ← Report CRUD
│
├── resources/
│   ├── images/
│   ├── icons/
│   └── sounds/
│
├── reports/
│   ├── daily_reports/          ← PDF daily reports saved here
│   └── weekly_reports/
│
├── logs/
│   └── apc.log                 ← Runtime log file
│
├── requirements.txt
└── README.md
```

---

## 🗄️ Database Schema

### `users`
| Column | Type | Description |
|---|---|---|
| user_id | INTEGER PK | Auto-increment |
| name | TEXT | Display name |
| email | TEXT UNIQUE | Login email |
| password | TEXT | bcrypt hash |
| avatar | BLOB | Optional profile image |
| created_at | DATETIME | Registration time |

### `focus_sessions`
| Column | Type | Description |
|---|---|---|
| session_id | INTEGER PK | Auto-increment |
| user_id | INTEGER FK | Owner |
| start_time | DATETIME | Session start |
| end_time | DATETIME | Session end |
| duration_minutes | REAL | Computed duration |
| distractions | INTEGER | Count |
| productivity_score | REAL | 0–100 |
| notes | TEXT | Optional notes |

### `reports`
| Column | Type | Description |
|---|---|---|
| report_id | INTEGER PK | Auto-increment |
| user_id | INTEGER FK | Owner |
| report_date | DATE | Report date |
| focus_hours | REAL | Total focus |
| distractions | INTEGER | Total distractions |
| score | REAL | Average score |
| report_type | TEXT | `daily` or `weekly` |

---

## ⚙️ Productivity Scoring Model

The score (0–100) is computed from four signals:

| Signal | Weight | How measured |
|---|---|---|
| Face presence | **50%** | OpenCV face detection |
| Keyboard activity | **25%** | Keystrokes per minute |
| Mouse activity | **15%** | Clicks per minute |
| Screen change | **10%** | Pixel diff between screenshots |

| Score | Grade |
|---|---|
| ≥ 85 | 🔥 Excellent |
| 70–84 | 👍 Good |
| 50–69 | 😐 Average |
| 30–49 | ⚠️ Low |
| < 30 | 🚨 Very Low |

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **PyQt5** – GUI framework
- **OpenCV** – Face & eye detection
- **pyttsx3** – Offline text-to-speech
- **SQLite** – Embedded database
- **bcrypt** – Password hashing
- **matplotlib** – Productivity charts
- **ReportLab** – PDF report export
- **pynput** – Keyboard/mouse monitoring
- **pyautogui** – Screen capture
- **win10toast** – Windows desktop toasts

---

## 📝 License

MIT License — feel free to use, modify, and distribute.

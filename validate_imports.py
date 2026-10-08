"""Quick import validation – run after pip install completes."""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

errors = []

modules = [
    # database
    "database.db_connection",
    "database.user_model",
    "database.session_model",
    "database.report_model",
    # analytics
    "analytics.productivity_score",
    "analytics.charts",
    "analytics.report_generator",
    # reminders
    "reminders.voice_reminder",
    "reminders.notification",
    "reminders.scheduler",
    # face detection
    "face_detection.detector",
    "face_detection.eye_tracking",
    "face_detection.camera_handler",
    # activity monitoring
    "activity_monitor.keyboard_tracker",
    "activity_monitor.mouse_tracker",
    "activity_monitor.screen_monitor",
    # gui (styles, preferences and every window)
    "gui.styles",
    "gui.preferences",
    "gui.login_window",
    "gui.dashboard",
    "gui.analytics_window",
    "gui.reports_window",
    "gui.settings_window",
    # entry point
    "main",
]

for mod in modules:
    try:
        __import__(mod)
        print(f"  [OK]  {mod}")
    except Exception as e:
        print(f"  [FAIL]  {mod}  ->  {e}")
        errors.append((mod, str(e)))

print()
if errors:
    print(f"[WARNING]  {len(errors)} module(s) failed to import.")
    sys.exit(1)
else:
    print("[SUCCESS]  All modules imported successfully!")

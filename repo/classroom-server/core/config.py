"""
core/config.py – global server settings.
Override any value here; class_config.json overrides per course.
"""

MQTT_BROKER   = "localhost"
MQTT_PORT     = 1883
MQTT_TOPIC    = "#"

# Directory that contains one sub-folder per class
CLASSES_DIR   = "classes"

# Scoring thresholds (overridable per class/lesson)
PASS_SCORE    = 70      # percent
BONUS_SCORE   = 90      # percent – triggers attendance bonus

# Canvas CSV export path
CANVAS_EXPORT = "exports/canvas_grades.csv"

# AI grading JSON export path
AI_EXPORT     = "exports/ai_grading.json"

# Server address published to devices in the assign message
# Override this with your classroom Wi-Fi IP
SERVER_IP   = "192.168.8.10"
SERVER_PORT = 5000

# Device slot limit (can be overridden per class in class_config.json)
MAX_SLOTS = 50

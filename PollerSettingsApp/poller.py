import json
import time
from pathlib import Path
from urllib.parse import urlparse
import pyautogui
from flask import Flask, jsonify
from flask_socketio import SocketIO
import threading
import os
import sys
import shutil
import os
os.chdir(os.path.dirname(__file__))
if not getattr(sys, 'frozen', False):
  # --- Ensure venv is prioritized for subprocesses and sys.path ---
  venv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'))
  if os.path.exists(venv_path) and sys.executable != venv_path:
    os.execv(venv_path, [venv_path] + sys.argv)


CONFIG_FILENAME = "aug_poller.json"
POLLER_SECTION_KEY = "pollerconfigs"
CHATBOT_SECTION_KEY = "chatbot"
if getattr(sys, 'frozen', False):
  # Running as a PyInstaller bundle
  BASE_DIR = os.path.dirname(sys.executable)
else:
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
prev_msg_time = 0
rec_counter = 0
voters = []
tally = {}

if pyautogui.size().width == 2560:
  SCREEN_COORDS = {
  '1': [720, 750],
  '2': [1275, 750],
  '3': [1825, 750],
  'r1': [720, 1150],
  'r2': [1275, 1150],
  'r3': [1825, 1150]
  }
elif pyautogui.size().width == 1920:
  SCREEN_COORDS = {
  '1': [550, 575],
  '2': [950, 575],
  '3': [1350, 575],
  'r1': [550, 860],
  'r2': [958, 860],
  'r3': [1364, 860]
}
else:
  SCREEN_COORDS = {
  '1': [0, 0],
  '2': [0, 0],
  '3': [0, 0],
  'r1': [0, 0],
  'r2': [0, 0],
  'r3': [0, 0]
}


def _click(button='left'):
  pyautogui.mouseDown(button=button)
  time.sleep(0.1)
  pyautogui.mouseUp(button=button)


def _read_chat() -> dict:
  # Prefer reading from aug_poller.json's chatbot section; fall back to ChatBot.json.
  # Always look for aug_poller.json in the PollerSettingsApp subfolder
  config_path = Path(os.path.dirname(__file__)) / CONFIG_FILENAME
  try:
    file_content = config_path.read_text(encoding="utf-8")
    data = json.loads(file_content)
    if isinstance(data, dict) and isinstance(data.get(CHATBOT_SECTION_KEY), dict):
      return data.get(CHATBOT_SECTION_KEY)
  except Exception as e:
    print(f"[poll] Error reading/parsing {CONFIG_FILENAME} at {config_path}: {e}")
    return {}


def _update_graphic() -> None:
  return  # Placeholder; no-op for now.

def emit_poll_options():
  socketio.emit('poll_options', list(tally.keys()))

def _run_aug_poll(duration_seconds: float, enable_rerolls: bool) -> None:
  global prev_msg_time, rec_counter, voters, tally
  if enable_rerolls:
    tally = {
      '1': 0,
      '2': 0,
      '3': 0,
      'r1': 0,
      'r2': 0,
      'r3': 0
    }
  else:
    tally = {
      '1': 0,
      '2': 0,
      '3': 0
    }

  voters.clear()

  emit_poll_options()  # Notify clients of the updated options

  start_time = time.time()
  if enable_rerolls:
    poll_interval = duration_seconds / 4
  else:
    poll_interval = duration_seconds
  print(f"[poll] started: duration={poll_interval}s config={enable_rerolls}")
  try:
    while start_time + poll_interval > time.time():
      chat_data = _read_chat()
      # Defensive check for required keys
      required_keys = ['chatter', 'msg_time', 'message']
      if not all(k in chat_data for k in required_keys):
        print(f"[poll] Skipping chat_data due to missing keys: {chat_data}")
        time.sleep(0.01)
        continue
      if chat_data['chatter'] not in voters and chat_data['msg_time'] != prev_msg_time:
        prev_msg_time = chat_data['msg_time']
        if str(chat_data['message']).lower() in tally.keys():
          voters.append(chat_data['chatter'])
          tally[str(chat_data['message']).lower()] += 1
          print(f"[poll] vote: {chat_data['chatter']} voted for {chat_data['message']}")
      _update_graphic()
      time.sleep(0.01)
    winner = str(max(tally, key=tally.get))
    pyautogui.moveTo(SCREEN_COORDS[winner][0], SCREEN_COORDS[winner][1])
    _click()
    if enable_rerolls and rec_counter < 3 and winner.startswith('r'):
      rec_counter += 1
      print(f"[poll] rerolling poll (attempt {rec_counter})")
      _run_aug_poll(duration_seconds, enable_rerolls)
    else:
      print(f"[poll] winner: option {winner} with {tally[winner]} votes")
      rec_counter = 0
  except Exception as e:
    print(f"[poll] encountered error: {e}")
  finally:
    print("[poll] ending script.")
    exit(0)  # Forcefully terminate the script


# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/poll_percentages', methods=['GET'])
def get_percentages():
  total_votes = sum(tally.values())
  percentages = {key: (value / total_votes * 100) if total_votes > 0 else 0 for key, value in tally.items()}
  return jsonify(percentages)

@app.route('/')
def index():
  return "Poller Server is running. Use /poll_percentages or WebSocket for updates."

@socketio.on('connect')
def handle_connect():
  print("Client connected")

def send_poll_updates():
  while True:
    total_votes = sum(tally.values())
    percentages = {key: (value / total_votes * 100) if total_votes > 0 else 0 for key, value in tally.items()}
    socketio.emit('poll_update', percentages)
    time.sleep(1)  # Send updates every second

@app.route('/start_poll', methods=['POST'])
def start_poll():
  from flask import request
  try:
    data = request.get_json()
    duration = data.get('duration', 30)  # Default to 30 seconds if not provided
    enable_rerolls = data.get('enable_rerolls', False)  # Default to False if not provided
    print(f"[poll] Starting poll for {duration} seconds with rerolls={'enabled' if enable_rerolls else 'disabled'}")
    _run_aug_poll(duration, enable_rerolls)
    return {"message": "Poll started successfully."}, 200
  except Exception as e:
    print(f"[poll] Failed to start poll: {e}")
    return {"error": "Failed to start poll."}, 500

@app.route('/poll_options', methods=['GET'])
def get_poll_options():
  return jsonify(list(tally.keys()))

if __name__ == '__main__':
  socketio.start_background_task(send_poll_updates)
  socketio.run(app, host='127.0.0.1', port=5000)
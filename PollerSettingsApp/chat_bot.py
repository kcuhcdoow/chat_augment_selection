from twitchAPI.twitch import Twitch, TwitchUser
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand, JoinEvent, LeftEvent
import asyncio
import json
import time
from pathlib import Path
import os
import sys
import shutil
# --- Ensure venv is prioritized for subprocesses and sys.path ---
venv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'))
if os.path.exists(venv_path) and sys.executable != venv_path:
  os.execv(venv_path, [venv_path] + sys.argv)
import sys

APP_ID = 'br7upd0u5q4d3d9d4vjxxvgv7oz3nk'
APP_SECRET = 'zw56jq4m8gmjpxbs2h5a40gf24d8sy'
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]#, AuthScope.USER_WRITE_CHAT, AuthScope.USER_MANAGE_WHISPERS]
TARGET_CHANNEL = 'Frodan'
if getattr(sys, 'frozen', False):
  # Running as a PyInstaller bundle
  BASE_DIR = os.path.dirname(sys.executable)
else:
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
write_json = {
  'chatter': '',
  'message': '',
  'msg_time': 0
}


def _load_json_file(path: Path) -> dict:
  if not path.exists():
    return {}
  try:
    data = json.loads(path.read_text(encoding='utf-8'))
    return data if isinstance(data, dict) else {}
  except Exception:
    return {}


def _atomic_write_json(path: Path, payload: dict) -> None:
  tmp = path.with_suffix(path.suffix + '.tmp')
  tmp.write_text(json.dumps(payload, indent=2), encoding='utf-8')
  tmp.replace(path)


def write_chatbot_section_to_aug_poller(chat_state: dict) -> None:
  """Merge-write chatbot state into aug_poller.json without touching pollerconfigs."""
  config_path = Path(__file__).with_name('aug_poller.json')
  root = _load_json_file(config_path)

  root['chatbot'] = {
    'chatter': str(chat_state.get('chatter', '')),
    'message': str(chat_state.get('message', '')),
    'msg_time': float(chat_state.get('msg_time', 0) or 0),
  }

  _atomic_write_json(config_path, root)

# this will be called when the event READY is triggered, which will be on bot start
async def on_ready(ready_event: EventData):
  print('Bot is ready for work, joining channels')
  # join our target channel, if you want to join multiple, either call join for each individually
  # or even better pass a list of channels as the argument
  await ready_event.chat.join_room(TARGET_CHANNEL)
  # you can do other bot initialization things in here
  # f = open(f'{directory}TimerStart.txt', 'w')
  # f.write('Start1')
  # f.close()


# this will be called whenever a message in a channel was send by either the bot OR another user
async def on_message(msg: ChatMessage):
  global write_json
  
  write_json['chatter'] = msg.user.name.strip()
  write_json['message'] = msg.text.strip()
  write_json['msg_time'] = time.time()
  try:
    write_chatbot_section_to_aug_poller(write_json)
  except Exception:
    pass
  # print(f'{msg.user.name}\n{msg.text}')


# this will be called whenever someone subscribes to a channel
async def on_sub(sub: ChatSub):
  print(f'New subscription in {sub.room.name}:\\n'
      f'  Type: {sub.sub_plan}\\n'
      f'  Message: {sub.sub_message}')


# this will be called whenever the !reply command is issued
async def test_command(cmd: ChatCommand):
  with open(f'Teams.json', 'r') as f:
    data = json.load(f)
    print(data)
    for key in data.keys():
      if cmd.user.name in data[key]:
        print(f'{cmd.user.name} you are team {key}!')
        await Twitch.send_chat_message(self=twitch, broadcaster_id='13576693', sender_id='1327736704', message=f'{cmd.user.name} you are team {key}!')
        return
    await Twitch.send_chat_message(self=twitch, broadcaster_id='13576693', sender_id='1327736704', message=f'{cmd.user.name} you have not signed up for the event yet! Type {list(data.keys())[0]} {list(data.keys())[1]} {list(data.keys())[2]} or {list(data.keys())[3]} in order to enter!')
    print(f'{cmd.user.name} you have not signed up for the event yet! Type {list(data.keys())[0]} {list(data.keys())[1]} {list(data.keys())[2]} or {list(data.keys())[3]} in order to enter!')

async def on_join(user: JoinEvent):
  print(f'{user.user_name}')

async def on_leave(user: LeftEvent):
  print(f'{user.user_name}')

# this is where we set up the bot
async def run():
  global twitch
  # set up twitch api instance and add user authentication with some scopes
  TWITCH_TOKEN_FILE = os.path.join(BASE_DIR, 'twitch_tokens.json')
  with open(TWITCH_TOKEN_FILE, 'r') as f:
      twitch_tokens = json.load(f)
  f.close()
  twitch = await Twitch(APP_ID, APP_SECRET)
  token = twitch_tokens['access_token']
  refresh_token = twitch_tokens['refresh_token']
  await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)
  # await twitch.send_whisper('46243367', '1290878940', 'Test')
  # create chat instance
  chat = await Chat(twitch)

  # register the handlers for the events you want

  # listen to when the bot is done starting up and ready to join channels
  chat.register_event(ChatEvent.READY, on_ready)
  # listen to chat messages
  chat.register_event(ChatEvent.MESSAGE, on_message)
  # listen to channel subscriptions
  # chat.register_event(ChatEvent.SUB, on_sub)
  # there are more events, you can view them all in this documentation

  # you can directly register commands and their handlers, this will register the !reply command
  chat.register_command('team', test_command)

  chat.register_event(JoinEvent, on_join)
  chat.register_event(LeftEvent, on_leave)


  # we are done with our setup, lets start this bot up!
  chat.start()
  

  # lets run till we press enter in the console
  try:
    input('press ENTER to stop\n')
  finally:
    # now we can close the chat bot and the twitch api client
    chat.stop()
    await twitch.close()
    

  # lets run our setup
# asyncio.run(run())
# f = open(f'{directory}TimerStart.txt', 'w')
# f.write('Pause')
# f.close()


asyncio.run(run())
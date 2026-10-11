"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: reverie.py
Description: This is the main program for running generative agent simulations
that defines the ReverieServer class. This class maintains and records all  
states related to the simulation.
"""
import json
import numpy
import datetime
import pickle
import time
import math
import os
import shutil
import traceback

from selenium import webdriver

from global_methods import *
from utils import *
from maze import *
from persona.persona import *

##############################################################################
#                                  REVERIE                                   #
##############################################################################

class ReverieServer: 
  def __init__(self, 
               fork_sim_code,
               sim_code):
    self.fork_sim_code = fork_sim_code
    fork_folder = f"{fs_storage}/{self.fork_sim_code}"

    self.sim_code = sim_code
    sim_folder = f"{fs_storage}/{self.sim_code}"
    copyanything(fork_folder, sim_folder)

    with open(f"{sim_folder}/reverie/meta.json") as json_file:  
      reverie_meta = json.load(json_file)

    with open(f"{sim_folder}/reverie/meta.json", "w") as outfile: 
      reverie_meta["fork_sim_code"] = fork_sim_code
      outfile.write(json.dumps(reverie_meta, indent=2))

    self.start_time = datetime.datetime.strptime(
                        f"{reverie_meta['start_date']}, 00:00:00",  
                        "%B %d, %Y, %H:%M:%S")
    self.curr_time = datetime.datetime.strptime(reverie_meta['curr_time'], 
                                                "%B %d, %Y, %H:%M:%S")
    self.sec_per_step = reverie_meta['sec_per_step']
    self.maze = Maze(reverie_meta['maze_name'])
    self.step = reverie_meta['step']

    self.personas = dict()
    self.personas_tile = dict()
    
    init_env_file = f"{sim_folder}/environment/{str(self.step)}.json"
    init_env = json.load(open(init_env_file))
    for persona_name in reverie_meta['persona_names']: 
      persona_folder = f"{sim_folder}/personas/{persona_name}"
      p_x = init_env[persona_name]["x"]
      p_y = init_env[persona_name]["y"]
      curr_persona = Persona(persona_name, persona_folder)

      self.personas[persona_name] = curr_persona
      self.personas_tile[persona_name] = (p_x, p_y)
      self.maze.tiles[p_y][p_x]["events"].add(curr_persona.scratch
                                              .get_curr_event_and_desc())

    self.server_sleep = 0.1

    os.makedirs(fs_temp_storage, exist_ok=True)
    
    curr_sim_code = dict()
    curr_sim_code["sim_code"] = self.sim_code
    with open(f"{fs_temp_storage}/curr_sim_code.json", "w") as outfile: 
      outfile.write(json.dumps(curr_sim_code, indent=2))
    
    curr_step = dict()
    curr_step["step"] = self.step
    with open(f"{fs_temp_storage}/curr_step.json", "w") as outfile: 
      outfile.write(json.dumps(curr_step, indent=2))


  def save(self): 
    sim_folder = f"{fs_storage}/{self.sim_code}"
    reverie_meta = dict() 
    reverie_meta["fork_sim_code"] = self.fork_sim_code
    reverie_meta["start_date"] = self.start_time.strftime("%B %d, %Y")
    reverie_meta["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")
    reverie_meta["sec_per_step"] = self.sec_per_step
    reverie_meta["maze_name"] = self.maze.maze_name
    reverie_meta["persona_names"] = list(self.personas.keys())
    reverie_meta["step"] = self.step
    reverie_meta_f = f"{sim_folder}/reverie/meta.json"
    with open(reverie_meta_f, "w") as outfile: 
      outfile.write(json.dumps(reverie_meta, indent=2))

    for persona_name, persona in self.personas.items(): 
      save_folder = f"{sim_folder}/personas/{persona_name}/bootstrap_memory"
      persona.save(save_folder)


  def start_path_tester_server(self): 
    pass


  def start_server(self, int_counter): 
    sim_folder = f"{fs_storage}/{self.sim_code}"
    game_obj_cleanup = dict()

    while (True): 
      if int_counter == 0: 
        break

      curr_env_file = f"{sim_folder}/environment/{self.step}.json"
      env_retrieved = False
      if check_if_file_exists(curr_env_file):
        try: 
          with open(curr_env_file) as json_file:
            new_env = json.load(json_file)
            env_retrieved = True
        except: 
          pass
      
        if env_retrieved: 
          for key, val in game_obj_cleanup.items(): 
            self.maze.turn_event_from_tile_idle(key, val)
          game_obj_cleanup = dict()

          for persona_name, persona in self.personas.items(): 
            curr_tile = self.personas_tile[persona_name]
            new_tile = (new_env[persona_name]["x"], 
                        new_env[persona_name]["y"])

            self.personas_tile[persona_name] = new_tile
            self.maze.remove_subject_events_from_tile(persona.name, curr_tile)
            self.maze.add_event_from_tile(persona.scratch
                                         .get_curr_event_and_desc(), new_tile)

            if not persona.scratch.planned_path: 
              game_obj_cleanup[persona.scratch
                               .get_curr_obj_event_and_desc()] = new_tile
              self.maze.add_event_from_tile(persona.scratch
                                     .get_curr_obj_event_and_desc(), new_tile)
              blank = (persona.scratch.get_curr_obj_event_and_desc()[0], 
                       None, None, None)
              self.maze.remove_event_from_tile(blank, new_tile)

          movements = {"persona": dict(), 
                       "meta": dict()}
          for persona_name, persona in self.personas.items(): 
            next_tile, pronunciatio, description = persona.move(
              self.maze, self.personas, self.personas_tile[persona_name], 
              self.curr_time)
            movements["persona"][persona_name] = {}
            movements["persona"][persona_name]["movement"] = next_tile
            movements["persona"][persona_name]["pronunciatio"] = pronunciatio
            movements["persona"][persona_name]["description"] = description
            movements["persona"][persona_name]["chat"] = (persona
                                                          .scratch.chat)

          movements["meta"]["curr_time"] = (self.curr_time 
                                             .strftime("%B %d, %Y, %H:%M:%S"))

          curr_move_file = f"{sim_folder}/movement/{self.step}.json"
          with open(curr_move_file, "w") as outfile: 
            outfile.write(json.dumps(movements, indent=2))

          self.step += 1
          self.curr_time += datetime.timedelta(seconds=self.sec_per_step)

          int_counter -= 1
          
      time.sleep(self.server_sleep)


  def open_server(self): 
    pass


if __name__ == '__main__':
  import threading
  import json
  import os
  from http.server import HTTPServer, BaseHTTPRequestHandler

  class VisualDashboardHandler(BaseHTTPRequestHandler):
      def do_GET(self):
          self.send_response(200)
          self.send_header("Content-type", "text/html; charset=utf-8")
          self.end_headers()
          
          sim_code = "render_simulation_run_1"
          sim_folder = f"environment/frontend_server/storage/{sim_code}"
          
          curr_time_str = "جاري التحميل..."
          step_val = 0
          movements_data = {}
          
          try:
              meta_file = f"{sim_folder}/reverie/meta.json"
              if os.path.exists(meta_file):
                  with open(meta_file, "r") as f:
                      meta_info = json.load(f)
                      curr_time_str = meta_info.get("curr_time", "غير معروف")
                      step_val = meta_info.get("step", 0)
                      
              prev_step = max(0, step_val - 1)
              move_file = f"{sim_folder}/movement/{prev_step}.json"
              if os.path.exists(move_file):
                  with open(move_file, "r") as f:
                      movements_data = json.load(f)
          except:
              pass

          persona_dict = movements_data.get("persona", {})
          
          html_content = f"""
          <!DOCTYPE html>
          <html lang="ar" dir="rtl">
          <head>
              <meta charset="UTF-8">
              <meta http-equiv="refresh" content="3">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>خريطة وحركة الشخصيات الحية</title>
              <style>
                  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, sans-serif; background: #090d16; color: #f8fafc; margin: 0; padding: 12px; direction: rtl; }}
                  .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); padding: 15px; border-radius: 14px; text-align: center; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(30,64,175,0.4); }}
                  .header h1 {{ margin: 0; font-size: 18px; color: #fff; }}
                  .badge {{ background: #10b981; color: white; padding: 3px 10px; border-radius: 20px; font-size: 11px; display: inline-block; margin-top: 5px; }}
                  .stats {{ display: flex; justify-content: space-between; background: #1e293b; padding: 10px 14px; border-radius: 10px; margin-bottom: 12px; font-size: 13px; border: 1px solid #334155; }}
                  .map-container {{ background: #0f172a; border: 2px solid #3b82f6; border-radius: 12px; height: 190px; position: relative; margin-bottom: 12px; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
                  .map-bg {{ position: absolute; width: 100%; height: 100%; opacity: 0.15; background-image: radial-gradient(#3b82f6 1px, transparent 1px); background-size: 20px 20px; }}
                  .agent-marker {{ position: absolute; color: white; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; transform: translate(-50%, -50%); box-shadow: 0 2px 8px rgba(0,0,0,0.5); transition: all 0.5s ease; white-space: nowrap; border: 1px solid #fff; }}
                  .card {{ background: #1e293b; border-radius: 12px; padding: 12px; margin-bottom: 10px; border: 1px solid #334155; }}
                  .p-name {{ color: #38bdf8; font-weight: bold; font-size: 15px; margin-bottom: 5px; border-bottom: 1px solid #334155; padding-bottom: 4px; }}
                  .p-info {{ font-size: 13px; margin: 4px 0; color: #cbd5e1; }}
                  .highlight {{ color: #fbbf24; }}
                  .chat-box {{ background: #0f172a; border-right: 3px solid #10b981; padding: 6px 10px; border-radius: 6px; margin-top: 6px; font-size: 12px; color: #34d399; font-style: italic; }}
                  .footer {{ text-align: center; font-size: 11px; color: #64748b; margin-top: 15px; }}
              </style>
          </head>
          <body>
              <div class="header">
                  <h1>🗺️ خريطة وعالم العملاء الافتراضيين</h1>
                  <div class="badge">🟢 البث الحي مفعل</div>
              </div>

              <div class="stats">
                  <div>⏱️ الوقت: <b style="color:#38bdf8">{curr_time_str}</b></div>
                  <div>🔄 الخطوة: <b style="color:#fbbf24">{step_val}</b></div>
              </div>

              <div class="map-container">
                  <div class="map-bg"></div>
                  <div style="position: absolute; top: 8px; right: 10px; font-size: 10px; color: #64748b;">خريطة إحداثيات الشخصيات</div>
          """
          
          colors = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b"]
          idx = 0
          if persona_dict:
              for p_name, p_info in persona_dict.items():
                  pos = p_info.get("movement", [50, 50])
                  x_pct = min(max(int((pos[0] / 120) * 100), 10), 90)
                  y_pct = min(max(int((pos[1] / 120) * 100), 10), 90)
                  color = colors[idx % len(colors)]
                  idx += 1
                  
                  short_name = p_name.split()[0]
                  html_content += f'<div class="agent-marker" style="top: {y_pct}%; left: {x_pct}%; background: {color};">📍 {short_name} ({pos[0]},{pos[1]})</div>'
          else:
              html_content += '<div style="color: #94a3b8; font-size: 13px; z-index: 2;">جاري تحميل مواقع الشخصيات...</div>'

          html_content += """
              </div>

              <h3 style="font-size: 14px; color: #94a3b8; margin: 10px 5px;">تفاصيل حركة وأنشطة الشخصيات:</h3>
          """

          if persona_dict:
              for p_name, p_info in persona_dict.items():
                  desc = p_info.get("description", "لا توجد تفاصيل")
                  pos = p_info.get("movement", [0, 0])
                  chat = p_info.get("chat", "")
                  html_content += f"""
                  <div class="card">
                      <div class="p-name">👤 {p_name}</div>
                      <div class="p-info">📍 الموقع (الإحداثيات): <b>{pos}</b></div>
                      <div class="p-info">🎯 النشاط الحالي: <span class="highlight">{desc}</span></div>
                      {f'<div class="chat-box">💬 "{chat}"</div>' if chat else ''}
                  </div>
                  """
          else:
              html_content += "<div class='card' style='text-align:center; color:#94a3b8;'>بانتظار اكتمال أول خطوة للمحاكاة...</div>"

          html_content += """
              <div class="footer">
                  تحدث الصفحة تلقائياً كل 3 ثوانٍ لعرض مواقع وأنشطة الشخصيات لحظة بلحظة.
              </div>
          </body>
          </html>
          """
          self.wfile.write(html_content.encode('utf-8'))

      def log_message(self, format, *args):
          return

  def run_visual_dashboard():
      port = int(os.environ.get("PORT", 10000))
      server = HTTPServer(("0.0.0.0", port), VisualDashboardHandler)
      print(f"==> Visual Dashboard server started on port {port}")
      server.serve_forever()

  dashboard_thread = threading.Thread(target=run_visual_dashboard, daemon=True)
  dashboard_thread.start()

  origin = "base_the_ville_isabella_maria_klaus"
  target = "render_simulation_run_1"

  rs = ReverieServer(origin, target)
  print("==> Starting automated Reverie simulation with Visual Dashboard on Render...")
  rs.start_server(10000)

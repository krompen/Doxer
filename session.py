import os
import json
from config import clients, logger
def get_all_sessions():
    sessions = []
    for client in clients:
        client_folder = os.path.join(session_dir, client["name"])
        if os.path.exists(client_folder):
            for file in os.listdir(client_folder):
                if file.endswith(".session"):
                    sessions.append({
                        "path": os.path.join(client_folder, file),
                        "api_id": client["api_id"],
                        "api_hash": client["api_hash"]
                    })
    return sessions
        
def check_and_create_session_files():
    sessions_dir = "Не_основные"
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
    
    session_files = [f for f in os.listdir(sessions_dir) if f.endswith('.session')]
    
    for session_file in session_files:
        session_name = session_file.replace('.session', '')
        json_file = os.path.join(sessions_dir, f"{session_name}.json")
        
        if not os.path.exists(json_file):
            with open(json_file, 'w') as f:
                json.dump({"name": session_name, "status": "Свободна"}, f)        

def init_sessions():
    base_dir = "Session"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    sessions = []
    for client in clients:
        client_dir = os.path.join(base_dir, client["name"])
        if not os.path.exists(client_dir):
            os.makedirs(client_dir)
            continue
        
        for file in os.listdir(client_dir):
            if file.endswith('.session'):
                session_name = file.replace('.session', '')
                json_file = os.path.join(client_dir, f"{session_name}.json")
                
                if not os.path.exists(json_file):
                    with open(json_file, 'w') as f:
                        json.dump({
                            "name": session_name,
                            "status": "Свободна",
                            "api_id": client["api_id"],
                            "api_hash": client["api_hash"]
                        }, f)
                
                sessions.append({
                    "path": os.path.join(client_dir, file),
                    "api_id": client["api_id"],
                    "api_hash": client["api_hash"],
                    "client": client["name"]
                })
    
    return sessions          
active_sessions = init_sessions()    
check_and_create_session_files()       



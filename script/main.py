import requests
import os
import subprocess
from dotenv import load_dotenv
import time

#setup
load_dotenv()
db_host = os.getenv("DB_HOST")
MODEL1 = os.getenv("MODEL1")
MODEL2 = os.getenv("MODEL2") 
MODEL3 = os.getenv("MODEL3")

kobold = "../koboldcpp.exe"
port1 = "5001"
port2 = "5002"
port3 = "5003"

models = [MODEL2, MODEL3, MODEL1]

layers = ["8", "25", "25"]

def run_model(model, port, layers):
    return subprocess.Popen([kobold, "--model", model, "--gpulayers", layers, "--port", port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

port_pairs = {"llama": port1, "gemma": port2, "mistral": port3}

def wait_for_api(port, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{port}/api/v1/models")
            if response.status_code == 200:
                return True
        except:
            time.sleep(2)
    return False

def ask_agent(port, question):
    url = f"http://localhost:{port}/v1/chat/completions"
    
    payload = {
        "messages": [
            {"role": "user", "content": question}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def get_response_text(response):
    try:
        return response['choices'][0]['message']['content']
    except (KeyError, IndexError):
        return "error getting response"

question = "should i be a powerlifter or a bodybuilder? answer decisively in one sentence at the start, then explain in three short bullet points why"
responses = []

ports = ["5001", "5002", "5003"]

for i in range(3):
    s = run_model(models[i], ports[i], layers[i])
    wait_for_api(ports[i])
    text = get_response_text(ask_agent(ports[i], question))
    responses.append(text)
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "koboldcpp.exe", "/T"],
            check=True,
            capture_output=True
        )
        print("terminated process.")

    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            print("process not found, did you choose correct .exe?")
        else:
            print(f"unexpected error {e.stderr.decode()}")
    time.sleep(1)

for i in range(3): 
    print(models[i])
    print("\n")
    print(responses[i])

print("test")
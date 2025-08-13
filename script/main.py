import requests
import os
import subprocess
from dotenv import load_dotenv
import time

start_time = time.perf_counter()

#setup
load_dotenv()
db_host = os.getenv("DB_HOST")
MODEL1 = os.getenv("MODEL1")
MODEL2 = os.getenv("MODEL2") 
MODEL3 = os.getenv("MODEL3")

kobold = "../koboldcpp.exe"

models = [MODEL2, MODEL3, MODEL1]

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

def ask_agent(port, question, model_path):
    url = f"http://localhost:{port}/v1/chat/completions"
    
    payload = {
        "model": model_path,
        "messages": [
            {"role": "user", "content": question}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def get_response_text(response):
    try:
        return response['choices'][0]['message']['content']
    except (KeyError, IndexError):
        return "error getting response"

question = ""
responses = []

#make this more general later!
s = subprocess.Popen(
    [kobold, "--model", models[0], "--model", models[1], "--model", models[2], "--gpulayers", "35", "--port", "5001"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
wait_for_api("5001")

for model in models:
    text = get_response_text(ask_agent("5001", question, model))
    responses.append(text)

for i in range(3): 
    print(models[i])
    print("\n")
    print(responses[i])

subprocess.run(["taskkill", "/F", "/IM", "koboldcpp.exe", "/T"],)


end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(elapsed_time)
# Trinity

Trinity is a local deliberation system that runs **three LLMs side-by-side** (analytical, diplomatic, and practical). Each one answers the same question, then they deliberate. If there’s disagreement, the third model can check whether the others are *logically the same* (even with different reasoning). Finally, Trinity synthesizes a single group answer.

---

## Requirements

* Python 3.10+
* [llama.cpp](https://github.com/ggerganov/llama.cpp) build with **Vulkan backend** (AMD GPUs need this).
* Gradio (for the UI)
* `sentence-transformers` (for semantic checks)
* `python-dotenv`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Setup

### Models

Put your `.gguf` models under `./models`. The defaults in `.env` expect:

```
MODEL1 = "../models/llama.gguf"
MODEL2 = "../models/mistral.gguf"
MODEL3 = "../models/zeph.gguf"
```

Edit `.env` if you want to swap models.

### Vulkan / AMD

To run on AMD cards with Vulkan:

1. Build llama.cpp with Vulkan:

```bash
cmake -B build -DGGML_VULKAN=ON
cmake --build build --config Release
```

2. Make sure these env vars are set (already in `init.py`):

```python
os.environ['LLAMA_CPP_VULKAN'] = '1'
os.environ['GGML_VULKAN_DEVICE'] = '0'
```

`GGML_VULKAN_DEVICE` picks which GPU if you have more than one.

3. Adjust `n_gpu_layers` in `init.py` to push as much as your VRAM can handle. Example:

```python
llm1 = Llama(model_path=MODEL1, n_gpu_layers=28, n_ctx=2048)
```

---

## Running

### CLI mode

Fastest way to test:

```bash
python main.py
```

It will prompt you for a question in the terminal.

### UI mode

Gradio UI for easier interaction:

```bash
python app.py
```

This opens a browser window at [http://127.0.0.1:7860](http://127.0.0.1:7860).

The UI shows:

* Each model’s clipped answer (first 4 lines)
* Any “condition” text if an outlier needed convincing
* The current status (`total_same`, `partial_same`, `disagreement`)
* The synthesized final decision

---

## How it Works

* **Round 1**: All three models answer independently.
* **Deliberation**: Each sees the others’ answers and revises.
* **Judge step**: Model 3 (or whichever is set) checks if the top-line choices are logically the same.
* **Conditions**: If one model disagrees, it can output a *condition* (what evidence would convince it). If that happens, Trinity defers or shows the condition.
* **Final decision**: If two or three agree, Trinity merges the answers into one definitive response.

---

## Notes

* Boot time is slower in `app.py` because Gradio spins up a local server and frontend. CLI (`main.py`) is quicker.
* All prompts (system, deliberation, condition, final) are defined in `.env`. Easy to swap personalities or tighten formats.
* If you’re running bigger models, drop `n_ctx` or `n_gpu_layers` in `init.py` if you run out of VRAM.
* By default, Vulkan runs on device 0. Change `GGML_VULKAN_DEVICE` if you have more than one AMD card.

---

## Example
<img width="1510" height="830" alt="image" src="https://github.com/user-attachments/assets/c078eea7-2b83-4d55-b41e-ec7c6d22888b" />

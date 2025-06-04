
---

# Prompt-to-3D Model Generator

## 🧠 Overview

This app takes a **user's text prompt**, enhances it using the **`llama3:latest` LLM via Ollama**, generates an **image**, and then converts the image into a **3D model (GLB)** using Openfabric APIs. All data is stored locally for easy access.

---

## ⚙️ Features

* **Prompt → Enhanced via LLM (`llama3:latest`)**
* **Image Generation via Openfabric**
* **Image → 3D Model (GLB format)**
* **Interactive Streamlit UI**
* **Local SQLite DB for history**

---

## 🗂️ Key Files

* `frontend.py` – Streamlit interface
* `llm_manager.py` – Uses Ollama (`llama3:latest`)
* `openfabric_manager.py` – Handles Openfabric API
* `memory_manager.py` – Manages generations DB
* `outputs/images/` – Saved PNG images
* `outputs/models/` – Saved `.glb` models

---

## 🛠️ Quick Start

```bash
pip install -r requirements.txt
streamlit run app/frontend.py
cd app && python ignite.py
```

---

## 📦 Output Locations

* **Images:** `app/outputs/images/`
* **3D Models:** `app/outputs/models/`
* **Database:** `app/generations.db`

---


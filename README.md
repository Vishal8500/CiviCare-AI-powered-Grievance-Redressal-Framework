# 🏛️ Civic Grievance Collector – AI-Driven Redressal System
A complete smart governance solution integrating **Telegram chatbot**, **AI-based issue classification**, **priority indexing**, and a **Streamlit dashboard** for analytics and visualization.

---
Developed by *M Vishal & Jeeva M*
---
## 🚀 Project Overview
This system automates grievance collection and prioritization for municipal governance using:
- **Telegram Bot** for citizen complaints  
- **Gemini API** for NLP-based issue extraction and polite AI replies  
- **Transformers (BERT)** for sentiment-based priority scoring  
- **MySQL** for structured grievance storage  
- **Streamlit Dashboard** for data analytics, heatmaps, and visualization  

---

## 🧩 System Architecture

Below illustrates the **end-to-end flow** of the Civic Grievance AI system —  
from complaint registration to AI prioritization, escalation, and analytics.

<p align="center">
  <img src="assets/arch.png" alt="System Architecture Flow" width="750"/>
</p>

---
```
## 🧰 Folder Structure
├── 📂 bot  
│ ├── init.py  
│ ├── main.py → Entry point to run Telegram bot  
│ ├── handlers.py → Handles commands, messages, and multi-step submissions  
│ ├── database.py → DB creation, saving, and retrieval functions  
│ ├── priority_index.py → AI-based priority calculation (sentiment + keywords)  
│ ├── genai_helper.py → Gemini API helpers for classification and replies  
│ ├── issue_config.py → Config for 20 civic issue types  
│ ├── dashboard.py → Streamlit dashboard for analytics  
│ └── utils.py → Gemini reply utility  
│  
├── .env → Environment variables  
├── .gitignore → Git ignore configuration  
├── requirements.txt → Python dependencies  
├── README.md → Documentation file  
└── venv/ → Virtual environment  
```
---

## ⚙️ Step 1: Setup Environment
1️⃣ Install Python 3.11+  
2️⃣ Create virtual environment and activate it  
3️⃣ Install dependencies  
4️⃣ Configure .env file

Example .env:
```
TELEGRAM_BOT_TOKEN="8331147973:AAHQ2eGRosrTE3Biu2xifNFwb2BJdOnyRYk"
DB_HOST="localhost"
DB_USER="root"
DB_PASSWORD=<DB PWD>
DB_NAME="grievance_db"
GEMINI_API_KEY=<ENTER API-KEY>
```

---

## 🧠 Step 2: Initialize Database
Start MySQL, then run:
```
python -c "from database import init_db; init_db()"
```

---

## 🤖 Step 3: Run Telegram Bot
```
python main.py
```

✅ The bot will log: “🤖 Bot is running...”  
Then test in Telegram:
```
/start
/register Garbage overflowing near bus stop
```

---

## 📊 Step 4: Launch Streamlit Dashboard
```
streamlit run dashboard.py
```
Open [http://localhost:8501](http://localhost:8501)

---

## 🧩 Key Functionalities
| Feature | Description |
|----------|--------------|
| **AI Issue Detection** | Uses Gemini API to identify issue type and location |
| **AI Polite Replies** | Gemini generates empathetic acknowledgement replies |
| **Priority Indexing** | BERT + keyword severity + frequency weighting |
| **MySQL Integration** | Stores all grievance records with metadata |
| **Streamlit Dashboard** | Displays complaints, charts, and maps dynamically |

---


## 💬 Telegram Bot Demo Flow

This demonstrates the **CiviCare Bot** interaction on Telegram 👇  

<p align="center">
  <img src="assets/bot_ui.jpg" alt="Telegram bot message flow" width="400"/>
</p>

🗣️ The bot automatically:
- Detects the issue type (e.g., *Fire Hazards*)  
- Requests photos or extra details based on configuration  
- Generates AI-based acknowledgments  
- Saves and prioritizes the complaint using NLP & BERT models  

---

## 📱 Quick Access via QR Code

Scan the QR below to access or test the **Telegram Bot** instantly: (Note: Check whether the backend is running)

<p align="center">
  <img src="assets/qr.png" alt="QR Code for Telegram Bot" width="200"/>
</p>

---


## 💡 Credits
Developed by **M Vishal & Jeeva M**  
Project: *AI-Based Civic Grievance Redressal System with Priority Analytics*



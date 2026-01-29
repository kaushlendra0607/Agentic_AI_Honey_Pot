# 🕸️ Agentic AI Honeypot (Team Jarvis)

> **An autonomous AI security agent that detects scams, engages attackers in multi-turn conversations, extracts intelligence, and reports findings in real-time.**

## 🚀 Overview
This project is a REST API built with **FastAPI** and **Llama-3 (via Groq)**. It acts as a "digital trap" for scammers.
1.  **Detects:** Analyzes incoming messages for scam intent (Urgency, Financial demands).
2.  **Engages:** Activates "Arthur", a confused 72-year-old persona, to waste the scammer's time.
3.  **Extracts:** Uses regex patterns to harvest UPI IDs, Bank Accounts, Phone Numbers, and Links.
4.  **Reports:** Sends real-time intelligence to the Central Command (Guvi Evaluation Endpoint).

---

## 🛠️ Tech Stack
* **Framework:** FastAPI (Python 3.10+)
* **AI Engine:** Groq API (Llama-3-70b-Versatile)
* **Validation:** Pydantic V2 (Strict Schema Compliance)
* **Intelligence:** Custom Regex Engine (International & Local formats)
* **Deployment:** Render / Uvicorn

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/agentic-honeypot.git](https://github.com/your-username/agentic-honeypot.git)
cd agentic-honeypot
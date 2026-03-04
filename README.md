# 🧠 AI Health Assistant Chatbot

An AI-powered web application designed to provide **disease awareness, symptom checking, and health-related guidance** using **Machine Learning and Retrieval-Augmented Generation (RAG)**.

This system allows users to interact with an intelligent chatbot that can answer medical queries, analyze symptoms, and provide disease information in a user-friendly interface.

---

# 📌 Project Overview

The **AI Health Assistant Chatbot** helps users understand health conditions and symptoms using AI technologies.

The system integrates:

• Machine Learning for disease prediction
• NLP-based chatbot for health queries
• Retrieval-Augmented Generation (RAG) for accurate responses
• Interactive web interface

This project was developed as part of the **Smart India Hackathon (SIH) – AI Driven Public Health Chatbot for Disease Awareness**.

---

# 🚀 Features

### 🤖 AI Chatbot

Users can ask health-related questions and receive intelligent responses.

### 🧬 Symptom Checker

Users enter symptoms and the system predicts possible diseases using a trained ML model.

### 📚 Disease Library

Provides detailed information about diseases including:

• symptoms
• causes
• prevention
• treatments

### 📊 Reports & Analytics

Admin dashboard shows:

• user activity
• chatbot usage
• quiz results
• feedback statistics

### 📝 Health Quiz

Interactive quiz to test health awareness.

### 📩 Feedback System

Users can submit feedback about the chatbot.

### 🔐 Authentication System

Includes:

• Signup
• Login
• JWT authentication
• Forgot password with OTP

### 📑 RAG Knowledge System

Medical PDFs are processed and converted into embeddings to provide accurate chatbot answers.

---

# 🏗️ System Architecture

User
↓
Frontend (HTML, CSS, JavaScript)
↓
FastAPI Backend
↓
ML Model + RAG Knowledge Base
↓
Database (SQLite)

---

# 🧠 Technologies Used

### Frontend

• HTML
• CSS
• JavaScript

### Backend

• FastAPI
• Python

### Machine Learning

• Scikit-learn
• Symptom2Disease dataset
• Trained classification model

### NLP / AI

• OpenRouter API
• GPT-based response generation
• Sentence Transformers for embeddings

### Vector Database

• Pinecone / Local vector store

### Database

• SQLite

---

# 📂 Project Structure

```
ai-health-assistantfinalbot
│
├── backend
│   ├── app
│   │   ├── api
│   │   ├── rag
│   │   ├── services
│   │   ├── utils
│   │   ├── models.py
│   │   ├── main.py
│   │   └── database.py
│
├── frontend
│   ├── css
│   ├── js
│   ├── chatbot.html
│   ├── login.html
│   ├── signup.html
│   └── reports.html
│
├── data
│   ├── medical_pdfs
│   ├── ml_assets
│   └── ingest_state.json
│
├── health.db
└── requirements.txt
```

---

# ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/ai-health-assistant.git
```

### Navigate to Project

```bash
cd ai-health-assistant
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Backend will run at:

```
http://127.0.0.1:8000
```

---

# ▶️ Run the Frontend

Open:

```
frontend/index.html
```

Or run using **Live Server**.

---

# 📊 Machine Learning Model

The system uses a trained classification model that predicts diseases based on symptoms.

Dataset used:

```
Symptom2Disease Dataset
```

Training script:

```
train.py
```

Model files:

```
disease_model.pkl
label_encoder.pkl
vectorizer.pkl
```

---

# 📚 RAG Knowledge Pipeline

Medical PDFs are processed through:

1️⃣ PDF Text Extraction
2️⃣ Text Chunking
3️⃣ Embedding Generation
4️⃣ Vector Storage
5️⃣ Retrieval during chatbot queries

This improves answer accuracy.

---

# 🔐 Authentication

User authentication includes:

• JWT token system
• secure password hashing
• email OTP verification
• protected routes

---

# 🎯 Future Improvements

• Multi-language support
• Voice-based chatbot
• Real-time health monitoring integration
• Mobile application version

---

# 👨‍💻 Author

**Janam Kusuma**

B.Tech – Computer Science Engineering
AI & Machine Learning Enthusiast

---

# 📜 License

This project is developed for **educational and research purposes**.

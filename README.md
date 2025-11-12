# 🍽️ SmartBites — AI-Powered Meal Planner & Nutrition Assistant

SmartBites is a **personalized meal planning web application** powered by **AI and RAG-based document querying**.
It helps users plan meals, explore nutrition insights, and generate AI-assisted recommendations — all within an interactive **Streamlit** interface powered by the **Google Gemini API**.

---

## 🎯 Project Objective

This Capstone project aims to integrate **AI-driven meal planning** with **nutritional guidance** to deliver:

* **Conversational AI Web App**: Streamlit-based chatbot using the Gemini API for nutrition Q&A and custom recommendations.
* **Smart Meal Planner**: AI-generated meal suggestions adapted to user preferences and dietary needs.
* **RAG Knowledge Base**: Upload and query nutrition or recipe documents through Retrieval-Augmented Generation.
* **Interactive Experience**: Intuitive web interface for healthy meal planning and daily food tracking.

---

## 👥 Team

* **Beatriz Marques** – 20231605
* **Constança Pereira da Silva** – 20231720
* **Maria Inês Santos** – 20231630
* **Mariana Calais-Pedro** – 20231641

---

## 📊 Methodology

### Capstone Development Timeline

Following the **NOVA IMS Capstone structure**, SmartBites was developed in three phases:

1. **📝 Week 3 – Initial Proposal**

   * Defined the project concept: AI-based meal planner & nutrition assistant
   * Formed the team and distributed roles
   * Drafted contribution plan and project scope

2. **🧩 Week 12 – Technical Blueprint**

   * Detailed architecture and module responsibilities
   * Integrated Gemini API and RAG pipeline for knowledge retrieval
   * Designed the Streamlit app structure and function-calling tools

3. **🚀 Final Delivery**

   * Fully deployed SmartBites application on Streamlit Cloud
   * Accompanied by final presentation and technical report

---

## 🧠 Technologies Used

| Category                      | Tools & Frameworks              |
| ----------------------------- | ------------------------------- |
| **Frontend & Deployment**     | Streamlit, Streamlit Cloud      |
| **AI Integration**            | Google Gemini API               |
| **Knowledge Retrieval (RAG)** | ChromaDB, LangChain / LangSmith |
| **Programming Language**      | Python                          |
| **Collaboration**             | Git, GitHub                     |
| **Environment Management**    | `venv`, `requirements.txt`      |

---

## 📁 Repository Structure

```tree
├── data/
│   └── sample_documents/
├── images/
│   └── smartbites_preview.png
├── notebooks/
│   ├── model_prototyping.ipynb
│   └── data_processing.ipynb
├── src/
│   ├── services/
│   │   ├── meal_service.py
│   │   ├── nutrition_service.py
│   │   └── ai_service.py
│   ├── tools/
│   │   ├── calorie_calculator.py
│   │   └── ingredient_parser.py
│   ├── utils/
│   │   ├── config.py
│   │   └── tracing.py
│   └── ai_client.py
├── report/
│   └── final_report.pdf
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

## 🔧 Architecture Overview

The SmartBites system follows a **modular AI architecture**, ensuring clear separation between layers:

```text
 ┌───────────────────────────────┐
 │         Streamlit UI          │
 │  (user input & visualization) │
 └──────────────┬────────────────┘
                │
                ▼
 ┌───────────────────────────────┐
 │     Service Layer (src/)      │
 │  - meal_service.py            │
 │  - nutrition_service.py       │
 │  Handles business logic       │
 └──────────────┬────────────────┘
                │
                ▼
 ┌───────────────────────────────┐
 │         AI Layer              │
 │   Gemini API + RAG (ChromaDB) │
 │   Natural language reasoning  │
 └──────────────┬────────────────┘
                │
                ▼
 ┌───────────────────────────────┐
 │     Tools & Utilities         │
 │  - Calorie calculators        │
 │  - Config & tracing           │
 └───────────────────────────────┘
```

---

## ⚙️ How to Run *SmartBites*

### 1️⃣ Create and Activate the Virtual Environment

**Windows**

```bash
python -m venv project-env
smartbites-env\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv project-env
source project-env/bin/activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the App

```bash
streamlit run streamlit_app.py
```

SmartBites will start in your browser at [http://localhost:8501](http://localhost:8501).

---

## 💡 Development Tips

* To stop the app: **Ctrl + C** in the terminal
* To check your Streamlit version:

  ```bash
  streamlit --version
  ```
* Update dependencies when new modules are added:

  ```bash
  pip freeze > requirements.txt
  ```

---

## 🤪 Git Workflow Guide

Ensure smooth collaboration across the team with these steps:

### 🔍 1. Check your branch

```bash
git branch
```

If needed, switch to your branch:

```bash
git checkout your-branch-name
```

### 🔄 2. Sync with the shared branch

```bash
git pull origin shared-branch-name
```

### 💾 3. Save and push your work

```bash
git add .
git commit -m "Add: meal planner UI"
git push origin your-branch-name
```

### 🔁 4. Merge your changes

```bash
git checkout shared-branch-name
git pull origin shared-branch-name
git merge your-branch-name
git push origin shared-branch-name
```

---

## 🚀 Deployment Notes

SmartBites is deployed on **Streamlit Cloud**.

* ✅ Ensure correct environment setup via `requirements.txt`
* ✅ Document all environment variables in `.env.example`
* ✅ Test RAG-based search and API integrations before deployment
* ✅ Use Streamlit access controls for visibility and version management

Deployment URL: *to be added upon final publication.*

---

## 📚 References

* [Google Gemini API Documentation](https://ai.google.dev/)
* [Streamlit Documentation](https://docs.streamlit.io/)
* [ChromaDB](https://docs.trychroma.com/)
* [LangChain Docs](https://python.langchain.com/)
* [Gemini Cookbook](https://github.com/google-gemini/cookbook)

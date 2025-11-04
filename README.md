# 🤖 Building a Custom AI Assistant Web App

Development of a domain-specific AI assistant using Streamlit, Gemini API, and RAG-based document querying. The project culminates in a deployed web application capable of intelligent conversation, tool execution, and document Q&A.

---

## 🎯 Project Objective

This project aims to apply advanced AI development techniques to deliver:

- **Conversational AI Web App**: A deployed Streamlit application with Gemini API integration and custom function-calling tools.
- **Domain-Specific Tool Suite**: AI-powered utilities tailored to a real-world use case (e.g., study buddy, travel planner, business assistant).
- **RAG-Enabled Knowledge System**: Intelligent document upload and querying using embeddings and retrieval-augmented generation.

---

## 📁 Repository Structure

```tree
├── data/
│   └── sample_documents/
├── images/
│   └── XX.png
├── notebooks/
│   ├── XX.ipynb
│   └── XX.ipynb
├── src/
│   ├── services/
│   ├── tools/
│   ├── utils/
│   └── ai_client.py
├── report/
│   └── final_report.pdf
├── README.md
├── streamlit_app.py
├── requirements.txt
└── .gitignore
```

---

## 👥 Team

- Beatriz Marques – 20231605  
- Constança Pereira da Silva - 20231720
- Maria Inês Santos - 20231630
- Mariana Calais-Pedro – 20231641

---

## 📊 Methodology

### Capstone Development Timeline

This project follows a milestone-based structure aligned with NOVA IMS Capstone guidelines:

1. **Week 3 – Initial Proposal**
   - Team formation
   - Preliminary app concept and problem statement
   - Role preferences and contribution plans

2. **Week 12 – Technical Blueprint**
   - Finalized problem definition and solution overview
   - Detailed team roles and responsibilities
   - Implementation plan and scope management

3. **Final Delivery**
   - Deployed Streamlit application
   - Pitch presentation and technical Q&A

---

## 🧠 Technologies Used

- **Google Gemini API** – Conversational AI and function calling  
- **Streamlit** – Web app framework and deployment  
- **ChromaDB** – Vector database for document embeddings  
- **LangChain / LangSmith** – RAG pipeline and tool orchestration  
- **Python** – Core programming language  
- **Git & GitHub** – Version control and collaboration

---

## 📚 References

- [Google AI Studio](https://ai.google.dev/)  
- [Streamlit Documentation](https://docs.streamlit.io/)  
- [ChromaDB Docs](https://docs.trychroma.com/)  
- [LangSmith Docs](https://docs.smith.langchain.com/)  
- [Gemini API Cookbook](https://github.com/google-gemini/cookbook)  
- [Python Crash Course, 3rd Edition](https://nostarch.com/pythoncrashcourse3e)

---

## 🚀 How to Run a *Streamlit* App

### 🧩 Steps

1. **Activate the environment**

    On Windows: 
    ```bash
    project-env\Scripts\activate
    ```

    On macOS/Linux:
    ```bash
    source project-env/bin/activate
    ```

2. **Run *Streamlit* app**

    ```bash
    streamlit run streamlit_app.py
    ```

    Starts the *Streamlit* server and launches your app in the browser (usually at [http://localhost:8501](http://localhost:8501/)).

---

### 💡 Tips

- To stop the app, press **Ctrl + C** in the terminal.
- To check your *Streamlit* version:

    ```bash
    streamlit --version
    ```

---


## 🧪 Git Workflow Guide

Follow these steps to collaborate smoothly with your team:

### 🔀 Step 1: Check your current branch

Before you start working, verify which branch you're on:

```bash
git branch
```
If you're already on your personal branch, proceed to Step 2. If not, switch to your branch:

```bash
git checkout your-branch-name
```
### 🔄 Step 2: Sync with the shared branch
Before you start working, pull the latest changes from the shared branch:
```bash
git pull origin shared-branch-name
```
Now you're ready to work!

### 💾 Step 3: Save and push your changes
When you're done working:
```bash
git add .
git commit -m "descriptive commit message"
git push origin your-branch-name
```
### 🔁 Step 4: Update the shared branch
After pushing your changes, merge them into the shared branch:
```bash
git checkout shared-branch-name
git pull origin shared-branch-name
git merge your-branch-name
git push origin shared-branch-name
```

---

## 🚀 Deployment Notes

The app will be deployed on **Streamlit Cloud**.

- Ensure proper environment setup using `venv` and `requirements.txt`  
- Monitor app performance and document all deployment steps  
- Include deployment instructions in the final report and repository  
- Use Streamlit’s sharing and access controls to manage visibility

This is the [deployment URL]().

---


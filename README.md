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



# TEMPLATE

# Professional Contract Analyzer

This is a **complete, production-ready AI application** demonstrating professional architecture patterns.

## Project Structure

```
contract_analyzer/
├── app.py                      # Streamlit UI (entry point)
├── .env.example                # Environment template
├── README.md                   # This file
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── contract_service.py     # Contract domain logic
│   ├── document_service.py     # PDF processing
│   └── ai_service.py           # All Gemini API calls
│
├── tools/                      # Function calling tools
│   ├── __init__.py
│   ├── date_calculator.py      # Date calculations
│   └── amount_calculator.py    # Financial calculations
│
└── utils/                      # Shared utilities
    ├── __init__.py
    ├── tracing.py              # Langfuse configuration
    └── config.py               # Environment variables
```

## Architecture Principles

### 1. Separation of Concerns
- **UI Layer (`app.py`)**: Only handles display and user interaction
- **Service Layer (`services/`)**: Contains all business logic
- **AI Layer (`ai_service.py`)**: Isolated AI/LLM operations
- **Tools Layer (`tools/`)**: Precise calculations

### 2. Dependency Injection
- Services receive dependencies in constructor
- Easy to test with mock dependencies
- Easy to swap implementations

### 3. Observability
- Every important function has `@observe()` decorator
- Full trace visibility in Langfuse
- Debug production issues easily

### 4. Reusability
- Services can be imported and used anywhere
- No coupling to Streamlit
- Works in CLI, API, or other UIs

## Setup

### 1. Install Dependencies

```bash
uv add google-genai streamlit langfuse python-dotenv
```

### 2. Configure Environment

```bash
# Copy example and fill in your keys
cp .env.example .env

# Edit .env with your API keys
```

### 3. Run Application

```bash
uv run streamlit run app.py
```

## How It Works

### Data Flow Example

When a user uploads a contract PDF:

```
1. User uploads PDF in Streamlit UI (app.py)
        ↓
2. app.py calls: service.analyze_contract(file_bytes)
        ↓
3. ContractService.analyze_contract() orchestrates:
   a. doc_service.validate_pdf(file_bytes)
   b. ai_service.extract_structured(file_bytes, schema)
   c. date_calc.days_until(expiry_date)
   d. amount_calc.calculate_total_value(...)
        ↓
4. Returns enriched contract data
        ↓
5. app.py displays results
```

**Every step is traced in Langfuse!**

### Tracing Flow

With `@observe()` decorators, Langfuse shows:

```
analyze_contract (parent)
├── validate_pdf
├── extract_structured
│   └── Gemini API call (input, output, tokens, latency)
├── days_until
└── calculate_total_value
```

## Testing Services

Services can be tested independently:

```python
# test_contract_service.py
from services.contract_service import ContractService

def test_analyze_contract():
    service = ContractService()

    with open("test_contract.pdf", "rb") as f:
        result = service.analyze_contract(f.read())

    assert "parties" in result
    assert "expiration_date" in result
```

No Streamlit required!

## Reusing Services

Use services in different contexts:

```python
# CLI script
from services.contract_service import ContractService

service = ContractService()

with open("contract.pdf", "rb") as f:
    data = service.analyze_contract(f.read())

print(f"Parties: {data['parties']}")
```

```python
# API endpoint (FastAPI)
from fastapi import FastAPI, UploadFile
from services.contract_service import ContractService

app = FastAPI()
service = ContractService()

@app.post("/analyze")
async def analyze(file: UploadFile):
    content = await file.read()
    return service.analyze_contract(content)
```

## Adding New Features

### Add a New Service

1. Create file in `services/`
2. Add `@observe()` to important methods
3. Import and use in other services or UI

### Add a New Tool

1. Create file in `tools/`
2. Add `@observe()` to functions
3. Use in service layer

### Extend UI

1. Keep business logic in services
2. UI only handles display and user input
3. Call service methods

## Key Takeaways

### ✅ Benefits of This Architecture

- **Testable**: Services work without UI
- **Maintainable**: Clear separation makes changes easy
- **Observable**: See everything in Langfuse
- **Reusable**: Services work in any interface
- **Team-friendly**: Different files for different concerns
- **Scalable**: Easy to add features without breaking things

### ❌ What We Avoided

- Monolithic single-file apps
- UI mixed with business logic
- Repeated client initialization
- Hardcoded values everywhere
- No visibility into what's happening
- Untestable code

## Learning Resources

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Langfuse Docs](https://langfuse.com/docs)
- [Streamlit Docs](https://docs.streamlit.io)

## Next Steps

**Use this as a template for your team project!**

1. Copy this structure
2. Replace "contract" with your domain
3. Define your schemas and business logic
4. Build your UI
5. Add your domain-specific tools
6. Deploy to Streamlit Cloud

**You have everything you need to build professional AI applications!** 🚀

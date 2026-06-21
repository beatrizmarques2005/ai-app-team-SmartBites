# SmartBites
### Capstone Project Class · Data Science Degree · NOVA IMS

***When motivation is low but hunger is high.***

**Team Name:** *SmartBites*

**Project Name:** *SmartBites*

**Project Domain:** Food & Meal Planning

## 📑 Table of Contents

- [Overview](#-overview)
- [Project's Architecture](#-projects-architecture)
- [Installation & Setup](#-installation--setup)
- [Deployment](#-deployment)
- [Repository Structure](#-repository-structure)
- [Team](#-team)

## 📋 Overview

*SmartBites* is a **personalized meal planning web application** designed to help university students manage meals despite busy and unpredictable schedules. Many students face repetitive meals, inefficient ingredient usage, and food waste due to limited time and lack of planning. *SmartBites* solves this by providing **practical, AI-driven meal plans and recipe suggestions** based on available ingredients, dietary preferences, and available cooking time.

Key features include:

* **AI-Powered Meal Planning**: Generates weekly meal suggestions adapted to user preferences, pantry contents, and time constraints.
* **Conversational Assistant**: Streamlit-based chatbot using the **Google *Gemini* API** to suggest recipes and assist with meal planning interactively.
* **Smart Pantry & Shopping Management**: Tracks ingredients, updates pantry items from receipts, and manages shopping lists to minimize waste.
* **Secure User Data Handling**: Authentication and per-user data persistence through ***Supabase***, keeping meal plans, pantry items, and shopping lists safe.
* **Interactive & Intuitive Experience**: Easy-to-use interface for planning meals, cooking assistance, and grocery management.

By combining **AI-driven reasoning** and a **friendly interactive interface**, *SmartBites* makes meal planning **fast, flexible, and stress-free** for students who want to cook efficiently and avoid food waste.

## 🏗️ Project's Architecture

This section presents the **design of our system architecture** along with the main technology choices. It highlights the layer structure, key components, and design decisions that support the application's functionality and scalability.

| **Category**       | **Technologies** |
|-------------------|----------------------------|
| **Backend**        | Python and Google *Gemini* API |
| **Frontend**       | *Streamlit* |
| **Database**       | *Supabase* |
| **Observability**  | *Langfuse* |
| **Deployment**  | *Streamlit Cloud Community* |

[View Full Architecture Details](docs/ARCHITECTURE.md)

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.13.5
- API keys for *AIService*

### Installation Steps

#### Environment Setup

```bash
# Clone repository
git clone https://github.com/beatrizmarques2005/ai-app-team-SmartBites.git
cd ai-app-team-smartbites

# Create and activate environment
python -m venv .venv
source .venv/bin/activate             # Mac
.venv\Scripts\activate on Windows     # Windows/Linux

# Install dependencies
pip install -r requirements.txt
```

#### Environment Variables
Create a `.env` file (just like the *.env.example* file):

```bash
# Google AI Configuration
GOOGLE_API_KEY="XXXXXXXXXXXXXXXXXX"
MODEL=gemini-2.5-flash-lite

# Langfuse Configuration (optional but recommended)
LANGFUSE_SECRET_KEY = "XXXXXXXXXXXXXXXXXX"
LANGFUSE_PUBLIC_KEY = "XXXXXXXXXXXXXXXXXX"
LANGFUSE_HOST = "https://cloud.langfuse.com"

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
TEMPERATURE=0.7
MAX_OUTPUT_TOKENS=2048

# SUPABASE Configuration
SUPABASE_URL="https://your-supabase-url.supabase.co"
SUPABASE_KEY="your-supabase-key"
```

### Run Locally
```bash
streamlit run streamlit/App.py
```

## 🚀 Deployment

**Live Application:** [Deployed Link](https://ai-app-smartbites.streamlit.app/)

**Deployment Platform:** *Streamlit Cloud Community*

## 📁 Repository Structure

```tree
ai-app-team-SmartBites/
│
├── data/                           # Sample documents and input files for testing.
│   └── sample_documents/
│
├── docs/                           # Project documentation, architecture, and guidelines.
│   ├── ARCHITECTURE.md
│   ├── SmartBites_TechnicalReport.pdf
│   ├── Project_Guidelines.pdf
│   └── Technical_Report_Guidelines.pdf
│
├── images/                         # Logo and diagrams.
│   ├── SmartBites_logo.png
│   ├── SmartBites_logo2.png
│   └── System_Architecture.png
│
├── src/
│   ├── db/                         # Database client and connection utilities.
│   │   └── client.py
│   ├── services/                   # Core service layer including AI orchestration.
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   └── system_instruction.txt
│   ├── tools/                      # Deterministic utility functions.
│   │   ├── cooking_assistant.py
│   │   ├── pantry_checker.py
│   │   ├── pantry_writer.py
│   │   ├── recipe_checker.py
│   │   ├── recipe_writer.py
│   │   ├── seasonal_finder.py
│   │   ├── shopping_writer.py
│   │   ├── user_checker.py
│   │   └── user_writer.py
│   ├── utils/                      # Helper modules for meal plan workflows, pending plans, and tracing/debugging.
│   │   ├── meal_plan_flow.py
│   │   ├── pending_meal_plan.py
│   │   └── tracing.py
│   ├── workflows/                  # Workflow scripts, including receipt parsing.
│   │   └── receipt_parser.py
│   └── authentication.py           # Handles user authentication logic.
│
├── streamlit/
│   ├── auth_/                      # Login and signup Streamlit pages.
│   │   ├── login.py
│   │   └── signup.py
│   ├── pages_/                     # Streamlit app pages.
│   │   ├── about_us.py
│   │   ├── chat.py
│   │   ├── pantry.py
│   │   ├── planner.py
│   │   ├── profile.py
│   │   ├── receipts.py
│   │   └── shopping_list.py
│   └── App.py                      # Main Streamlit application entry point.
│
├── .env.example                    # Example environment variables file.
├── .gitignore                      # Git ignore rules.
├── README.md                       # Project overview and instructions.
└── requirements.txt                # Python dependencies.
```

## 👥 Team

**Team Members:**
- Beatriz Marques – 20231605
- Constança Pereira da Silva – 20231720
- Maria Inês Santos – 20231630
- Mariana Calais-Pedro – 20231641

### Team Members & Roles

**Beatriz Marques** → *AI & Systems Architecture*

Leads the overall technical direction of the project and designs the system architecture. Responsible for AI-related components, including prompt design, conversational workflows, OCR-based receipt parsing, and implementation of the Service Layer that connects the UI, tools, and persistence layers.

**Constança Pereira da Silva** → *UI & Streamlit Development*

Responsible for all user-facing components of the application. Designs and implements the Streamlit interface, ensuring intuitive user interaction, accessibility, and seamless integration with backend services.

**Maria Inês Santos** → *Tools & Utility Logic*

Develops and maintains deterministic tools and utility modules that support core application functionality. Ensures correct integration between tools, AI outputs, and service logic.

**Mariana Calais-Pedro** → *Database & Persistence*

Designs and manages the data model and persistence layer. Implements database schemas and CRUD operations, ensuring data integrity and reliable storage across the application.
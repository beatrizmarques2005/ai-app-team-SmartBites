# Team Project Architecture Plan

**Team Name:** *SmartBites*  
**Project Name:** *SmartBites*  
**Team Members:**  
1. Beatriz Marques - 20231605  
2. Constança Pereira da Silva - 20231720  
3. Maria Inês Santos - 20231630  
4. Mariana Calais-Pedro - 20231641  

**Project Domain:** Lifestyle  

---

## Part 1: Project Overview

### What problem are you solving?
SmartBites addresses the everyday challenge of managing groceries, reducing food waste, and maintaining a nutritious diet—especially for individuals with busy schedules. It helps users make the most of their available ingredients, plan meals efficiently, and meet dietary goals while minimizing time and effort.

### Who will use your application?
The app is designed for students and busy adults who want to eat healthily, manage their groceries effectively, reduce food waste, and streamline meal planning without spending excessive time.

### What's your core value proposition? (In one sentence)
SmartBites delivers personalized, AI-powered meal recommendations that optimize nutrition, reduce waste, and simplify grocery management based on what users already have.

---

## Part 2: Define Your Layers

### UI Layer (Streamlit)

**Framework:** Streamlit  
**Purpose:** Provide an intuitive, conversational interface that allows users to upload grocery receipts, manage ingredients, and receive personalized meal suggestions.  

**Pages/Screens:**
1. **Main Page: Chatbot** – Interact with AI assistant for meal planning and grocery organization.  
2. **User Profile Page** – Display and edit personal info (name, age, dietary preferences, BMI, allergies).  
3. **Calendar Page** – Weekly meal plan with clickable recipe entries.  
4. **Shopping List Page** – Dynamic shopping list based on planned meals.  
5. **Ingredients Page** – Manage and visualize ingredient database.  
6. **Recipes Page** – Browse suggested or saved recipes.  
7. **Login/Sign Up Pages** – Authenticate users via local credentials.  

**User Inputs:**
- File uploads (images or PDFs of receipts)  
- Text input (chat, search)  
- Dropdowns (dietary options, cuisine types)  
- Sliders/numeric inputs (household size)  
- Checkboxes and toggles (preferences/allergies)

**Display Outputs:**
- Extracted structured data (from receipt parsing)  
- Chatbot messages and recommendations  
- Charts/visualizations for nutrition and inventory  
- Tables (recipes, shopping lists)  
- Metrics (calorie intake, weekly goals)

---

### Service Layer (Business Logic)

**Framework:** Python (FastAPI or internal Python modules called by Streamlit)

#### Service 1: Grocery Parsing Service
- **Purpose:** Extract and structure grocery data from receipts.  
- **Responsibilities:**
  - Apply OCR to extract text from images or PDFs  
  - Use AI to identify ingredients, quantities, and prices  
  - Update the ingredient database with parsed items  

#### Service 2: Meal Planning Service
- **Purpose:** Generate weekly meal plans.  
- **Responsibilities:**
  - Match available ingredients with recipe options  
  - Optimize for user preferences, dietary restrictions, and goals  
  - Populate the meal calendar  

#### Service 3: Shopping List Generator
- **Purpose:** Build shopping lists based on upcoming meal plans.  
- **Responsibilities:**
  - Compare recipe requirements vs. current inventory  
  - List missing ingredients and quantities  
  - Display or export shopping list  

---

### AI Layer (Gemini Operations)

**Platform:** Google Gemini API (via function calling)  
**Capabilities:**
- Extract structured data from receipts (item name, quantity, price, supermarket, date)  
- Handle multi-turn chatbot conversations for meal planning  
- Summarize weekly meal plans or nutrition intake  
- Categorize foods by cuisine or group  
- Generate text content for recipes or feedback messages  
- Compare recipes based on nutrition, cost, or prep time  

**Multi-turn conversations:**  
☑ Yes — for meal planning, dietary guidance, and grocery organization  

**RAG/Vector Search:**  
Potential future enhancement — e.g., semantic search across recipe databases.  

---

### Tools Layer (Function Calling)

| **Tool** | **Purpose** | **Inputs** | **Outputs** |
|-----------|--------------|-------------|--------------|
| **BMI Calculator** | Compute BMI for health insights | height, weight | BMI value + health category |
| **Nutritional Analyzer** | Evaluate nutritional value of recipes | ingredient list | calories, macros, allergens |
| **Calendar Sync Tool** | Integrate meal plan into user calendar | meal schedule | synced events (via `.ics` export or Google Calendar API) |

---

## Part 3: Data Flow

**Example User Scenario:**
User uploads a grocery receipt and requests a weekly meal plan.

```
1. User uploads receipt and interacts with chatbot
↓
2. Streamlit (UI) sends file to Grocery Parsing Service
↓
3. Grocery Parsing Service:
   a. Extracts items/quantities using OCR + Gemini
   b. Updates ingredient database
   c. Triggers meal planning service
↓
4. Meal Planning Service requests AI suggestions
   Input: available ingredients + user preferences
   Output: structured weekly plan
↓
5. Tools Layer:
   a. Nutritional Analyzer calculates nutrition
   b. Calendar Sync Tool schedules meals
↓
6. Streamlit displays:
   - Weekly meal plan
   - Shopping list
   - Nutrition dashboard
↓
7. User can edit, confirm, or regenerate plan
```

---

## Part 4: Data Schema

### Structured Data Extracted

**Domain Schema:**
```json
{
  "user_profile": {
    "name": "string",
    "birth_date": "date",
    "gender": "string",
    "nationality": "string",
    "household_size": "integer",
    "dietary_preferences": ["string"],
    "allergies": ["string"],
    "bmi": "float"
  },
  "ingredient": {
    "name": "string",
    "quantity": "float",
    "unit": "string",
    "expiration_date": "date"
  },
  "recipe": {
    "title": "string",
    "ingredients": ["ingredient"],
    "instructions": "string",
    "nutrition": {
      "calories": "float",
      "protein": "float",
      "carbs": "float",
      "fat": "float"
    },
    "image_url": "string"
  },
  "shopping_list": {
    "items": [
      { "name": "string", "quantity": "float", "unit": "string" }
    ]
  }
}
```

**Required fields:**
- User name  
- Ingredient name + quantity  
- Recipe title + ingredients  

**Optional fields:**
- Nutrition breakdown  
- Recipe image  
- Expiration dates  

---

## Part 5: Component-Level Documentation

| **Component** | **Technology** | **Purpose** | **Interfaces With** |
|----------------|----------------|--------------|----------------------|
| `app.py` | Streamlit | Main entry point; controls UI routing and session state | Services + Gemini |
| `receipt_parser.py` | Python, Gemini | Extracts structured data from uploaded receipts | OCR engine, database |
| `meal_planner.py` | Python | Generates weekly plan | AI Layer, Nutritional Analyzer |
| `database.py` | SQLite or Firebase | Stores user profiles, ingredients, recipes | All services |
| `tools.py` | Python | Defines callable functions (BMI, nutrition, calendar) | Streamlit + AI |
| `config.yaml` | YAML | Holds API keys and model settings | AI and Tool Layers |

---

## Part 6: Architecture Decisions & Technical Choices

| **Decision** | **Rationale** |
|---------------|---------------|
| **Streamlit for UI** | Rapid prototyping and interactive AI integration |
| **Python (modular structure)** | Familiar language for team; strong ecosystem |
| **Gemini API** | Native multimodal capabilities for text + image (receipt parsing) |
| **Local Database (SQLite)** | Simple to implement and sufficient for prototype stage |
| **Function Calling for Tools** | Enables modular AI-tool interaction (BMI, nutrition, calendar) |
| **Streamlit Cloud Deployment** | Free hosting, easy sharing, integrated secrets management |
| **Langfuse Integration (future)** | Adds tracing and performance monitoring for LLM calls |

---

## Part 7: Setup & Deployment Instructions

*00_environment_setup.ipynb*

### **1. Environment Setup**
```bash
# Clone repository
git clone https://github.com/<team-repo>/smartbites.git
cd smartbites

# Create environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Variables**
Create a `.env` file:
```
GEMINI_API_KEY=your_api_key_here
STREAMLIT_API_KEY=your_key_if_needed
```

### **3. Run Locally**
```bash
streamlit run app.py
```

### **4. Deployment**
1. Push to GitHub.  
2. Log in to [Streamlit Cloud](https://share.streamlit.io/).  
3. Deploy repository → set environment variables.  
4. Share the public app link with testers.  

---

## Part 8: Team Roles

- **Beatriz Marques** → AI operations and chatbot integration  
- **Constança Pereira da Silva** → UI design and Streamlit pages  
- **Maria Inês Santos** → Backend services and database management  
- **Mariana Calais-Pedro** → Data extraction, receipt parsing, calendar sync  

---

## Part 9: Next Steps

**This Week:**  
- Set up project structure  
- Implement grocery parsing prototype  
- Test Gemini function calling  

**Next 2 Weeks:**  
- Develop Streamlit UI  
- Integrate services with AI layer  
- Add Langfuse tracing  

**Final Weeks:**  
- Refine user experience  
- Conduct end-to-end testing  
- Deploy final version on Streamlit Cloud  
- Prepare and rehearse final presentation  
This doc should explain:
- Architecture decisions and technical choices
- Component-level documentation recommended for complex modules
- Complete setup and deployment instructions

2. Define Your Application Concept
• What problem does your application solve?
• Who are your users?
• What’s the core value proposition?
• How will users interact with it?

3. Plan Your Architecture
• Review clean architecture materials from class
• Design your layered structure (UI, Service, AI, Tools)
• Identify which AI capabilities you need:
– What tools/functions will extend the LLM?
– What documents need to be processed?
– Does your project benefit from multimodal processing?
– Do you need RAG/vector database (e.g., semantic search for similarity matching)?


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

**Pages/Screens:**

1. **Main Page: Chatbot**  
   - Receive grocery receipts, organize weekly recipes, generate shopping lists.

2. **User Profile Page**  
   - Display and edit user info: name, gender, birth date, nationality, household size, BMI, dietary preferences, allergies.

3. **Calendar Page**  
   - Weekly meal plan with clickable recipe entries.

4. **Shopping List Page**  
   - Shopping list based on planned meals.

5. **Ingredients Page**  
   - Browse and manage ingredient database.

6. **Login Page**  
   - Authenticate users.

7. **Recipes Page**  
   - View recipe database with metadata and images.

8. **Sign Up Page**  
   - Create account.

**User Inputs:**

- ☑ File upload (images, PDF)
- ☑ Text input (chat, search)
- ☑ Dropdown selections (dietary options, cuisine types)
- ☑ Sliders/numeric inputs (household size)
- ☑ Other: checkboxes (allergies), toggles (vegan/vegetarian)

**Display Outputs:**

- ☑ Extracted structured data
- ☑ Chat conversations
- ☑ Charts/visualizations
- ☑ Tables
- ☑ Metrics/statistics
- ☑ Other: recipe images, nutrition breakdowns

---

### Service Layer (Business Logic)

**Service 1:** Grocery Parsing Service  
- Purpose: Extract structured data from uploaded receipts  
- Responsibilities:
  - Parse text from images/PDFs
  - Identify ingredients and quantities
  - Update ingredient database

**Service 2:** Meal Planning Service  
- Purpose: Generate weekly meal plans  
- Responsibilities:
  - Match ingredients to recipes
  - Optimize for dietary goals
  - Schedule meals in calendar

**Service 3:** Shopping List Generator  
- Purpose: Create shopping lists  
- Responsibilities:
  - Compare planned recipes with inventory
  - Calculate missing quantities
  - Format and display list

---

### AI Layer (Gemini Operations)

**AI Operations:**

- ☑ Extract structured data from documents  
  - Fields: item name, quantity, price, supermarket, date

- ☑ Chat/Q&A with context  
  - Topics: meal suggestions, dietary advice, grocery tips

- ☑ Summarization  
  - Content: weekly meal plan, nutrition intake

- ☑ Classification/Categorization  
  - Categories: food groups, cuisines

- ☑ Text generation  
  - Content: meal suggestions, chatbot responses

- ☑ Comparison  
  - Items: recipes by nutrition, cost, prep time

- ☑ Analysis  
  - Data: dietary habits, ingredient usage

- ☑ Other: recipe recommendation engine

**Multi-turn conversations:**  
☑ Yes  
- Purpose: Chatbot meal planning, dietary coaching, grocery management

---

### Tools Layer (Function Calling)

**Tool 1:** BMI Calculator  
- Purpose: Calculate BMI  
- Inputs: height, weight  
- Output: BMI value and category

**Tool 2:** Nutritional Analyzer  
- Purpose: Evaluate meal nutrition  
- Inputs: recipe ingredients  
- Output: calories, macros, allergens

**Tool 3:** Calendar Sync Tool  
- Purpose: Sync meal plan  
- Inputs: meal schedule  
- Output: calendar entries

**Function Calling:**  
☑ Yes, using function calling

---

## Part 3: Data Flow

**User Action:** User uploads grocery receipt and asks for weekly meal plan

**Step-by-Step Flow:**

```
1. User does: Uploads receipt and interacts with chatbot
        ↓
2. Streamlit (app.py) calls: Grocery Parsing Service
        ↓
3. Which service: Grocery Parsing Service
   What does it do:
   a. Extracts items and quantities from receipt
   b. Updates ingredient database
   c. Triggers meal planning
        ↓
4. AI Service called for: Meal Planning
   Input: available ingredients, user preferences
   Output: weekly meal plan
        ↓
5. Tools called: Nutritional Analyzer, Calendar Sync Tool
   For: nutrition breakdown, calendar integration
        ↓
6. Data returned to UI: meal plan, shopping list, calendar entries
        ↓
7. User sees: Suggested meals, shopping list, nutrition summary
```

**Draw a diagram on paper/whiteboard showing this flow!**

---

## Part 4: Data Schema

### What structured data do you extract?

**Your Domain Schema:**

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
      {
        "name": "string",
        "quantity": "float",
        "unit": "string"
      }
    ]
  }
}
```

**Your Actual Schema:**

```json
{




}
```

**Required fields (must have):**
- User name  
- Ingredient name and quantity  
- Recipe title and ingredients  

**Optional fields (nice to have):**
- Nutrition breakdown  
- Recipe image  
- Expiration dates  

---

## Part 5: Team Roles
- **Beatriz Marques** → AI operations and chatbot integration  
- **Constança Pereira da Silva** → UI design and Streamlit pages  
- **Maria Inês Santos** → Backend services and database management  
- **Mariana Calais-Pedro** → Data extraction, receipt parsing, calendar sync  

---

## Part 6: Next Steps

**This week:**
- Set up project structure  
- Create main service  
- Test AI operations  

**Next 2 weeks:**
- Build Streamlit UI  
- Connect services  
- Add tracing with Langfuse  

**Final weeks:**
- Polish and improve UX  
- Test thoroughly  
- Deploy to Streamlit Cloud  
- Prepare presentation  

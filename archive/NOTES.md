# SmartBites — Complete Functional Specification & Developer Guide

> **Goal:** Deliver a single Markdown file that contains the full product spec, DB schema, prompt/workflow definitions, API endpoints, ERD, flowcharts, suggested services/tools/utils, folder structure, and a minimal quickstart checklist so the team can start building. This file is designed to be actionable and ready-to-implement.

---

## Table of contents

1. [Overview](#overview)
2. [Core concepts & user flows](#core-concepts--user-flows)
3. [Pages / UI screens](#pages--ui-screens)
4. [Prompts / Scenarios / Processes](#prompts--scenarios--processes)
5. [Database schema (detailed)](#database-schema-detailed)
6. [Services, Tools & Utils (implementation-ready)](#services-tools--utils-implementation-ready)
7. [Suggested architecture & folder structure](#suggested-architecture--folder-structure)
8. [API endpoints (Swagger-ready)](#api-endpoints-swagger-ready)
9. [ERD & relationships (ASCII + notes)](#erd--relationships-ascii--notes)
10. [Flowcharts (textual) and sequence diagrams](#flowcharts-textual-and-sequence-diagrams)
11. [AI Prompt templates & prompt-building guidelines](#ai-prompt-templates--prompt-building-guidelines)
12. [Testing plan & acceptance criteria](#testing-plan--acceptance-criteria)
13. [Quickstart / developer checklist](#quickstart--developer-checklist)
14. [Next steps & optional enhancements](#next-steps--optional-enhancements)

---

## Overview

SmartBites is an AI-powered grocery, pantry and meal planning app for students and busy adults. It helps users manage receipts, keep an up-to-date pantry inventory, generate meal plans that optimize ingredient usage, and maintain shopping lists.

Key design goals:
- Minimal friction for adding receipts and pantry items.
- Accurate extraction of ingredients from receipts (OCR + NLP).
- AI-guided meal plan generation that uses current pantry contents first.
- Clear approval/interaction loop with user for any automatic changes.
- Lightweight and modular backend architecture so features can be independently developed and scaled.


---

## Core concepts & user flows

**Core entities:** User, Receipt, ReceiptItem, PantryItem (Ingredient), Recipe, MealPlan, MealSlot, ShoppingList, Notification

Primary user flows:
- Upload/receive receipt → OCR → parse → save receipt → add ingredients to pantry → remove items from shopping list.
- Request meal plan → system collects constraints → searches recipes (internal + web) → creates plan → requests approval → saves plan & updates shopping list as needed.
- Manual pantry updates (user adds items without a receipt).
- Manual shopping list edits.
- Report consumption of items not in plan → update pantry and meal plan.
- Cooking questions → provide guidance (no DB change required unless user confirms consumption/reservation).


---

## Pages / UI screens

1. **Chatbot UI** — primary conversational interface (follow-up questions, confirmations, quick actions).
2. **Pantry** — item list, quantities, add/remove, mark used, move to shopping list checkbox.
3. **Shopping List** — add/remove/clear items, grouped by store section (optional).
4. **Meal Plan** — calendar-like view with days and 3 slots/day (Breakfast, Lunch, Dinner). Each slot shows recipe, servings and ingredients used.
5. **Receipts DB** — chronological list of receipts with detail view and ability to edit parsed items.
6. **User Profile** — personal info, diet preferences, allergies, household size, favorite recipes.
7. **Recipe Library** — saved recipes, favorites, ability to add custom recipe.


---

## Prompts / Scenarios / Processes

> Full, implementation-ready prompt logic. This section contains the user prompts, trigger scenarios, follow-ups and the step-by-step automation each service must perform.

### 1) Receipt Processing

**Trigger:** user uploads a receipt/image or confirms they went shopping.

**Prompt example:** "I went shopping today — here's the receipt." (file + optional text)

**Process (implementation steps):**
1. Store original file & metadata (uploader, timestamp).
2. Send image to OCR service → get raw text.
3. Run NLP extraction pipeline to parse: store_name, purchase_date, purchase_time, invoice_number, items (name, section, quantity, unit_price, total_price), subtotal, discounts, total, payment_method.
4. Validate parsed totals vs detected numbers (flag suspicious receipts for review).
5. Persist structured receipt to `receipts` DB table.
6. For each parsed item: run `IngredientMatchingUtils` to normalize name and decide if it is a food ingredient.
7. Add food items to `pantry` (create or update quantity). Use `UnitConversionUtils` to standardize quantities.
8. Remove matching items from `shopping_list` if present (and quantities align).
9. Emit event `receipt.processed` for downstream systems (notifications, metrics).

**Edge cases & notes:**
- If OCR confidence is low, mark receipt for manual review in the UI.
- If quantities are not detected, create pantry item with `quantity=null` and prompt user for clarification via the chatbot.


### 2) Meal Plan Generation

**Trigger:** user asks "Generate meal plan" or similar.

**Prompt example:** "Generate a 7-day meal plan for 2 people, breakfast/lunch/dinner. Vegetarian, avoid nuts."

**Follow-up questions the system must ask (if missing):**
- Date range (from / to)
- Number of people (servings)
- Meals to include (breakfast/lunch/dinner)
- Any special events/occasions
- Any hard preferences for specific days/meals

**Process:**
1. Validate constraints and user profile (allergies, diet_type).
2. Pull pantry snapshot and normalize ingredients/quantities.
3. Use `RecipeService.search_recipes_by_ingredients()` with strict mode to find recipes that require only pantry ingredients.
4. If strict mode yields recipes for all meal slots: propose them.
5. If not, run a relaxed search to find recipes with minimal missing ingredients and compile `missingItems` list.
6. Present a proposal to the user with:
   - Recipes for each slot
   - Missing items (if any) and quick "Add to shopping list" buttons
   - Estimated prep time and complexity (from recipe data)
7. Upon user approval, save meal plan, reserve pantry quantities (optional: reduce pantry quantities immediately or on consumption), and add missing items to `shopping_list` if user confirms.

**Optimization constraints (future):**
- Combine recipes that reuse ingredients to reduce waste.
- Minimize number of unique missing items.
- Prefer quick recipes on weekdays.


### 3) Add Ingredients Without Receipt (Manual)

**Trigger:** user says "Add these ingredients" or uses a UI form.

**Follow-up questions (when fields missing):**
- Ingredient name (mandatory)
- Quantity (ask for unit or allow free text)
- Purchase date (optional)
- Section / category (optional)

**Process:**
- Validate input; normalize using `TextNormalizationUtils` and `UnitConversionUtils`.
- Save to pantry. If required fields are missing, keep in `pantry.pending` and ask user via chatbot.


### 4) Modify Meal Plan

**Trigger:** user requests to change or remove a meal slot.

**Prompt example:** "Change Wednesday dinner — I don't want to cook."

**Follow-up questions:**
- Which day/meal?
- Replace with what? (quick recipe, takeaway, remove)
- Any dietary/thematic constraints for replacement?

**Process:**
- If replacement is a recipe from the pantry, propose alternatives.
- If replacement requires shopping, add missing items to `shopping_list` and ask for approval.
- Update plan after user confirmation.


### 5) Ate an Item Not in Plan

**Trigger:** user reports consumption outside plan.

**Prompt example:** "I ate 2 slices of bread at 10:30."

**Follow-up questions:**
- What exactly was consumed? (clarify brand/type if ambiguous)
- Quantity (approx.)
- When?

**Process:**
- Deduct quantity from pantry (or mark as unknown). If quantity becomes negative, prompt user to restock or update.
- If the consumed ingredient was planned for a future meal: flag the meal slot and propose replacements using available pantry items.


### 6) Shopping List Management

**Trigger:** user adds/removes items manually or via auto-add from meal planning.

**Prompt example:** "Add milk 1L to my shopping list." or "Remove eggs"

**Process:**
- CRUD operations on `shopping_list` table.
- Support grouping by store section (optional) for better UX when viewing list.
- When a receipt is added, sync to remove purchased items.


### 7) Cooking Helper

**Trigger:** user asks a cooking question.

**Prompt example:** "What's the correct doneness for beef ribeye on the pan?"

**Follow-up:** Ask for cut, thickness, method (pan/oven/grill).

**Process:**
- Provide temperature/time guidance and step-by-step suggestions.
- No DB changes unless user explicitly uses a suggestion and marks an ingredient consumed.


---

## Database schema (detailed)

This section defines tables and JSON structures for core entities.

### Receipts (table: `receipts`)

Columns:
- id (uuid, PK)
- user_id (fk)
- store_name (string|null)
- purchase_date (date|null)
- purchase_time (time|null)
- invoice_number (string|null)
- items (jsonb) — array of receipt items (name, section, quantity, unit_price, total_price)
- subtotal (decimal|null)
- discounts (decimal|null)
- total (decimal|null)
- payment_method (string|null)
- raw_ocr_text (text)
- parsed (boolean)
- parsing_confidence (float)
- created_at, updated_at

ReceiptItem structure (JSON element):
```json
{
  "name": "string",
  "section": "string|null",
  "quantity": "number|null",
  "unit": "string|null",
  "unit_price": "number|null",
  "total_price": "number|null"
}
```


### Pantry (table: `pantry_items`)

Columns:
- id (uuid, PK)
- user_id (fk)
- name (string)
- normalized_name (string) — for fuzzy matching
- quantity (decimal|null)
- unit (string|null)
- purchase_date (date|null)
- source_receipt_id (fk|null)
- expiration_date (date|null)
- category (string|null)
- created_at, updated_at


### Recipes (table: `recipes`)

Columns:
- id (uuid, PK)
- user_id (fk|null) — owner if custom
- title
- ingredients (jsonb) — array [{name, qty, unit}]
- instructions (text)
- link (string|null)
- favorite (boolean)
- prep_time_minutes (int|null)
- servings (int|null)
- cuisine_type (string|null)
- created_at, updated_at


### Meal Plans (table: `meal_plans`)

Columns:
- id (uuid, PK)
- user_id (fk)
- start_date, end_date
- metadata (jsonb) — constraints, people count, notes
- slots (jsonb) — array of day slots with meal recipe ids and status (proposed/confirmed)
- created_at, updated_at

Example slot:
```json
{
  "date": "2025-11-30",
  "meals": {
    "breakfast": {"recipe_id": "uuid", "status": "confirmed"},
    "lunch": {"recipe_id": "uuid", "status": "proposed"},
    "dinner": {"recipe_id": "uuid", "status": "confirmed"}
  }
}
```


### Shopping List (table: `shopping_list_items`)

Columns:
- id (uuid, PK)
- user_id (fk)
- name (string)
- quantity (decimal|null)
- unit (string|null)
- section (string|null)
- auto_added_by (string|null) — e.g., "meal_plan_123"
- created_at, updated_at


### Users (table: `users`)

Columns:
- id (uuid, PK)
- username (string, unique)
- email (string, unique)
- full_name (string)
- birth_date (date|null)
- gender (string|null)
- household_number (int|null)
- allergies (jsonb) — array of strings
- intolerances (jsonb) — array of strings
- restrictions (jsonb) — religion/likes/dislikes
- diet_type (string) — e.g., carnivore, balanced, vegetarian
- favorite_recipes (jsonb) — array of recipe_ids
- created_at, updated_at


---

## Services, Tools & Utils (implementation-ready)

> This is the same list we validated earlier but expanded with concrete implementation suggestions and interfaces.

### Services (back-end microservices or modules)

1. **ReceiptService**
   - API: `POST /receipts` (file + optional meta)
   - Integrations: OCRTool, NLPParser, PantryService, ShoppingListService
   - Events: `receipt.received`, `receipt.processed`

2. **PantryService**
   - API: `GET/POST/PATCH /pantry`
   - Responsibilities: normalized inventory, expiration tracking, reservations (optional)

3. **RecipeService**
   - API: `GET /recipes?ingredients=...`, `POST /recipes`
   - Integrations: WebScraper, EmbeddingSearch for semantic retrieval

4. **MealPlanService**
   - API: `POST /mealplan`, `PATCH /mealplan/{id}`
   - Integrations: RecipeService, PantryService, AIPlanner

5. **ShoppingListService**
   - API: `GET/POST/PATCH /shoppinglist`
   - Sync logic with receipts and meal plans

6. **UserService**
   - API: `GET/POST/PATCH /user`

7. **AuthService**
   - JWT-based auth, password hashing, refresh tokens

8. **CookingHelperService**
   - Lightweight rule-based + LLM-assisted helper


### Tools / Integrations

- **OCR**: Tesseract (self-host) or Google Cloud Vision (managed)
- **NLP Parser**: custom rules + spaCy / transformer-based extractor for receipts
- **WebScraper**: Puppeteer/Playwright or BeautifulSoup + requests; obey robots.txt
- **Embedding Search**: OpenAI embeddings / Milvus / Pinecone / Weaviate
- **LLM / AI Planner**: GPT-4/5 style LLM (hosted via API) or local LLM for offline
- **Image Storage**: S3-compatible (AWS S3, DigitalOcean Spaces)
- **Database**: PostgreSQL (with jsonb support)
- **Queue / Events**: RabbitMQ / Redis Streams / Kafka
- **Task Runner**: Celery (Python) or BullMQ (Node)
- **Monitoring & Logging**: Sentry + ELK / Grafana


### Utils

- `DateTimeUtils` — parsing & normalizing dates
- `UnitConversionUtils` — standardize units
- `TextNormalizationUtils` — remove accents, lowercase, trim stopwords for matching
- `IngredientMatchingUtils` — fuzzy match + synonyms map
- `AI PromptBuilderUtils` — function to assemble system + user prompts with constraints
- `ValidationUtils` — common validation functions
- `PlanConflictUtils` — find uses of ingredient across future plans


---

## Suggested architecture & folder structure

The folders below prioritize clarity and separation of concerns. This structure assumes a Python + FastAPI backend, PostgreSQL DB and React frontend. It can be adapted to Node/Express.

```
smartbites/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI app
│  │  ├─ config.py
│  │  ├─ api/
│  │  │  ├─ v1/
│  │  │  │  ├─ receipts.py
│  │  │  │  ├─ pantry.py
│  │  │  │  ├─ recipes.py
│  │  │  │  └─ mealplan.py
│  │  ├─ services/
│  │  │  ├─ receipt_service.py
│  │  │  ├─ pantry_service.py
│  │  │  ├─ recipe_service.py
│  │  │  └─ mealplan_service.py
│  │  ├─ tools/
│  │  │  ├─ ocr.py
│  │  │  ├─ nlp_parser.py
│  │  │  └─ webscraper.py
│  │  ├─ utils/
│  │  │  ├─ datetime_utils.py
│  │  │  ├─ unit_conversion.py
│  │  │  └─ ingredient_matching.py
│  │  ├─ db/
│  │  │  ├─ models.py
│  │  │  └─ crud.py
│  │  └─ tasks/
│  │     └─ worker.py
│  └─ Dockerfile
├─ frontend/
│  ├─ src/
│  │  ├─ pages/Chatbot.jsx
│  │  ├─ pages/Pantry.jsx
│  │  └─ components/ReceiptUploader.jsx
│  └─ package.json
├─ infra/
│  ├─ docker-compose.yml
│  └─ k8s/ (if needed)
├─ scripts/
│  ├─ init_db.sql
│  └─ seed_data.py
└─ README.md
```


---

## API endpoints (Swagger-ready quick list)

> Implementation notes: use REST for simplicity. Later consider GraphQL for flexible client queries.

**Auth**
- `POST /auth/register` — register user
- `POST /auth/login` — get tokens
- `POST /auth/refresh` — refresh token

**Receipts**
- `POST /receipts` — upload receipt image + optional metadata
- `GET /receipts` — list user receipts
- `GET /receipts/{id}` — get receipt detail
- `PATCH /receipts/{id}` — manual correction

**Pantry**
- `GET /pantry` — list pantry items
- `POST /pantry` — add pantry item (manual)
- `PATCH /pantry/{id}` — update quantity/expiry
- `DELETE /pantry/{id}` — remove item

**Recipes**
- `GET /recipes` — search recipes (query params: ingredients,searchexact)
- `POST /recipes` — add custom recipe
- `GET /recipes/{id}` — recipe detail
- `PATCH /recipes/{id}` — update

**Meal Plans**
- `POST /mealplan` — generate plan (body contains constraints)
- `GET /mealplan` — get user plans
- `GET /mealplan/{id}` — detail
- `PATCH /mealplan/{id}` — update

**Shopping List**
- `GET /shoppinglist`
- `POST /shoppinglist`
- `PATCH /shoppinglist/{id}`
- `DELETE /shoppinglist/{id}`

**User**
- `GET /user/{id}`
- `PATCH /user/{id}`


---

## ERD & relationships (ASCII + notes)

```
[users] 1 ---- * [receipts]
[users] 1 ---- * [pantry_items]
[users] 1 ---- * [recipes]
[users] 1 ---- * [meal_plans]
[meal_plans] * ---- * [recipes]  (via slots array)
[receipts] 1 ---- * [receipt_items] (jsonb embedded or normalized table)
[users] 1 ---- * [shopping_list_items]
```

Notes:
- Many-to-many between meal_plans and recipes is represented as `slots` json array inside meal_plans for simplicity.
- If analytics are required (e.g., historical recipe usage), add `recipe_usage` table.


---

## Flowcharts (textual) and sequence diagrams

### Receipt processing (sequence)

```
User -> Frontend: upload receipt image
Frontend -> Backend /receipts: POST file
Backend -> OCR tool: process image
OCR -> Backend: raw text
Backend -> NLP Parser: parse items
NLP -> Backend: structured receipt
Backend -> DB: save receipt
Backend -> PantryService: add items
Backend -> ShoppingListService: remove purchased items
Backend -> User: confirm parsing / ask clarifications via chatbot
```

### Meal plan generation (sequence)

```
User -> Frontend: request meal plan (constraints)
Backend -> UserService: load profile/allergies
Backend -> PantryService: snapshot pantry
Backend -> RecipeService: search recipes
RecipeService -> Backend: candidate recipes + missing items
Backend -> AIPlanner: optimize multi-day plan
AIPlanner -> Backend: proposed plan
Backend -> Frontend: show plan + missing items
User -> Frontend: approve / modify
Frontend -> Backend: confirm
Backend -> MealPlanService: save plan
Backend -> ShoppingListService: add missing items (if approved)
```


---

## AI Prompt templates & prompt-building guidelines

**Prompt goals:**
- Keep system prompts short and factual.
- Pass *only necessary* context to LLM (pantry snapshot, user constraints, recipe metadata).
- Use deterministic instructions for follow-up question generation.

**Example: Meal Planner system prompt (skeleton)**

```
You are SmartBites assistant. Given a pantry (list of ingredients with quantities and units), user constraints (diet, allergies), and requested date range + meals per day, propose recipes for each meal slot.
Constraints:
- Prefer recipes that use only pantry ingredients. If not possible, include a minimal missing ingredient list.
- Respect allergies/restrictions exactly.
- Keep total prep time under 45 minutes for weekday dinners.
Output JSON shape: {"plan": [{"date":"YYYY-MM-DD","meals":{...}}], "missingItems": [...]}
```

**Prompt building tip:** limit pantry snapshot size by filtering to ingredients more likely to be used (e.g., exclude condiments unless required) or pass a hashed list of normalized ingredient names.


---

## Testing plan & acceptance criteria

**Unit tests:**
- ReceiptService: OCR parse -> expected structured json for sample receipts
- UnitConversionUtils: conversions between common units
- IngredientMatchingUtils: fuzzy matches (10+ test pairs)

**Integration tests:**
- Upload receipt -> pantry updated -> shopping list sync
- Generate meal plan with exact pantry coverage -> plan saved, no missing items
- Generate meal plan with missing ingredients -> missing items added to shopping list on approval

**E2E tests:**
- User flow: upload receipt, request 3-day plan, approve plan, simulate consuming an item, verify meal plan updated.

**Acceptance criteria (basic):**
- OCR accuracy >= acceptable threshold on provided sample receipts (subjective).
- Meal planner returns valid JSON plan and nothing violates user allergies.
- Pantry quantities never go negative silently; negative states must trigger an explicit user confirmation to restock.


---

## Quickstart / developer checklist

This section lets a developer get the project running locally with minimum friction.

1. Clone repo
2. `docker-compose up` — local Postgres, Redis, backend, frontend
3. Run DB migrations `scripts/init_db.sql` or Alembic migrations
4. Seed sample user + pantry + recipe data with `scripts/seed_data.py`
5. Start frontend and login with seeded user
6. Test receipt upload with sample images in `/scripts/samples/receipts/`


---

## Next steps & optional enhancements

- Add expiry tracking + push notifications for soon-to-expire ingredients.
- Add nutrition calculation per meal + weekly summary.
- Add multi-user household support with shared pantry and permissions.
- Add recipe rating and history to improve AI recommendations.
- Add offline-first mobile caching for users who are often offline.

---

## Appendix A: Helpful heuristics for implementation

- Standardize ingredient names with a combination of rules + embeddings for best results.
- Use `jsonb` for flexible recipe and receipt item storage, migrate to normalized tables only if analytics demand it.
- Keep evidence of OCR results (store raw text) to allow manual correction later.
- Prefer event-driven architecture for decoupling long-running tasks (OCR, webscraping, recipe enrichment).


---

*Document generated to be developer-friendly and directly actionable.*

If you want, I can now:
- generate API swagger YAML for the endpoints above
- scaffold the `backend/app/services` files with function signatures (Python/FastAPI)
- create seed data used in tests

Tell me which of the above you'd like next.


---

## 8. API ENDPOINTS (HIGH‑LEVEL)

### 🧾 **Receipt API**
- `POST /receipts/upload` – Upload a receipt (image/PDF)
- `GET /receipts/{id}` – Get receipt details
- `GET /receipts` – List user receipts

### 🥫 **Pantry API**
- `GET /pantry` – List all ingredients
- `POST /pantry/add` – Add item manually
- `PATCH /pantry/update` – Update an ingredient
- `DELETE /pantry/{name}` – Remove ingredient

### 🍽️ **Meal Plan API**
- `POST /mealplan/generate` – Create a new plan
- `GET /mealplan` – Retrieve current plan
- `PATCH /mealplan/update` – Modify a meal
- `POST /mealplan/consume` – Log consumption not in plan

### 🛒 **Shopping List API**
- `GET /shopping-list` – Get items
- `POST /shopping-list/add` – Add item
- `DELETE /shopping-list/{item}` – Remove item
- `DELETE /shopping-list` – Clear list

### 🍲 **Recipe API**
- `GET /recipes/search` – Search recipes by ingredients
- `POST /recipes/save` – Save recipe
- `PATCH /recipes/{id}/favorite` – Toggle favorite

### 👤 **User API**
- `GET /user` – Get profile
- `PATCH /user` – Update user settings

### 🔐 **Auth API**
- `POST /auth/register` – Create account
- `POST /auth/login` – Login

---

## 9. SEQUENCE DIAGRAMS (TEXT VERSION)

### 📸 **A) Receipt Processing Sequence**
```
User → Receipt API → OCR Tool → NLP Parser → ReceiptService
      → PantryService → ShoppingListService → DB
```

### 📅 **B) Meal Plan Generation Sequence**
```
User → MealPlan API → MealPlanService
     → PantryService
     → RecipeService → WebScraper/AI Tool
     → ShoppingListService
     → DB → User
```

### 🍽️ **C) Unplanned Consumption Sequence**
```
User → MealPlan API → MealPlanService
     → PantryService
     → PlanConflictUtils → RecipeService
     → ShoppingListService → DB
```

---

## 10. DATA MODELS (JSON EXAMPLES)

### 🧾 **Receipt**
```json
{
  "store_name": "Continente",
  "purchase_date": "2025-01-22",
  "purchase_time": "14:22",
  "invoice_number": "FS22-233",
  "items": [
    { "name": "Bananas", "section": "Fruit", "quantity": 1.2, "unit_price": 1.49, "total_price": 1.78 }
  ],
  "subtotal": 1.78,
  "discounts": 0,
  "total": 1.78,
  "payment_method": "MBWay"
}
```

### 🥫 **Pantry Item**
```json
{
  "name": "Arroz",
  "quantity": 500,
  "unit": "g",
  "purchase_date": "2025-01-20"
}
```

### 🍽️ **Meal Plan Day**
```json
{
  "date": "2025-01-23",
  "meals": {
    "breakfast": { "recipe_id": 32 },
    "lunch": { "recipe_id": 91 },
    "dinner": { "recipe_id": 54 }
  }
}
```

---

## 11. FRONTEND PAGES — FINAL DETAIL

### **1. Chatbot page**
- Main interaction center
- Chat UI + message history
- Buttons for quick actions (Add receipt, Generate plan, Add item)

### **2. Pantry page**
- Table view of all pantry items
- Toggle: *show low stock only*
- Checkbox to send items to Shopping List
- Add manual item modal

### **3. User page**
- Profile information
- Dietary restrictions
- Allergies/intolerances
- Household size
- Favorite recipes gallery

### **4. Meal Plan page**
- Calendar-like layout (no hours)
- 3 slots per day
- Modify meal (swap / remove / replace)
- Regenerate week

### **5. Receipts page**
- List all receipts
- Click into details
- Show extracted ingredients

---

## 12. NEXT STEPS (IMPLEMENTATION ROADMAP)

### **Phase 1 — Foundations (Backend)**
- Set up project structure
- Implement AuthService
- Create database schemas
- Create basic CRUD endpoints

### **Phase 2 — Receipt Pipeline**
- Add OCR + NLP pipeline
- Test with sample receipts
- Integrate Pantry updates
- Shopping list auto‑sync

### **Phase 3 — Recipes + Web Scraping**
- Create search engine
- Normalize ingredient parsing
- Save recipes

### **Phase 4 — Meal Planning Engine**
- Integrate AI model (prompt builder + constraints)
- Validation tool for follow‑ups

### **Phase 5 — Frontend UI**
- Calendar view
- Chatbot
- Pantry dashboard
- Final clean-up

---

(Feel free to ask for the next addition: endpoints in full Swagger, full folder structure with actual file stubs, or test scenarios!)

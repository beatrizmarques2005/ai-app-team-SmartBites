# Services and Tools — Summary

This document lists all services and tools in the codebase, with purpose and main functions/methods found in each file.

---

## Services

### AIService
- File: `src/services/ai_service.py`
- Purpose: Centralized AI / LLM helpers used across the app (extraction, recipe generation, QA, suggestions).
- Key methods:
  - `extract_structured(file_bytes, schema, mime_type)`
  - `chat_with_context(question, context, system_instruction)`
  - `summarize(text, max_sentences)`
  - `_build_extraction_prompt(schema)`
  - `extract_recipe(html)` / `extract_recipe_from_html(html)`
  - `get_recipe_links()` / `get_supermarket_recipes(max_recipes)`
  - `check_ingredients(recipe, inventory_manager)` / `get_possible_recipes(inventory_manager)`
  - `generate_recipe_from_ingredients(ingredients, servings, dietary)`
  - `ask_recipe_question(recipe, question)`
  - `validate_recipe(data)`
  - `suggestion(ingredients)`
  - `answer_question(question, context, system_instruction)`
  - `generate_recipe(inventory_manager, servings, dietary)`

### DocumentService
- File: `src/services/document_service.py`
- Purpose: Validate files (PDF/images) and extract text using local OCR or fallbacks.
- Key methods:
  - `validate_file(file_bytes, mime_type)`
  - `get_file_info(file_bytes)`
  - `extract_text(file_bytes, mime_type=None)`

### ExpiryNotifier
- File: `src/services/expiry_notifier.py`
- Purpose: Notify / return items that are expiring soon (wraps `PantryService.expiry_check`).
- Key methods:
  - `expiring_soon(user_id)`

### IngredientService
- File: `src/services/ingredient_service.py`
- Purpose: Compare recipes against inventory and suggest AI-based replacements.
- Key methods:
  - `check_missing(recipe, user_id=None)`
  - `suggest_replacement(ingredient, context=None)`

### MealPlanService
- File: `src/services/mealplan_service.py`
- Purpose: Propose, persist and manage meal plans (uses `tools.meal_planner` and Supabase adapter).
- Key methods:
  - `propose_plan(ingredients, preferences, user_id=None)`
  - `get_schedule_and_shopping(plan)`
  - `save_plan(user_id, start_date, end_date, plan, metadata=None)`
  - `add_history_entry(user_id, date, meal)`
  - `list_history(user_id, limit=50)`
  - `remove_history_entry(user_id, entry_id)`

### PantryService
- File: `src/services/pantry_service.py`
- Purpose: Manage pantry items, normalize names, expiry checks, and provide ingredient lists for recipe generation.
- Key methods:
  - `list_items(user_id)`
  - `add_or_update_item(user_id, name, quantity=None, unit=None, source_receipt_id=None)`
  - `remove_item(user_id, item_id)`
  - `as_pretty(pantry_row)`
  - `expiry_check(user_id)`
  - `get_ingredients_for_recipe(user_id, prioritize_expiring=True)`

### ReceiptService
- File: `src/services/receipt_service.py`
- Purpose: End-to-end receipt analysis pipeline (validate, AI extraction, normalize, persist, update pantry & shopping list).
- Key methods:
  - `analyze_receipt(file_bytes, mime_type=None)`
  - `process_and_store_receipt(file_bytes, mime_type, user_id)`
  - `_get_receipt_schema()`

### RecipeGeneratorAI (shim)
- File: `src/services/recipe_generator.py`
- Purpose: Backwards-compatible shim for recipe generation; delegates to `AIService` when available and provides deterministic fallback for demos/tests.
- Key methods / API:
  - `generate(prompt, **kwargs)` (fallback shim)
  - `generate_recipe(inventory_manager, servings, dietary)`
  - `get_recipe_links()`
  - `extract_recipe_from_html(html)`
  - `get_supermarket_recipes(max_recipes)`
  - `check_ingredients(recipe, inventory_manager)`
  - `get_possible_recipes(inventory_manager)`

### RecipeScraper
- File: `src/services/recipe_scraper.py`
- Purpose: Crawl/fetch recipe pages and extract structured recipes using AI.
- Key methods:
  - `fetch_html(url)`
  - `collect_links(sources=None)`
  - `scrape(url)`
  - `search_recipes(query, sources=None, max_results=20)`

### RecipeService
- File: `src/services/recipe_service.py`
- Purpose: High-level recipe API for searching, generating and fetching saved recipes; integrates AI generator and persistence.
- Key methods:
  - `search_by_ingredients(ingredients, strict=True)`
  - `get_saved_recipes(user_id)`
  - `generate_from_pantry(inventory_manager, servings=1, dietary=None)`

### ShoppingListService
- File: `src/services/shopping_list_service.py`
- Purpose: Manage shopping list items and generate shopping lists from meal plans.
- Key methods:
  - `list_items(user_id)`
  - `add_item(user_id, name, quantity=None, unit=None, section=None, auto_added_by=None)`
  - `remove_item(user_id, item_id)`
  - `generate_from_plan(meal_plan, inventory=None)`
  - `format_shopping_list(items)`

### UserService
- File: `src/services/user_service.py`
- Purpose: User profile, preferences, favorites, household info and user management (includes lightweight helpers and a more complete repository-backed service and DTOs).
- Key methods / capabilities:
  - Lightweight: `get_user_profile(user_id)`, `update_user_profile(user_id, data)`, `set_dietary_preferences(user_id, allergies, intolerances, diet_type)`, `add_favorite_recipe(user_id, recipe_id)`, `remove_favorite_recipe(user_id, recipe_id)`, `get_favorite_recipes(user_id)`, `get_household_info(user_id)`, `update_household_info(user_id, number_of_members)`
  - Extended CRUD/auth: DTOs and repository protocol, `create_user(user_in)`, `get_user(user_id)`, `get_by_email(email)`, `authenticate(email, password)`, `update_user(user_id, changes)`, `delete_user(user_id)`

---

## Tools

### CookingAssistant
- File: `src/tools/cooking_assistant.py`
- Purpose: On-demand cooking guidance / cooking helper. (File currently contains a placeholder / notes to integrate with `AIService`.)
- Key items: placeholder module (no formal public methods present in file)

### DateCalculator
- File: `src/tools/date_calculator.py`
- Purpose: Deterministic date utilities and food expiry calculations (avoid AI for exact date logic).
- Key methods / functions:
  - `DateCalculator.days_until(target_date)`
  - `DateCalculator.get_renewal_date(expiry_date, days_before=90)`
  - `DateCalculator.add_business_days(start_date, days)`
  - `DateCalculator.get_duration_months(start_date, end_date)`
  - `DateCalculator.is_weekend(date)`
  - `get_food_status(open_date, shelf_life)` (returns expiry info and `days_remaining`)

### MealPlanner
- File: `src/tools/meal_planner.py`
- Purpose: Pure functions to match pantry ingredients to recipes, generate meal plans, and create schedules (no persistence).
- Key functions:
  - `_fetch_recipes_from_remote(url, timeout)`
  - `_get_recipe_db()`
  - `_filter_by_preferences(recipe, preferences)`
  - `match_ingredients_to_recipes(ingredients)`
  - `generate_meal_plan(ingredients, preferences)`
  - `schedule_meals(meal_plan)`

### RecipeFeedback
- File: `src/tools/recipe_feedback.py`
- Purpose: Collect and analyze recipe ratings/comments with optional JSON persistence.
- Key methods:
  - `submit_feedback(recipe_id, rating, comments, user_id, tags=None)`
  - `all_feedback(recipe_id=None, sort_by_time=True, descending=True)`
  - `statistics(recipe_id)`
  - `global_statistics()`
  - `filter_by_tag(tag)`

### SeasonalFinder
- File: `src/tools/seasonal_finder.py`
- Purpose: Basic seasonal matching for recipes and a lightweight `MealHistory` helper.
- Key items:
  - `seasonal_finder(recipes, season)`
  - `MealHistory` class with `add_meal(...)`, `meals_on_date(target_date)`, `meals_on_day(target_day)`, `count_meal_freq()`, `most_frequent_meals(top_n=1)`, `meals_in_range(start_date, end_date)`

---

If you want, I can:
- Export this to a different filename or include additional fields (examples, sample calls).
- Generate a CSV or a shorter one-page summary for your report.

File saved to: `services_and_tools_summary.md` in the repository root.

# SmartBites — Bea Streamlit Demo

This folder contains a small multipage Streamlit demo to preview core flows (pantry, shopping list, meal planner, receipts, recipes, chatbot, and profile).

Quick start

1. Create & activate your Python environment (optional but recommended).
2. Install dependencies (if not already installed):

```powershell
python -m pip install -r requirements.txt
# or at minimum:
python -m pip install streamlit
```

3. Run the demo:

```powershell
streamlit run streamlit_bea/app.py
```

Notes

- The demo uses lightweight in-memory mocks by default so you can open and interact without external services.
- To try a single-file demo (the original combined UI), run `streamlit run streamlit_bea/App.py`.
- If you wire up Supabase or your own `src.services` implementations, the demo will attempt to use them automatically when available.

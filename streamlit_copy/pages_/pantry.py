import streamlit as st
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.services_old.pantry_service import PantryService


def pantry_page():
    st.set_page_config(page_title="Pantry", page_icon="🥫", layout="wide")
    st.title("My Pantry")
    st.write("Manage your pantry items here!")

    # Initialize pantry service once
    @st.cache_resource
    def get_pantry_service():
        return PantryService()

    pantry = get_pantry_service()


    # Fetch items from DB/service
    try:
        with st.spinner("Loading pantry items..."):
            items = pantry.list_items(st.session_state.get('user_id'))
    except Exception as e:
        st.error(f"Failed to load pantry items: {e}")
        items = []

    if not items:
        st.info("No pantry items found for this user.")
        return

    # Optionally prettify quantity/unit
    pretty_rows = [pantry.as_pretty(row) for row in items]

    # Show as a table
    import pandas as pd

    df = pd.DataFrame(pretty_rows)

    # Choose columns to display (common fields)
    display_cols = []
    for col in [
        'id', 'name', 'normalized_name', 'quantity', 'unit', 'pretty_quantity', 'pretty_unit',
        'open_date', 'shelf_life', 'notes'
    ]:
        if col in df.columns:
            display_cols.append(col)

    st.dataframe(df[display_cols])

    
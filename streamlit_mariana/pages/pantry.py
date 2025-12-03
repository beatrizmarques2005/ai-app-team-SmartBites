import streamlit as st

from supabase_client import supabase
from datetime import datetime

st.write("Current user:", st.session_state.user_id)


if "user_id" not in st.session_state or not st.session_state.user_id:
    st.switch_page("login.py")


st.set_page_config(page_title="SmartBites | Pantry", layout="wide")

# ----------------- SECURITY CHECK -----------------
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.error("You must be logged in to access this page.")
    st.stop()

user_id = st.session_state.user_id

# ----------------- TITLE -----------------
st.title("🍽️ SmartBites")
st.subheader("Your Pantry & Shopping List")

st.markdown("---")

# ----------------- LAYOUT -----------------
pantry_col, shopping_col = st.columns([3, 1])

# ===================== PANTRY =====================
with pantry_col:
    st.header("🧺 Pantry")

    pantry_response = supabase.table("pantry_items")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()

    pantry_items = pantry_response.data

    if not pantry_items:
        st.info("Your pantry is empty.")
    else:
        for item in pantry_items:
            date_obj = datetime.fromisoformat(item["created_at"])
            formatted_date = date_obj.strftime("%d %B")

            st.markdown(
                f"""
                **{item['ingredient_name']}**  
                Quantity: {item['quantity']}  
                Added on: {formatted_date}
                """
            )
            st.divider()

# ===================== SHOPPING LIST =====================
with shopping_col:
    st.header("🛒 Shopping List")

    shopping_response = supabase.table("shopping_list")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    shopping_items = shopping_response.data

    if not shopping_items:
        st.info("Your shopping list is empty.")
    else:
        for item in shopping_items:
            checked = st.checkbox(
                f"{item['ingredient']} ({item['quantity']})",
                key=item["id"]
            )

            if checked:
                supabase.table("shopping_list")\
                    .delete()\
                    .eq("id", item["id"])\
                    .execute()

                st.rerun()

# ----------------- LOGOUT -----------------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

import streamlit as st

# def signup_page():
#     st.title("Sign Up for Smart Bites")

#     with st.form("signup_form"):
#         new_username = st.text_input("Choose a username")
#         new_password = st.text_input("Choose a password", type="password")
#         confirm_password = st.text_input("Confirm password", type="password")

#         submitted = st.form_submit_button("Sign Up")

#         if submitted:
#             if new_username in USER_CREDENTIALS:
#                 st.error("Username already exists.")
#             elif new_password != confirm_password:
#                 st.error("Passwords do not match.")
#             elif new_username == "" or new_password == "":
#                 st.error("Please fill in all fields.")
#             else:
#                 # Add user to credentials
#                 USER_CREDENTIALS[new_username] = new_password
#                 st.success("Account created successfully! Please log in.")
#                 st.session_state['logged_in'] = True
#                 st.session_state['username'] = new_username
#                 st.session_state['show_signup'] = False
#                 st.rerun()



def _init_signup_state():
    """Ensure session state keys exist for the wizard."""
    if "signup_step" not in st.session_state:
        st.session_state.signup_step = 0
    if "signup_data" not in st.session_state:
        st.session_state.signup_data = {
            "username": "",
            "password": "",
            "confirm": "",
            "email": "",
            # preferences
            "dietary_preferences": [],
            "allergies": "",
            "restrictions": "",
            "preferred_cuisines": [],
            "default_servings": 1,
            "dislikes": "",

        }

def signup_page():
    _init_signup_state()
    step = st.session_state.signup_step
    data = st.session_state.signup_data

    st.set_page_config(page_title="Sign Up", page_icon="📝", layout="wide")
    st.title("Sign Up for Smart Bites")
    st.write("Create an account — move through the steps to finish signup.")

    # Progress indicator
    total_steps = 4
    progress = int((step / total_steps) * 100)
    st.progress(progress)



    # STEP 0: Choose username
    if step == 0:
        st.header("Step 1 — Choose a username")
        with st.form(key="signup_step_0"):
            username = st.text_input("Choose a username", value=data.get("username", ""))
            next_clicked = st.form_submit_button("Next")

            if next_clicked:
                if username.strip() == "":
                    st.error("Please enter a username.")
                elif username in USER_CREDENTIALS:
                    st.error("Username already exists.")
                else:
                    st.session_state.signup_data["username"] = username.strip()
                    st.session_state.signup_step = 1
                    st.rerun()

    # STEP 1: Password
    elif step == 1:
        st.header("Step 2 — Choose a password")
        with st.form(key="signup_step_1"):
            password = st.text_input("Choose a password", type="password", value=data.get("password", ""))
            confirm = st.text_input("Confirm password", type="password", value=data.get("confirm", ""))
            next_clicked = st.form_submit_button("Next")

            if next_clicked:
                if not password or not confirm:
                    st.error("Please fill both password fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    st.session_state.signup_data["password"] = password
                    st.session_state.signup_data["confirm"] = confirm
                    st.session_state.signup_step = 2
                    st.rerun()

    # STEP 2: Profile / consent (proceed to preferences)
    elif step == 2:
        st.header("Step 3 — Profile and consent")
        with st.form(key="signup_step_2"):
            email = st.text_input("Email (optional)", value=data.get("email", ""))
            next_clicked = st.form_submit_button("Next: Preferences")

            if next_clicked:
                st.session_state.signup_data["email"] = email
                st.session_state.signup_step = 3
                st.rerun()

    # STEP 3: Preferences (diet, allergies, cuisines, servings)
    elif step == 3:
        st.header("Step 4 — Preferences")
        with st.form(key="signup_step_3"):
            diet_options = ["None", "Vegetarian", "Vegan", "Pescatarian", "Keto", "Gluten-Free", "Dairy-Free"]
            cuisine_options = ["Italian", "Mexican", "Indian", "Chinese", "Mediterranean", "American", "Portuguese", "Other"]

            dietary = st.multiselect("Dietary preferences (choose any)", options=diet_options, default=data.get("dietary_preferences", []))
            allergies = st.text_input("Allergies (comma-separated)", value=data.get("allergies", ""))
            restrictions = st.text_input("Dietary restrictions (comma-separated)", value=data.get("restrictions", ""))
            cuisines = st.multiselect("Preferred cuisines", options=cuisine_options, default=data.get("preferred_cuisines", []))
            servings = st.number_input("Default servings", min_value=1, max_value=10, value=data.get("default_servings", 1))
            dislikes = st.text_input("Dislikes (comma-separated)", value=data.get("dislikes", ""))

            create_clicked = st.form_submit_button("Create account")

            if create_clicked:
                # save preferences
                st.session_state.signup_data["dietary_preferences"] = dietary
                st.session_state.signup_data["allergies"] = allergies
                st.session_state.signup_data["restrictions"] = restrictions
                st.session_state.signup_data["preferred_cuisines"] = cuisines
                st.session_state.signup_data["default_servings"] = int(servings)
                st.session_state.signup_data["dislikes"] = dislikes

                username = st.session_state.signup_data.get("username")
                password = st.session_state.signup_data.get("password")
                # Final sanity checks
                if not username or not password:
                    st.error("Missing username or password — please go back and complete the fields.")
                else:
                    # Create account (in-memory USER_CREDENTIALS dict for this demo)
                    USER_CREDENTIALS[username] = password

                    # Optionally attach profile to session (demo storage)
                    st.session_state["user_profile"] = {
                        "username": username,
                        "email": st.session_state.signup_data.get("email"),
                        "dietary_preferences": st.session_state.signup_data.get("dietary_preferences"),
                        "allergies": st.session_state.signup_data.get("allergies"),
                        "restrictions": st.session_state.signup_data.get("restrictions"),
                        "preferred_cuisines": st.session_state.signup_data.get("preferred_cuisines"),
                        "default_servings": st.session_state.signup_data.get("default_servings"),
                        "dislikes": st.session_state.signup_data.get("dislikes"),
                    }

                    # Mark logged in
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    # reset/clear wizard
                    st.session_state.signup_step = 0
                    st.session_state.signup_data = {
                        "username": "",
                        "password": "",
                        "confirm": "",
                        "email": "",
                        "dietary_preferences": [],
                        "allergies": "",
                        "restrictions": "",
                        "preferred_cuisines": [],
                        "default_servings": 1,
                        "dislikes": "",
                    }

                    st.success("Account created successfully! You are now logged in.")
                    st.rerun()


    # Back button (disabled on first step)
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("Back", type = 'tertiary') and step > 0:
            st.session_state.signup_step = step - 1
            st.rerun()

    # Optionally add a cancel/clear button
    with col3:
        if st.button("Cancel / Clear", type = 'tertiary'):
            st.session_state.signup_step = 0
            st.session_state.signup_data = {
                "username": "",
                "password": "",
                "confirm": "",
                "email": "",
            }
            st.rerun()
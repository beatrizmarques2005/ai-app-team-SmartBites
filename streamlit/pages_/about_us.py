import streamlit as st

def about_us_page():
    st.set_page_config(
        page_title="*SmartBites* | About Us",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/info-circle.svg",
        layout="centered",
        initial_sidebar_state='collapsed'
    )



    st.markdown(
                """
        <h1 style="margin: 0.25rem 0;">About <em>SmartBites</em></h1>
        <div style="text-align: justify;">
        <p><em>SmartBites</em> is an intelligent meal-planning web app designed to simplify everyday food decisions — from “What should I cook?” to “What do I actually have at home?”</p>
        <p>Built with student life in mind, <em>SmartBites</em> helps users plan meals, manage their pantry, and reduce food waste with minimal effort. The platform suggests recipes based on available ingredients, supports meal planning across the week, and keeps track of groceries so nothing gets forgotten at the back of the fridge.</p>
        <p>With an AI-powered assistant at its core, <em>SmartBites</em> adapts to users’ preferences, schedules, and habits, making meal planning faster, smarter, and far less stressful. Whether you’re short on time, motivation, or ideas, <em>SmartBites</em> helps turn everyday ingredients into realistic meal plans — no overthinking required.</p>
        <h2 style="margin: 0.25rem 0;">Developers</h2>
        <p><em>SmartBites</em> was developed as a capstone project by four final-year undergraduate students who got tired of asking the same question every day: “What are we eating today?”</p>
        <p>What started as a student struggle quickly became a fully functional prototype built through collaboration, creativity, and a shared belief that technology should make everyday life easier — especially when food is involved.</p>
        <p>Built by students, for students (and anyone else who’s ever stared at an empty fridge).</p>
        </div>
                """,
                unsafe_allow_html=True,
            )
import streamlit as st
import pandas as pd
from transformers import pipeline
import sqlite3
import hashlib
from datetime import datetime
import os

# Create a 'database' directory if it doesn't exist
if not os.path.exists('database'):
    os.makedirs('database')

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Database setup
def init_db():
    try:
        conn = sqlite3.connect('database/users.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username TEXT PRIMARY KEY, 
                     password TEXT, 
                     email TEXT,
                     created_at TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database Error: {str(e)}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    try:
        conn = sqlite3.connect('database/users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?',
                 (username, hash_password(password)))
        result = c.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        st.error(f"Login Error: {str(e)}")
        return False

def register_user(username, email, password):
    try:
        conn = sqlite3.connect('database/users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                 (username, hash_password(password), email, 
                  datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        st.error(f"Registration Error: {str(e)}")
        return False

def main():
    st.title("📊 DataQueryAI")
    st.write("Your Data, Your Language, Your Insights")
    
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Sign Up", "Login"])
        
        with tab1:
            st.header("Create Account")
            signup_username = st.text_input("Username", key="signup_username")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            
            if st.button("Sign Up", key="signup_button"):
                if signup_username and signup_email and signup_password:
                    if register_user(signup_username, signup_email, signup_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists or registration failed.")
                else:
                    st.error("Please fill in all fields")
        
        with tab2:
            st.header("Welcome Back")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_button"):
                if login_username and login_password:
                    if login_user(login_username, login_password):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please fill in all fields")
    
    else:
        st.write(f"Welcome back, {st.session_state.username}! 👋")
        
        if st.button("Logout", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
        
        uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.write("### Data Preview")
            st.dataframe(df.head())
            
            question = st.text_input("Ask a question about your data:")
            if st.button("Get Answer") and question:
                try:
                    # Initialize the QA pipeline
                    qa_pipeline = pipeline(
                        task="table-question-answering",
                        model="google/tapas-base-finetuned-wtq"
                    )
                    
                    # Process the question
                    table = df.astype(str).to_dict(orient='records')
                    answer = qa_pipeline(table=table, query=question)
                    
                    st.success("### Answer")
                    st.write(answer['answer'])
                except Exception as e:
                    st.error(f"Error analyzing data: {str(e)}")

if __name__ == "__main__":
    try:
        init_db()
        main()
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
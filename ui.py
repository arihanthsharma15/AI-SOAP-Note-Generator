import streamlit as st
import requests

# --- Page Configuration and Backend URL (No change) ---
st.set_page_config(page_title="MedNotes.ai", page_icon="🩺", layout="wide")
LOGIN_URL = "http://127.0.0.1:8000/login/"
GENERATE_NOTE_URL = "http://127.0.0.1:8000/notes/generate/"

# --- App State Management (No change) ---
if 'token' not in st.session_state:
    st.session_state.token = None
if 'soap_note' not in st.session_state:
    st.session_state.soap_note = ""

# --- LOGIN PAGE (No change) ---
if st.session_state.token is None:
    st.title("Welcome to MedNotes.ai")
    st.header("Please Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        if login_button:
            if email and password:
                with st.spinner("Authenticating..."):
                    try:
                        login_data = {'username': email, 'password': password}
                        response = requests.post(LOGIN_URL, data=login_data)
                        if response.status_code == 200:
                            token_data = response.json()
                            st.session_state.token = token_data['access_token']
                            st.rerun()
                        else:
                            st.error(f"Login failed: {response.json().get('detail')}")
                    except requests.exceptions.RequestException:
                        st.error("Connection Error! Is the backend running?")
            else:
                st.warning("Please enter both email and password.")

# =====================================================================
# --- MAIN APPLICATION PAGE (YAHAN PE CHANGES HAIN) ---
# =====================================================================
else:
    st.sidebar.title(f"👨‍⚕️ Welcome, Doctor!")
    st.sidebar.success("You are logged in.")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()

    st.title("🩺 AI SOAP Note Generator")
    st.info("Paste a transcript below to generate a clinical SOAP note.")

    SAMPLE_TRANSCRIPT = "Patient complains of a persistent dry cough for one week. Doctor observed a fever of 101 F. Plan is to prescribe antibiotics."
    transcript_input = st.text_area("Patient Transcript:", value=SAMPLE_TRANSCRIPT, height=300)

    if st.button("Generate SOAP Note", type="primary", use_container_width=True):
        if transcript_input.strip():
            with st.spinner("AI is analyzing and generating the note..."):
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    payload = {"transcript_text": transcript_input}
                    response = requests.post(GENERATE_NOTE_URL, json=payload, headers=headers)
                    if response.status_code == 200:
                        st.balloons()
                        result = response.json()
                        st.session_state.soap_note = result.get("soap_note_content", "Error parsing note.")
                    else:
                        st.error(f"Error from server: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException:
                    st.error("Connection Error!")
        else:
            st.warning("Please enter a transcript.")

    st.subheader("Generated SOAP Note:")
    
    # --- THIS IS THE NEW, SMART FORMATTING LOGIC ---
    if st.session_state.soap_note:
        # We split the AI's response by the section titles
        # This will work even if the AI misses a section
        sections = {
            "Subjective:": "Objective:",
            "Objective:": "Assessment:",
            "Assessment:": "Plan:",
            "Plan:": None # The last section
        }
        
        # Get the full text from the AI
        note_text = st.session_state.soap_note

        # Use a container for a nice border
        with st.container(border=True):
            for section_title, next_section_title in sections.items():
                try:
                    # Find the start of the current section
                    start_index = note_text.index(section_title)
                    
                    # Find the start of the next section, or the end of the string
                    if next_section_title:
                        end_index = note_text.index(next_section_title)
                    else:
                        end_index = len(note_text)
                    
                    # Extract the content for the current section
                    section_content = note_text[start_index + len(section_title):end_index].strip()

                    # Display it with a subheader
                    st.markdown(f"**{section_title}**")
                    st.markdown(f"> {section_content}") # Using blockquote for nice formatting

                except ValueError:
                    # This happens if a section title is not found in the AI's response
                    pass # We just skip it
    else:
        st.write("The generated note will appear here...")
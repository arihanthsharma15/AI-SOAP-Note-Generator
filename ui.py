# === PART 1: IMPORTS (Zaroori Auzaar) ===
import streamlit as st
import requests # Yeh library humare UI ko backend se baat karne me help karegi

# === PART 2: CONFIGURATION (Basic Setup) ===

# Set the title and icon that appear in the browser tab
st.set_page_config(
    page_title="AI SOAP Note Generator",
    page_icon="🩺",
    layout="wide" # Use the full width of the page
)

# This is the address of our FastAPI backend's "door"
BACKEND_URL = "http://127.0.0.1:8000/generate-soap-note/"

# A sample transcript for users to test easily
SAMPLE_TRANSCRIPT = """Doctor: Good morning, Mr. Sharma. What brings you in today?
Patient: Good morning, doctor. I've had this persistent cough for about two weeks now. It's mostly dry, but sometimes I get a bit of phlegm. I've also been feeling very tired and have had a low-grade fever, around 99.5 F, especially in the evenings. I checked my temperature this morning and it was 99.2 F.
Doctor: I see. Any other symptoms? Shortness of breath, chest pain, or body aches?
Patient: No real chest pain, thankfully. But I do feel some minor body aches all over, and I definitely get out of breath more easily than usual, like when I climb the stairs to my apartment.
Doctor: Okay. Let me check your vitals..."""

# === PART 3: THE USER INTERFACE (The Main App) ===

# Display the title on the page
st.title("🩺 AI SOAP Note Generator")
st.info("This app uses a local LLM (TinyLlama) and a RAG pipeline to create structured clinical notes from patient transcripts.")

# Create two columns for a cleaner layout
col1, col2 = st.columns(2)

# --- The Left Column: User Input ---
with col1:
    st.subheader("Patient Transcript")
    # Create a text area for the user to paste the transcript
    transcript_input = st.text_area(
        "Paste the Doctor-Patient Transcript Here:", 
        value=SAMPLE_TRANSCRIPT, # Pre-fill with our sample
        height=400
    )
    
    # Create the "Generate" button
    generate_button = st.button("Generate SOAP Note", type="primary", use_container_width=True)

# --- The Right Column: AI Output ---
with col2:
    st.subheader("Generated SOAP Note")
    
    # This is where the AI's response will be displayed
    # We use a session_state variable to "remember" the last generated note
    if 'soap_note' not in st.session_state:
        st.session_state.soap_note = "The generated note will appear here..."

    # When the user clicks the button
    if generate_button:
        # Check if the user has entered any text
        if transcript_input.strip():
            # Show a "spinner" message while the AI is working
            with st.spinner("The AI is reading the transcript and writing the note... This may take a moment."):
                try:
                    # --- THIS IS THE MAGIC ---
                    # Send the transcript to our FastAPI backend
                    payload = {"content": transcript_input}
                    response = requests.post(BACKEND_URL, json=payload)

                    if response.status_code == 200:
                        # If successful, get the result and store it
                        result = response.json()
                        st.session_state.soap_note = result.get("soap_note", "Error: Could not parse SOAP note.")
                        st.balloons() # A fun little celebration!
                    else:
                        # If the server returned an error
                        error_message = f"Error from server: {response.status_code} - {response.text}"
                        st.session_state.soap_note = error_message
                        st.error(error_message)

                except requests.exceptions.RequestException as e:
                    # If we couldn't even connect to the server
                    error_message = f"Connection Error! Please ensure the FastAPI backend is running. Details: {e}"
                    st.session_state.soap_note = error_message
                    st.error(error_message)
        else:
            st.warning("Please paste a transcript before generating.")

    # Display the (new or old) SOAP note
    st.markdown(st.session_state.soap_note)
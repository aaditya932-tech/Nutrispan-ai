import streamlit as st
import json
from google import genai
from google.genai import types

st.set_page_config(page_title="NutriSpan AI", layout="wide")

# Securely get the API key from Streamlit's secrets settings
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("Please configure your GEMINI_API_KEY in the Streamlit Cloud Settings.")
    st.stop()

# Sidebar Configuration
st.sidebar.title("👤 User Profile Configuration")
user_mode = st.sidebar.selectbox("Choose Mode", ["Elite Fitness (Gym Freak)", "Golden Care (Elderly Mode)"])

profile_details = {}

if user_mode == "Elite Fitness (Gym Freak)":
    st.sidebar.subheader("🏋️ Gym Metrics")
    profile_details['goal'] = st.sidebar.selectbox("Your Fitness Goal", ["Bulking", "Cutting", "Clean Eating"])
    profile_details['protein_target'] = st.sidebar.slider("Daily Protein Target (g)", 100, 250, 150)
    st.title("💪 NutriSpan AI: Performance Engine")
else:
    st.sidebar.subheader("👵 Health Metrics")
    conditions = st.sidebar.multiselect(
        "Existing Chronic Conditions", 
        ["Hypertension (High BP)", "Type 2 Diabetes", "High Cholesterol", "None"]
    )
    profile_details['conditions'] = conditions
    st.title("💙 NutriSpan AI: Golden Longevity Care")

st.divider()

# --- Core App Functionality ---
st.subheader("📸 Log Your Meal")
input_choice = st.radio("How do you want to log your food?", ["Type Text", "Upload Photo"])

food_input = None
input_type = "text"

if input_choice == "Type Text":
    food_input = st.text_input("Example: I ate a bowl of oats with milk and a banana")
    input_type = "text"
else:
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        food_input = uploaded_file.read()
        input_type = "image"

if st.button("Analyze & Log Meal"):
    if food_input:
        with st.spinner("AI Engine analyzing nutrition metrics..."):
            try:
                base_prompt = """
                You are an expert nutrition AI. Analyze the provided food item.
                You MUST respond ONLY with a valid JSON object matching this structure:
                {
                  "food_name": "Name of the food",
                  "calories": 250,
                  "protein_g": 20,
                  "carbs_g": 30,
                  "fat_g": 5,
                  "sodium_mg": 150,
                  "sugar_g": 5,
                  "health_verdict": "Your personalized feedback here based on the profile context."
                }
                """
                if user_mode == "Elite Fitness (Gym Freak)":
                    profile_context = f"The user is a fitness enthusiast. Their goal is {profile_details['goal']}. Focus on muscle building."
                else:
                    profile_context = f"The user is elderly with conditions: {', '.join(profile_details['conditions'])}. Flag dangerous elements like sugar or sodium."
                
                full_prompt = base_prompt + "\n" + profile_context
                
                if input_type == "image":
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[types.Part.from_bytes(data=food_input, mime_type='image/jpeg'), full_prompt]
                    )
                else:
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=[food_input, full_prompt])
                
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_json)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Food Item", result['food_name'])
                col2.metric("Total Calories", f"{result['calories']} kcal")
                col3.metric("Protein", f"{result['protein_g']}g")
                
                st.subheader("📋 AI Health Verdict")
                if user_mode == "Golden Care (Elderly Mode)" and ("Warning" in result['health_verdict'] or result['sodium_mg'] > 300 or result['sugar_g'] > 10):
                    st.error(result['health_verdict'])
                else:
                    st.success(result['health_verdict'])
                    
            except Exception as e:
                st.error(f"Error processing. Make sure your API Key is valid. Error: {e}")
    else:
        st.warning("Please provide input first.")

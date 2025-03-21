import os
import openai
import streamlit as st
import re
from dotenv import load_dotenv, find_dotenv
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import base64

# Load environment variables
_ = load_dotenv(find_dotenv())

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# temporary for debugging purpose
print("OPENAI_API_KEY:", os.environ.get("OPENAI_API_KEY"))

# Initialize geocoder
geolocator = Nominatim(user_agent="nitti_bot")

# ===========================
# CUSTOM UI: Inject custom CSS for styling using Nitti colors (bright yellow, white, and black)
# ===========================
st.markdown(
    """
    <style>
    /* Global Page Background */
    .reportview-container, .main {
        background-color: #ffffff;
    }
    /* Header styling */
    .header {
        background-color: #FFD700; /* Bright yellow */
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .header img {
        width: 50px;
        height: 50px;
        vertical-align: middle;
    }
    .header h1 {
        display: inline;
        margin-left: 10px;
        vertical-align: middle;
        color: #000000; /* Black text */
        font-family: sans-serif;
    }
    /* Chat container styling */
    .chat-container {
        max-width: 800px;
        margin: auto;
        padding: 10px;
    }
    /* User message bubble styling */
    .user-message {
        background-color: #FFD700; /* bright yellow */
        color: #000000;
        padding: 10px;
        border-radius: 21px;
        margin: 10px 0;
        text-align: right;
        max-width: 70%;
        float: right;
        clear: both;
        font-family: sans-serif;
    }
    /* Bot message bubble styling */
    .bot-message {
        background-color: #000000; /* black */
        color: #ffffff;
        padding: 10px;
        border-radius: 21px;
        margin: 10px 0;
        text-align: left;
        max-width: 70%;
        float: left;
        clear: both;
        font-family: sans-serif;
    }
    /* Input box styling: override Streamlit's default input style */
    input, textarea {
        border-radius: 21px !important;
        border: 2px solid #000000 !important;
        padding: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===========================
# CUSTOM UI: Header with a yellow box around the customer service icon and title
# ===========================
def get_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

icon_base64 = get_base64("icon.png")

st.markdown(
    f"""
    <div style="background-color: #FFD700; padding: 10px; border-radius: 10px; text-align: center;">
        <img src="data:image/png;base64,{icon_base64}" width="50" style="vertical-align: middle;" alt="Customer Service Icon">
        <h1 style="display: inline; color: #ffffff; font-family: sans-serif; margin-left: 10px;">
            Protection, Comfort, Durability, Everyday
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ===========================
# Original Session State Initialization
# ===========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_enabled" not in st.session_state:
    st.session_state.chat_enabled = True  # Set to True to allow input field to appear
if "chat_context" not in st.session_state:
    st.session_state.chat_context = [
        {'role': 'system', 'content': """
You are CustomerserviceBot for Terrapeak, an automated service to assist with incoming enquiries.
You first greet the customer, then assist with the enquiry regarding our services,
and then ask if our representatives can reach out to them.
If you do not know the answer, ask if it is okay that Customer Service contacts them.
When they request a live chat follow the next steps:
- first try to have them ask their question to you
- if they insist then ask their phone number and email and inform them that a callback will be handled as soon as possible but within 1 working day
- if they want a live chat immediately then provide Terrapeak phonenumber: +6580619479
- inform them that an email is also possible if there is no reply at: Terrapeak@enquiry.com
If customer sks address then inform them that at the moment only call back can be arranged 
You wait to collect all the information, then summarize it and check for a final time if the customer needs anything else.
Finally, request their phone number and email.
When asking for a phone number, always check the country code.
Ensure clarity on requested services and customer details.
You respond in a short, friendly, and conversational style, without repeating questions more than twice.
Orders cannot be placed via this chatbot; instead, collect the user's contact details for a sales follow-up.
services provided are:
- Consulting
- trading
- Automation Solutions
- Coaching & Training

Content you can select from for consulting enquiries:
Phase 1: Business Discovery & Strategy Development
Laying the foundation for Expansion, (Sales) growth, and AI Integration.
Prior to moving forward with implementation, we take the time to learn, analyze, and create a tailored plan aligned with your business objectives. This phase guarantees a well-informed, data-driven plan to achieve long-term success.

a. Initial Consultation & Business Assessment:
- Understanding Your Vision, Challenges & Goals
We start with a detailed conversation to more clearly comprehend your business model, growth goals, sales performance, or readiness for artificial intelligence.
Our experts assess growth opportunities, operating weaknesses & strengths, and key challenges to focus on.
We map out a preliminary roadmap according to your specific business requirements.

b. Market & Feasibility Analysis:
Data-driven Insights for Strategic Decision-making
For market expansion: We analyze industry trends, competitor positioning, and regulatory landscapes in APAC.
For sales optimization: We review your sales pipeline, customer acquisition strategies, and revenue models.
As for AI implementation, we assess your current technological base and identify areas of important automation potential.
We offer a risk assessment along with actionable insights to optimize the most effective approach.

c. Strategy Formulation & Customized Roadmap:
Personalized Growth and Expansion Strategy
Based on our findings, we develop a simple, step-by-step strategy for your business. For market expansion, we map entry strategies, distributor partnerships, and compliance pathways. For growth in revenue, we simplify pricing models, sales organizations, and lead generation strategies. To facilitate AI integration, we develop a staged adoption plan to automate and streamline business processes. At the conclusion of Phase 1, you'll have a well-planned and implementable roadmap in hand.

"""} ]

# ✅ Validation functions
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_phone(phone):
    return re.match(r"^\+?\d{10,15}$", phone)

def validate_postal(postal_code):
    return re.match(r'^\d{6}$', postal_code) is not None

def get_coordinates(postal_code):
    try:
        location = geolocator.geocode(postal_code + ", Singapore")
        return (location.latitude, location.longitude) if location else None
    except Exception as e:
        st.error(f"Error fetching coordinates: {e}")
        return None

if "chat_context" not in st.session_state:
    st.session_state.chat_context = [
        {'role': 'system', 'content': "You are CustomerserviceBot for Nitti Safety Footwear. You assist with store locations and safety footwear inquiries."}
    ] + st.session_state.store_context

# OpenAI communication function (Original Code)
def get_completion_from_messages(user_messages, model="gpt-3.5-turbo", temperature=0):
    client = openai.OpenAI()
    messages = st.session_state.chat_context + user_messages
    if any(kw in user_messages[-1]["content"].lower() for kw in ["store", "nearest", "location", "buy", "address"]):
        store_info = "\n".join(
            f"{name}: 📍 {info['address']}, 📞 {info['tel']}"
            for name, info in stores.items()
        )
        messages.append({"role": "system", "content": f"Here are the store locations:\n{store_info}"})
    response = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
    return response.choices[0].message.content

# ===========================
# User Details Input (Original Code)
# ===========================
st.title("Welcome to Nitti Customer Service")
st.markdown("📢 **Enter your contact details before chatting:**")

email = st.text_input("Enter your email:", key="email_input")
phone = st.text_input("Enter your phone number:", key="phone_input")
country = st.selectbox("Select Country", ["Singapore", "Malaysia", "Indonesia"], key="country_dropdown")
postal = st.text_input("Enter your postal code (Required if in SG):", key="postal_input")

def validate_and_start():
    if not is_valid_email(email):
        return "❌ Invalid email."
    if not is_valid_phone(phone):
        return "❌ Invalid phone number."
    if country == "Singapore" and not validate_postal(postal):
        return "❌ Invalid postal code."
    st.session_state.chat_enabled = True
    if country == "Singapore":
        store_info = find_nearest_store(postal)
        st.session_state.chat_context.append(
            {"role": "system", "content": f"The nearest store to the user is: {store_info}"}
        )
    else:
        store_info = "No store information available for this country."
    return f"✅ **Details saved! {store_info}**"

if st.button("Submit Details", key="submit_button"):
    validation_message = validate_and_start()
    st.markdown(validation_message, unsafe_allow_html=True)

# ===========================
# CUSTOM UI: Display Chat History with Styled Chat Bubbles
# (This replaces the original plain text display block.)
# ===========================
st.markdown("---")
st.markdown("**💬 Chat with the Nitti Safety Footwear Bot:**")

with st.container():
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f'<div class="user-message">{chat["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{chat["content"]}</div>', unsafe_allow_html=True)

# ===========================
# CUSTOM UI: Chat Input Field with Send Button
# (Replaces the original plain text input.)
# ===========================
if "chat_input_key" not in st.session_state:
    st.session_state.chat_input_key = 0

if st.session_state.chat_enabled:
    user_input = st.text_input(
        "Type your message here...",
        key=f"chat_input_{st.session_state.chat_input_key}",
        value=""
    )

    if st.button("Send", key="send_button"):
        if user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
            response = get_completion_from_messages(st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.session_state.chat_input_key += 1
            st.rerun()

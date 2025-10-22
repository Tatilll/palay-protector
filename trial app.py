import base64
import streamlit as st
from PIL import Image
import sqlite3
import random
import string
import time
import smtplib
from email.message import EmailMessage
import io
from inference_sdk import InferenceHTTPClient

# ========== DATABASE SETUP ==========
# Simple SQLite database to store user accounts and detection history
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Table for user accounts
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        phone TEXT,
        password TEXT
    )
''')

# Table for detection history
cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        result TEXT,
        confidence REAL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
conn.commit()
conn.close()

# ========== SESSION STATE INITIALIZATION ==========
# Session state keeps track of user data across page interactions
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None
  
if "page" not in st.session_state:
    st.session_state.page = "login"

# ========== PAGE CONFIGURATION ==========
st.set_page_config(page_title="Palay Protector", layout="centered", page_icon="🌾")

# ========== MODERN CSS STYLING ==========
st.markdown("""
<style>
    /* ============================================
       GLOBAL STYLES - Base styling for entire app
       ============================================ */
    
    /* Import professional font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Apply font to all elements */
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Hide Streamlit's default branding elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main app background with gradient */
    .stApp {
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 50%, #ffffff 100%);
    }
    
    /* Container padding for better spacing */
    .main > .block-container {
        padding: 2rem 1rem 8rem 1rem;
        max-width: 800px;
    }
    
    /* ============================================
       HEADER STYLES - Logo and app title
       ============================================ */
    
    .app-header {
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 1rem 0 0.5rem 0;
        letter-spacing: 1px;
    }
    
    .app-subtitle {
        color: #5f6368;
        font-size: 0.95rem;
        font-weight: 400;
    }
    
    /* ============================================
       CARD COMPONENTS - Modern card-based layouts
       ============================================ */
    
    .modern-card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin: 1.5rem 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(46, 125, 50, 0.15);
    }
    
    /* Feature cards on home screen */
    .feature-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fdf9 100%);
        border-radius: 16px;
        padding: 2rem 1.5rem;
        text-align: center;
        border: 2px solid #e8f5e9;
        transition: all 0.3s ease;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .feature-card:hover {
        border-color: #4CAF50;
        transform: translateY(-8px);
        box-shadow: 0 12px 24px rgba(76, 175, 80, 0.2);
    }
    
    .feature-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        animation: bounce 2s infinite;
    }
    
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2e7d32;
        margin: 0.5rem 0;
    }
    
    .feature-desc {
        font-size: 0.9rem;
        color: #5f6368;
        line-height: 1.4;
    }
    
    /* ============================================
       FORM INPUTS - Styled text inputs and buttons
       ============================================ */
    
    /* Text input fields */
    .stTextInput input {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }
    
    .stTextInput input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
    }
    
    /* Primary buttons (green) */
    .stButton button {
        background: linear-gradient(135deg, #4CAF50 0%, #66bb6a 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        cursor: pointer;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
        background: linear-gradient(135deg, #388e3c 0%, #4CAF50 100%);
    }
    
    /* ============================================
       WEATHER FORECAST SECTION
       ============================================ */
    
    .weather-container {
        background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 2rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    .weather-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1976d2;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .forecast-scroll {
        display: flex;
        gap: 12px;
        overflow-x: auto;
        padding: 10px 5px;
    }
    
    .forecast-scroll::-webkit-scrollbar {
        height: 6px;
    }
    
    .forecast-scroll::-webkit-scrollbar-thumb {
        background: #4CAF50;
        border-radius: 10px;
    }
    
    .forecast-day {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        min-width: 90px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease;
    }
    
    .forecast-day:hover {
        transform: scale(1.05);
    }
    
    .day-label {
        font-weight: 600;
        color: #2e7d32;
        font-size: 0.9rem;
    }
    
    .temp-high {
        color: #ff5722;
        font-weight: 600;
    }
    
    .temp-low {
        color: #2196f3;
        font-weight: 600;
    }
    
    /* ============================================
       BOTTOM NAVIGATION BAR
       ============================================ */
    
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 600px;
        background: white;
        padding: 0.8rem 1rem 1.2rem 1rem;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
        border-radius: 20px 20px 0 0;
        z-index: 1000;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        transition: all 0.3s ease;
        cursor: pointer;
        min-width: 70px;
    }
    
    .nav-item:hover {
        background: #f1f8f4;
        transform: translateY(-3px);
    }
    
    .nav-item.active {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    }
    
    .nav-icon {
        font-size: 1.8rem;
        margin-bottom: 0.3rem;
        filter: grayscale(100%);
        opacity: 0.6;
        transition: all 0.3s ease;
    }
    
    .nav-item.active .nav-icon {
        filter: grayscale(0%);
        opacity: 1;
    }
    
    .nav-label {
        font-size: 0.75rem;
        color: #5f6368;
        font-weight: 500;
    }
    
    .nav-item.active .nav-label {
        color: #2e7d32;
        font-weight: 600;
    }
    
    /* ============================================
       DETECTION SCREEN STYLES
       ============================================ */
    
    .upload-zone {
        background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
        border: 3px dashed #4CAF50;
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        margin: 2rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        background: #f1f8f4;
        border-color: #2e7d32;
    }
    
    .upload-icon {
        font-size: 4rem;
        color: #4CAF50;
        margin-bottom: 1rem;
    }
    
    .upload-text {
        font-size: 1.2rem;
        color: #2e7d32;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .upload-subtext {
        color: #5f6368;
        font-size: 0.9rem;
    }
    
    .result-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        animation: slideInRight 0.5s ease-out;
    }
    
    .disease-detected {
        border-left-color: #ff5722;
    }
    
    .confidence-bar {
        height: 10px;
        background: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #4CAF50 0%, #66bb6a 100%);
        border-radius: 10px;
        transition: width 1s ease-out;
    }
    
    /* ============================================
       HISTORY TABLE STYLES
       ============================================ */
    
    .history-table {
        width: 100%;
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    .history-table th {
        background: linear-gradient(135deg, #4CAF50 0%, #66bb6a 100%);
        color: white;
        padding: 1rem;
        font-weight: 600;
        text-align: left;
    }
    
    .history-table td {
        padding: 1rem;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .history-table tr:hover {
        background: #f1f8f4;
    }
    
    .remedy-btn {
        background: #2e7d32;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.85rem;
        transition: all 0.3s ease;
        display: inline-block;
    }
    
    .remedy-btn:hover {
        background: #1b5e20;
        transform: scale(1.05);
    }
    
    /* ============================================
       ANIMATIONS - Smooth entrance effects
       ============================================ */
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes bounce {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-10px);
        }
    }
    
    /* ============================================
       INFO/TIP BOXES
       ============================================ */
    
    .info-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffffff 100%);
        border-left: 4px solid #ff9800;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }
    
    .info-title {
        font-weight: 600;
        color: #e65100;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .info-text {
        color: #5f6368;
        line-height: 1.6;
    }
    
    /* ============================================
       PROFILE METRICS
       ============================================ */
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #4CAF50;
    }
    
    .metric-label {
        color: #5f6368;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* ============================================
       RESPONSIVE DESIGN - Mobile optimization
       ============================================ */
    
    @media (max-width: 768px) {
        .main > .block-container {
            padding: 1rem 0.5rem 8rem 0.5rem;
        }
        
        .modern-card {
            padding: 1.5rem;
        }
        
        .feature-card {
            height: 180px;
            padding: 1.5rem 1rem;
        }
        
        .app-title {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS ==========

def show_header():
    """Display app header with logo and title"""
    st.markdown("""
        <div class="app-header">
            <div class="app-title">🌾 PALAY PROTECTOR</div>
            <div class="app-subtitle">AI-Powered Rice Disease Detection System</div>
        </div>
    """, unsafe_allow_html=True)

def show_bottom_nav(active_page):
    """Display bottom navigation bar with active page highlighted"""
    st.markdown(f"""
        <div class="bottom-nav">
            <div class="nav-item {'active' if active_page == 'home' else ''}">
                <div class="nav-icon">🏠</div>
                <div class="nav-label">Home</div>
            </div>
            <div class="nav-item {'active' if active_page == 'detect' else ''}">
                <div class="nav-icon">🔍</div>
                <div class="nav-label">Detect</div>
            </div>
            <div class="nav-item {'active' if active_page == 'library' else ''}">
                <div class="nav-icon">📚</div>
                <div class="nav-label">Library</div>
            </div>
            <div class="nav-item {'active' if active_page == 'profile' else ''}">
                <div class="nav-icon">👤</div>
                <div class="nav-label">Profile</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons (hidden but functional)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Home", key=f"nav_home_{active_page}"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("Detect", key=f"nav_detect_{active_page}"):
            st.session_state.page = "detect"
            st.rerun()
    with col3:
        if st.button("Library", key=f"nav_library_{active_page}"):
            st.session_state.page = "library"
            st.rerun()
    with col4:
        if st.button("Profile", key=f"nav_profile_{active_page}"):
            st.session_state.page = "profile"
            st.rerun()

def generate_otp(length=6):
    """Generate random 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(receiver_email, otp):
    """Send OTP code to user's email"""
    try:
        msg = EmailMessage()
        msg['Subject'] = "Palay Protector - Your OTP Code"
        msg['From'] = "palayprotector@gmail.com"
        msg['To'] = receiver_email
        msg.set_content(f"Your OTP code is: {otp}\nValid for 3 minutes only.")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("palayprotector@gmail.com", "dfhzpiitlsgkptmg")
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return False

def init_client():
    """Initialize Roboflow AI client for disease detection"""
    return InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key="KajReyLpzYwgJ8fJ8sVd"
    )

# ========== LOGIN SCREEN ==========
if st.session_state.page == "login":
    show_header()
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("### 🔐 Welcome Back")
    st.markdown("Sign in to continue protecting your rice crops")
    
    username = st.text_input("Username", key="login_username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Forgot?", key="goto_forgot"):
            st.session_state.page = "otp_verification"
            st.rerun()
    
    if st.button("LOG IN", key="login_button"):
        if username and password:
            # Check database for matching credentials
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", 
                         (username, password))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                # Login successful - store user data in session
                st.session_state.user_id = user[0]
                st.session_state.logged_user = user[1]
                st.session_state.page = "home"
                st.success("✅ Login successful!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
        else:
            st.error("⚠️ Please enter both username and password")
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #5f6368;'>Don't have an account?</div>", 
                unsafe_allow_html=True)
    
    if st.button("CREATE ACCOUNT", key="signup_redirect"):
        st.session_state.page = "signup"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ========== SIGNUP SCREEN ==========
elif st.session_state.page == "signup":
    show_header()
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Create Your Account")
    st.markdown("Join Palay Protector to start detecting rice diseases")
    
    username = st.text_input("Username", key="signup_username", placeholder="Choose a username")
    email = st.text_input("Email", key="signup_email", placeholder="your.email@example.com")
    phone = st.text_input("Phone Number", key="signup_phone", placeholder="+63 XXX XXX XXXX")
    password = st.text_input("Password", type="password", key="signup_password", 
                            placeholder="Create a strong password")
    confirm_password = st.text_input("Confirm Password", type="password", 
                                    key="signup_confirm_password", placeholder="Re-enter password")
    
    if st.button("CREATE ACCOUNT", key="create_account"):
        if password != confirm_password:
            st.error("❌ Passwords do not match")
        elif len(password) < 6:
            st.error("⚠️ Password must be at least 6 characters")
        else:
            try:
                # Insert new user into database
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, email, phone, password)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, phone, password))
                conn.commit()
                conn.close()
                
                st.success("✅ Account created successfully!")
                time.sleep(1)
                st.session_state.page = "login"
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("❌ Username already exists")
    
    st.markdown("---")
    if st.button("← BACK TO LOGIN", key="back_to_login"):
        st.session_state.page = "login"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ========== OTP VERIFICATION SCREEN ==========
elif st.session_state.page == "otp_verification":
    show_header()
    
    if "otp_stage" not in st.session_state:
        st.session_state.otp_stage = "input_email"
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    
    if st.session_state.otp_stage == "input_email":
        st.markdown("### 📧 Forgot Password")
        st.markdown("Enter your email to receive OTP code")
        
        input_email = st.text_input("Email Address", key="otp_email_input", 
                                   placeholder="your.email@example.com")
        
        if st.button("SEND OTP", key="send_otp_btn"):
            if input_email:
                # Check if email exists in database
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE email = ?", (input_email,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    # Generate and send OTP
                    otp = generate_otp()
                    sent = send_otp_email(input_email, otp)
                    if sent:
                        st.session_state.generated_otp = otp
                        st.session_state.otp_start_time = time.time()
                        st.session_state.otp_email = input_email
                        st.session_state.verified_user = result[0]
                        st.session_state.otp_stage = "verify_otp"
                        st.success("✅ OTP sent to your email!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to send OTP")
                else:
                    st.error("❌ Email not found")
        
        if st.button("← BACK TO LOGIN", key="back_to_login"):
            st.session_state.page = "login"
            st.rerun()
    
    elif st.session_state.otp_stage == "verify_otp":
        st.markdown("### 🔢 Enter OTP Code")
        
        # Calculate remaining time
        time_left = 180 - (time.time() - st.session_state.otp_start_time)
        
        if time_left > 0:
            minutes = int(time_left // 60)
            seconds = int(time_left % 60)
            st.info(f"⏱️ OTP expires in {minutes:02d}:{seconds:02d}")
        else:
            st.error("❌ OTP has expired")
        
        entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6, 
                                   key="otp_input", placeholder="000000")
        
        if st.button("VERIFY OTP", key="verify_otp_btn"):
            if entered_otp == st.session_state.generated_otp and time_left > 0:
                st.success("✅ OTP Verified!")
                time.sleep(1)
                st.session_state.page = "change_password"
                st.rerun()
            elif time_left <= 0:
                st.error("❌ OTP has expired. Please resend.")
            else:
                st.error("❌ Invalid OTP")
        
        if st.button("🔄 RESEND OTP", key="resend_otp_btn"):
            new_otp = generate_otp()
            st.session_state.generated_otp = new_otp
            st.session_state.otp_start_time = time.time()
            send_otp_email(st.session_state.otp_email, new_otp)
            st.success("✅ New OTP sent!")
            st.rerun()
        
        # Auto-refresh to update timer
        if time_left > 0:
            time.sleep(1)
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ========== CHANGE PASSWORD SCREEN ==========
elif st.session_state.page == "change_password":
    show_header()
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("### 🔑 Create New Password")
    
    new_password = st.text_input("New Password", type="password", 
                               key="new_password", placeholder="Enter new password")
    confirm_password = st.text_input("Confirm Password", type="password", 
                                   key="confirm_password", placeholder="Re-enter password")
    
    if st.button("CHANGE PASSWORD", key="change_pwd_btn"):
        if not new_password or not confirm_password:
            st.error("⚠️ Please fill in both fields")
        elif new_password != confirm_password:
            st.error("❌ Passwords do not match")
        elif len(new_password) < 6:
            st.error("⚠️ Password must be at least 6 characters")
        else:
            # Update password in database
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE email = ?", 
                         (new_password, st.session_state.otp_email))
            conn.commit()
            conn.close()
            
            st.success("✅ Password changed successfully!")
            time.sleep(1)
            
            # Clear OTP session data
            for key in ['generated_otp', 'otp_start_time', 'otp_email', 'verified_user', 'otp_stage']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.page = "login"
            st.rerun()
    
    if st.button("← BACK TO LOGIN", key="back_to_login_from_pwd"):
        st.session_state.page = "login"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ========== HOME SCREEN ==========
elif st.session_state.page == "home":
    show_header()
    
    # Welcome message with user's name
    st.markdown(f"""
        <div class="modern-card" style="text-align: center;">
            <h2 style="color: #2e7d32; margin-bottom: 0.5rem;">
                Welcome back, <span style="color: #4CAF50;">{st.session_state.logged_user}</span>! 👋
            </h2>
            <p style="color: #5f6368;">Ready to protect your palay today?</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Weather forecast section
    from datetime import datetime, timedelta
    
    def get_7day_forecast():
        """Generate 7-day weather forecast (simulated data for demo)"""
        today = datetime.now()
        temp_ranges = [
            {"max": 32, "min": 25, "icon": "☀️"},
            {"max": 31, "min": 24, "icon": "🌤️"},
            {"max": 33, "min": 26, "icon": "⛅"},
            {"max": 30, "min": 25, "icon": "🌧️"},
            {"max": 32, "min": 26, "icon": "☀️"},
            {"max": 31, "min": 25, "icon": "🌤️"},
            {"max": 29, "min": 24, "icon": "☁️"}
        ]
        forecast_data = []
        for i in range(7):
            current_date = today + timedelta(days=i)
            forecast_data.append({
                "day": current_date.strftime("%a"),
                "temp_max": temp_ranges[i]["max"],
                "temp_min": temp_ranges[i]["min"],
                "icon": temp_ranges[i]["icon"]
            })
        return forecast_data
    
    forecast = get_7day_forecast()
    
    # Display weather forecast
    st.markdown("""
        <div class="weather-container">
            <div class="weather-title">🌤️ 7-Day Weather Forecast</div>
            <div class="forecast-scroll">
    """, unsafe_allow_html=True)
    
    for day in forecast:
        st.markdown(f"""
            <div class="forecast-day">
                <div class="day-label">{day['day']}</div>
                <div style="font-size: 2rem; margin: 0.5rem 0;">{day['icon']}</div>
                <div>
                    <span class="temp-high">{day['temp_max']}°</span> / 
                    <span class="temp-low">{day['temp_min']}°</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Feature cards
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <div class="feature-title">Detect Disease</div>
                <div class="feature-desc">Upload images of rice plants for AI-powered disease detection</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("START DETECTION", key="detect_button"):
            st.session_state.page = "detect"
            st.rerun()
    
    with col2:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">View History</div>
                <div class="feature-desc">Check your previous scans and detection results</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("VIEW HISTORY", key="history_button"):
            st.session_state.page = "history"
            st.rerun()
    
    # Did you know section
    st.markdown("""
        <div class="info-box">
            <div class="info-title">
                💡 Did You Know?
            </div>
            <div class="info-text">
                Early detection of rice diseases can increase your yield by up to 30%. 
                Regular monitoring and uploading images weekly helps protect your crops effectively.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    show_bottom_nav('home')

# ========== DETECTION SCREEN ==========
elif st.session_state.page == "detect":
    show_header()
    
    st.markdown("""
        <div class="modern-card">
            <h2 style="color: #2e7d32; text-align: center; margin-bottom: 0.5rem;">
                🔬 Disease Detection
            </h2>
            <p style="text-align: center; color: #5f6368;">
                Upload a rice leaf image for AI-powered analysis
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"], 
                                     label_visibility="collapsed")
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Detection button
        if st.button("🔍 DETECT DISEASE", key="detect_btn"):
            with st.spinner("🔄 Analyzing image with AI..."):
                try:
                    # Save image temporarily for AI processing
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        image.save(tmp_file, format="JPEG")
                        tmp_file_path = tmp_file.name
                    
                    # Call Roboflow AI for disease detection
                    client = init_client()
                    result = client.infer(tmp_file_path, model_id="palayprotector-project/1")
                    
                    # Display results
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.markdown("### 📋 Detection Results")
                    
                    if result.get("predictions"):
                        for pred in result["predictions"]:
                            disease = pred["class"]
                            confidence = pred["confidence"] * 100
                            
                            st.markdown(f"""
                                <div class="result-card disease-detected">
                                    <h3 style="color: #d32f2f; margin: 0;">⚠️ {disease}</h3>
                                    <p style="color: #5f6368;">Confidence Level</p>
                                    <div class="confidence-bar">
                                        <div class="confidence-fill" style="width: {confidence}%;"></div>
                                    </div>
                                    <p style="text-align: center; font-weight: 600; color: #2e7d32;">
                                        {confidence:.1f}%
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Save to history database
                            conn = sqlite3.connect("users.db")
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO history (user_id, result, confidence)
                                VALUES (?, ?, ?)
                            """, (st.session_state.user_id, disease, confidence))
                            conn.commit()
                            conn.close()
                    else:
                        # No disease detected
                        st.markdown("""
                            <div class="result-card">
                                <div style="text-align: center; padding: 2rem;">
                                    <div style="font-size: 4rem;">✅</div>
                                    <h3 style="color: #2e7d32;">Healthy Rice Plant</h3>
                                    <p style="color: #5f6368;">No diseases detected in this image</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Error during detection: {str(e)}")
    else:
        # Upload zone when no image
        st.markdown("""
            <div class="upload-zone">
                <div class="upload-icon">📤</div>
                <div class="upload-text">Upload Rice Leaf Image</div>
                <div class="upload-subtext">Supported: JPG, JPEG, PNG (Max 5MB)</div>
            </div>
        """, unsafe_allow_html=True)
    
    if st.button("← BACK TO HOME", key="detect_back_home"):
        st.session_state.page = "home"
        st.rerun()
    
    show_bottom_nav('detect')

# ========== HISTORY SCREEN ==========
elif st.session_state.page == "history":
    show_header()
    
    st.markdown("""
        <div class="modern-card">
            <h2 style="color: #2e7d32; text-align: center;">📊 Detection History</h2>
            <p style="text-align: center; color: #5f6368;">View your previous disease detection results</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_id is None:
        st.warning("⚠️ Please log in to view your history")
    else:
        # Fetch user's detection history from database
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT created_at, result, confidence
            FROM history
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (st.session_state.user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            # Display history in table format
            table_html = """
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>📅 Date</th>
                            <th>🦠 Disease</th>
                            <th>📊 Confidence</th>
                            <th>🔗 Action</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for date, disease, confidence in rows:
                try:
                    from datetime import datetime
                    d_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                    formatted_date = d_obj.strftime("%b %d, %Y")
                except:
                    formatted_date = date
                
                table_html += f"""
                    <tr>
                        <td>{formatted_date}</td>
                        <td><strong>{disease}</strong></td>
                        <td>{confidence:.1f}%</td>
                        <td>
                            <a href="https://example.com/remedy?disease={disease}" 
                               target="_blank" class="remedy-btn">
                                View Remedy
                            </a>
                        </td>
                    </tr>
                """
            
            table_html += """
                    </tbody>
                </table>
            """
            
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info("📭 No detection history yet. Start by detecting diseases!")
    
    show_bottom_nav('history')

# ========== DISEASE LIBRARY ==========
elif st.session_state.page == "library":
    show_header()
    
    st.markdown("""
        <div class="modern-card">
            <h2 style="color: #2e7d32; text-align: center;">📚 Rice Disease Library</h2>
            <p style="text-align: center; color: #5f6368;">Learn about common rice diseases and their treatments</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Search functionality
    search = st.text_input("🔍 Search diseases...", key="disease_search", 
                          placeholder="Type disease name...")
    
    # Disease database (can be expanded)
    diseases = [
        {
            "name": "Rice Blast",
            "scientific": "Pyricularia oryzae",
            "severity": "High",
            "symptoms": "Diamond-shaped lesions with gray centers and brown borders on leaves",
            "treatment": "Apply fungicides, use resistant varieties, improve field drainage"
        },
        {
            "name": "Bacterial Leaf Blight",
            "scientific": "Xanthomonas oryzae",
            "severity": "High",
            "symptoms": "Water-soaked lesions that turn yellow with wavy margins",
            "treatment": "Use resistant varieties, apply copper-based bactericides, avoid excessive nitrogen"
        },
        {
            "name": "Brown Spot",
            "scientific": "Bipolaris oryzae",
            "severity": "Medium",
            "symptoms": "Circular brown spots with gray centers on leaves and grains",
            "treatment": "Apply fungicides, improve soil fertility, use certified seeds"
        },
        {
            "name": "Sheath Blight",
            "scientific": "Rhizoctonia solani",
            "severity": "High",
            "symptoms": "Oval or irregular greenish-gray lesions on leaf sheaths",
            "treatment": "Apply fungicides, reduce plant density, improve air circulation"
        },
        {
            "name": "Tungro Disease",
            "scientific": "Rice tungro virus",
            "severity": "High",
            "symptoms": "Yellow or orange-yellow discoloration of leaves, stunted growth",
            "treatment": "Control vector leafhoppers, use resistant varieties, remove infected plants"
        }
    ]
    
    # Display disease cards
    for disease in diseases:
        if search.lower() in disease['name'].lower() or search == "":
            severity_color = "#d32f2f" if disease['severity'] == "High" else "#ff9800"
            
            st.markdown(f"""
                <div class="modern-card">
                    <h3 style="color: #2e7d32; margin-bottom: 0.5rem;">
                        🦠 {disease['name']}
                    </h3>
                    <p style="color: #5f6368; font-style: italic; margin-bottom: 1rem;">
                        {disease['scientific']}
                    </p>
                    <div style="background: {severity_color}; color: white; 
                                padding: 0.3rem 0.8rem; border-radius: 20px; 
                                display: inline-block; font-size: 0.85rem; font-weight: 600;">
                        Severity: {disease['severity']}
                    </div>
                    <div style="margin-top: 1rem;">
                        <p><strong>Symptoms:</strong> {disease['symptoms']}</p>
                        <p><strong>Treatment:</strong> {disease['treatment']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    show_bottom_nav('library')

# ========== PROFILE PAGE ==========
elif st.session_state.page == "profile":
    show_header()

    st.markdown("""
        <style>
        .profile-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        .profile-card {
            background: linear-gradient(145deg, #f0fdf4, #ffffff);
            border: 1px solid #c8e6c9;
            border-radius: 20px;
            padding: 30px;
            width: 90%;
            max-width: 450px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            margin-bottom: 25px;
        }
        .avatar {
            font-size: 70px;
            margin-bottom: 12px;
        }
        .username {
            font-weight: 700;
            font-size: 22px;
            color: #1b5e20;
            margin-bottom: 5px;
        }
        .email {
            color: #6c757d;
            font-size: 15px;
        }
        .metrics-card {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        .metric-box {
            background: #e8f5e9;
            border-radius: 15px;
            padding: 10px 20px;
            text-align: center;
            min-width: 100px;
        }
        .metric-value {
            font-size: 22px;
            font-weight: bold;
            color: #1b5e20;
        }
        .metric-label {
            font-size: 13px;
            color: #4e5d52;
        }
        .action-btn {
            width: 90%;
            background: linear-gradient(135deg, #4CAF50, #2e7d32);
            color: white;
            border: none;
            border-radius: 15px;
            padding: 12px;
            font-size: 16px;
            margin: 8px 0;
            transition: 0.3s;
        }
        .action-btn:hover {
            background: linear-gradient(135deg, #66bb6a, #388e3c);
        }
        </style>
    """, unsafe_allow_html=True)

    # Profile header
    st.markdown("<h2 style='text-align: center; color: #1b5e20;'>👤 Profile</h2>", unsafe_allow_html=True)

    # Profile info
    st.markdown(f"""
        <div class='profile-container'>
            <div class='profile-card'>
                <div class='avatar'>🧑‍🌾</div>
                <div class='username'>{st.session_state.logged_user}</div>
                <div class='email'>farmer@palayprotector.com</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Metrics
    st.markdown("""
        <div class='metrics-card'>
            <div class='metric-box'>
                <div class='metric-value'>127</div>
                <div class='metric-label'>Total Scans</div>
            </div>
            <div class='metric-box'>
                <div class='metric-value'>89</div>
                <div class='metric-label'>Healthy</div>
            </div>
            <div class='metric-box'>
                <div class='metric-value'>12</div>
                <div class='metric-label'>Detected</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Action buttons
    if st.button("⚙️ Settings", key="settings_btn", use_container_width=True):
        st.info("Settings coming soon")

    if st.button("🔒 Privacy", key="privacy_btn", use_container_width=True):
        st.info("Privacy settings coming soon")

    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        st.session_state.page = "login"
        st.session_state.user_id = None
        st.session_state.logged_user = None
        st.rerun()

    show_bottom_nav('profile')

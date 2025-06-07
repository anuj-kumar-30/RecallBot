import streamlit as st
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RecallBot - AI Memory Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        font-size: 1.2rem;
        color: #64748b;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    
    /* Status indicators */
    .status-success {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .status-error {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #dc2626;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .status-info {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #0369a1;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 1rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Message styling */
    .user-message {
        background: #3b82f6;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 1rem 1rem 0.25rem 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        word-wrap: break-word;
    }
    
    .bot-message {
        background: #f1f5f9;
        color: #1e293b;
        padding: 0.75rem 1rem;
        border-radius: 1rem 1rem 1rem 0.25rem;
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
    }
    
    /* Stats styling */
    .stats-container {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stat-item {
        display: flex;
        justify-content: space-between;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }
    
    /* Hide Streamlit elements */
    .stDeployButton {
        display: none;
    }
    
    #MainMenu {
        visibility: hidden;
    }
    
    .stFooter {
        display: none;
    }
    
    /* Custom button styling */
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'user_sessions' not in st.session_state:
        st.session_state.user_sessions = {}
    if 'ai_client' not in st.session_state:
        st.session_state.ai_client = None
    if 'mem_client' not in st.session_state:
        st.session_state.mem_client = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_user_id' not in st.session_state:
        st.session_state.current_user_id = None
    if 'session_initialized' not in st.session_state:
        st.session_state.session_initialized = False

def initialize_clients(mem_api_key, google_api_key):
    """Initialize AI clients with provided API keys"""
    try:
        from openai import OpenAI
        from mem0 import MemoryClient
        
        st.session_state.mem_client = MemoryClient(api_key=mem_api_key)
        st.session_state.ai_client = OpenAI(
            api_key=google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        return True, "Successfully connected to AI services!"
    except Exception as e:
        return False, f"Error connecting to services: {str(e)}"

def create_user_id(username, custom_user_id=None):
    """Create user ID based on username or custom ID"""
    if custom_user_id and custom_user_id.strip():
        return custom_user_id.strip().lower().replace(" ", "_")
    else:
        return username.strip().lower().replace(" ", "_")

def setup_user_session(username, user_id):
    """Set up user session"""
    system_prompt = "You are a helpful and polite assistant with memory capabilities."
    st.session_state.user_sessions[user_id] = {
        'name': username,
        'messages': [{'role': 'system', 'content': system_prompt}],
        'processed_memories': set(),
    }
    st.session_state.current_user_id = user_id
    st.session_state.session_initialized = True

def chat_with_bot(message, user_id):
    """Main chat function"""
    if not user_id or user_id not in st.session_state.user_sessions:
        return "Please complete setup first!"
    
    if not message or not message.strip():
        return "Please enter a message!"
    
    if not st.session_state.ai_client or not st.session_state.mem_client:
        return "AI services not connected!"
    
    session = st.session_state.user_sessions[user_id]
    
    try:
        # Search for relevant memories
        with st.spinner("Searching memories..."):
            relevant_mem = st.session_state.mem_client.search(message, user_id=user_id)
        
        # Prepare messages for AI
        current_messages = session['messages'].copy()
        
        if relevant_mem:
            # Add new memories
            for mem in relevant_mem:
                if mem['memory'] not in session['processed_memories']:
                    current_messages.append({'role': 'user', 'content': mem['memory']})
                    session['processed_memories'].add(mem['memory'])
        
        # Add current user input
        current_messages.append({'role': 'user', 'content': message})
        
        # Generate AI response
        with st.spinner("Generating response..."):
            stream = st.session_state.ai_client.chat.completions.create(
                model='gemini-2.0-flash',
                messages=current_messages,
            )
        
        ai_response = stream.choices[0].message.content
        
        # Update session messages
        session['messages'].append({'role': 'user', 'content': message})
        session['messages'].append({'role': 'assistant', 'content': ai_response})
        
        # Save to memory
        try:
            with st.spinner("Saving to memory..."):
                st.session_state.mem_client.add(user_id=user_id, messages=current_messages)
        except Exception as e:
            st.warning(f"Response generated but memory save failed: {str(e)}")
        
        return ai_response
        
    except Exception as e:
        return f"Error: {str(e)}"

def get_user_stats(user_id):
    """Get user statistics"""
    if not user_id or user_id not in st.session_state.user_sessions:
        return None
    
    session = st.session_state.user_sessions[user_id]
    return {
        'name': session['name'],
        'messages': len(session['messages']) - 1,  # Exclude system message
        'memories': len(session['processed_memories']),
        'user_id': user_id
    }

# Initialize session state
initialize_session_state()

# Sidebar Configuration
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h2>🧠 RecallBot Setup</h2>
        <p>Configure your AI assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Keys Section
    st.subheader("🔑 API Configuration")
    
    # Get API keys with fallback to environment variables
    mem_api_key = st.text_input(
        "Mem0 API Key *",
        type="password",
        value=os.environ.get('MEMO_API_KEY', ''),
        help="Required: Your Mem0 API key for memory functionality"
    )
    
    google_api_key = st.text_input(
        "Google API Key *",
        type="password", 
        value=os.environ.get('GOOGLE_API_KEY', ''),
        help="Required: Your Google API key for AI responses"
    )
    
    st.markdown("---")
    
    # User Information Section
    st.subheader("👤 User Information")
    
    username = st.text_input(
        "Your Name *",
        placeholder="Enter your name",
        help="Required: Used for personalization"
    )
    
    custom_user_id = st.text_input(
        "Custom User ID (Optional)",
        placeholder="Leave empty for auto-generation",
        help="Optional: Custom identifier for your session"
    )
    
    # Session Management
    st.markdown("---")
    
    # Initialize Session Button
    if st.button("🚀 Initialize Session", type="primary"):
        # Validation
        if not mem_api_key or not mem_api_key.strip():
            st.error("Mem0 API Key is required!")
        elif not google_api_key or not google_api_key.strip():
            st.error("Google API Key is required!")
        elif not username or not username.strip():
            st.error("Name is required!")
        else:
            # Initialize clients
            success, message = initialize_clients(mem_api_key, google_api_key)
            if success:
                # Create user ID and setup session
                user_id = create_user_id(username, custom_user_id)
                setup_user_session(username, user_id)
                st.success(f"✅ {message}")
                st.success(f"Session active for {username} (ID: {user_id})")
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    # Session Status
    if st.session_state.session_initialized:
        st.markdown('<div class="status-success">✅ Session Active</div>', unsafe_allow_html=True)
        
        # User Statistics
        stats = get_user_stats(st.session_state.current_user_id)
        if stats:
            st.markdown("### 📊 Session Statistics")
            st.markdown(f"""
            <div class="stats-container">
                <div class="stat-item"><span>User:</span><span>{stats['name']}</span></div>
                <div class="stat-item"><span>Messages:</span><span>{stats['messages']}</span></div>
                <div class="stat-item"><span>Memories:</span><span>{stats['memories']}</span></div>
                <div class="stat-item"><span>Session ID:</span><span>{stats['user_id']}</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear Chat Button
        if st.button("🔄 Clear Chat History"):
            st.session_state.chat_history = []
            if st.session_state.current_user_id in st.session_state.user_sessions:
                st.session_state.user_sessions[st.session_state.current_user_id]['messages'] = [
                    {'role': 'system', 'content': "You are a helpful and polite assistant with memory capabilities."}
                ]
                st.session_state.user_sessions[st.session_state.current_user_id]['processed_memories'] = set()
            st.success("Chat history cleared!")
            st.rerun()
    else:
        st.markdown('<div class="status-info">ℹ️ Please initialize your session</div>', unsafe_allow_html=True)

# Main Content Area
st.markdown("""
<div class="main-header">
    <h1>RecallBot</h1>
    <p>Your AI-powered memory assistant</p>
</div>
""", unsafe_allow_html=True)

# Chat Interface
if st.session_state.session_initialized:
    # Chat History Display
    chat_container = st.container()
    
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        if st.session_state.chat_history:
            for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
                # User message
                st.markdown(f'<div class="user-message">👤 {user_msg}</div>', unsafe_allow_html=True)
                # Bot message
                st.markdown(f'<div class="bot-message">🤖 {bot_msg}</div>', unsafe_allow_html=True)
        else:
            st.info("💬 Start a conversation! Your messages will appear here.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Message Input
    st.markdown("---")
    
    # Create columns for input and button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_message = st.text_input(
            "Type your message:",
            placeholder="Ask me anything...",
            label_visibility="collapsed",
            key="message_input"
        )
    
    with col2:
        send_button = st.button("📤 Send", type="primary")
    
    # Handle message sending
    if send_button or (user_message and st.session_state.get('last_message') != user_message):
        if user_message and user_message.strip():
            # Update last message to prevent duplicate processing
            st.session_state.last_message = user_message
            
            # Get bot response
            bot_response = chat_with_bot(user_message, st.session_state.current_user_id)
            
            # Add to chat history
            st.session_state.chat_history.append((user_message, bot_response))
            
            # Clear the input and rerun to show new message
            st.rerun()
        else:
            st.warning("Please enter a message!")

else:
    # Welcome message when not initialized
    st.markdown("""
    <div class="chat-container">
        <div style="text-align: center; padding: 3rem;">
            <h3>Welcome to RecallBot! 🎉</h3>
            <p>To get started:</p>
            <ol style="text-align: left; display: inline-block;">
                <li>Enter your API keys in the sidebar</li>
                <li>Provide your name</li>
                <li>Optionally set a custom user ID</li>
                <li>Click "Initialize Session"</li>
            </ol>
            <p><em>Your AI assistant with memory is waiting for you!</em></p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem; padding: 1rem;">
    <p>🔒 Your conversations are securely stored with personalized memory</p>
    <p>💡 <strong>Tip:</strong> The more you chat, the better RecallBot remembers your context!</p>
</div>
""", unsafe_allow_html=True)
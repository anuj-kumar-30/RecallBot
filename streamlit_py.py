import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from mem0 import MemoryClient
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="RecallBot - AI Memory Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .user-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-left-color: #667eea;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
        border-left-color: #28a745;
    }
    
    .memory-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffc107;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.messages = []
    st.session_state.processed_memories = set()
    st.session_state.user_name = ""
    st.session_state.user_id = ""
    st.session_state.mem_client = None
    st.session_state.ai_client = None

def initialize_clients():
    """Initialize API clients"""
    try:
        load_dotenv()
        mem_api_key = os.getenv('MEMO_API_KEY')
        google_api_key = os.getenv('GOOGLE_API_KEY')
        
        if not mem_api_key or not google_api_key:
            st.error("❌ API keys not found. Please check your .env file.")
            return False
        
        mem_client = MemoryClient(api_key=mem_api_key)
        ai_client = OpenAI(
            api_key=google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        st.session_state.mem_client = mem_client
        st.session_state.ai_client = ai_client
        return True
    except Exception as e:
        st.error(f"❌ Error initializing clients: {e}")
        return False

# Header
st.markdown("""
<div class="main-header">
    <h1>🧠 RecallBot</h1>
    <p>Your AI Memory Assistant - Powered by Advanced Memory Technology</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for user setup and stats
with st.sidebar:
    st.header("🔧 Setup")
    
    if not st.session_state.initialized:
        st.info("👤 Enter your name to get started")
        user_name = st.text_input("Your Name:", placeholder="Enter your full name")
        
        if user_name and st.button("🚀 Initialize RecallBot"):
            if initialize_clients():
                st.session_state.user_name = user_name
                st.session_state.user_id = user_name.replace(" ", "_").strip().lower()
                st.session_state.initialized = True
                st.session_state.messages = [
                    {'role': 'system', 'content': 'You are very polite and helpful assistant.'}
                ]
                st.success(f"✅ Welcome, {user_name}!")
                st.rerun()
    else:
        st.success(f"👤 **User:** {st.session_state.user_name}")
        st.info(f"🆔 **ID:** {st.session_state.user_id}")
        
        # Stats section
        st.header("📊 Session Stats")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{len(st.session_state.messages) - 1}</h3>
                <p>Messages</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{len(st.session_state.processed_memories)}</h3>
                <p>Memories</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = [
                {'role': 'system', 'content': 'You are very polite and helpful assistant.'}
            ]
            st.rerun()
        
        # Reset button
        if st.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Main chat interface
if st.session_state.initialized:
    # Chat container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for i, message in enumerate(st.session_state.messages[1:], 1):  # Skip system message
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            elif message['role'] == 'assistant':
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 RecallBot:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
    
    # Input section
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "💭 Your message:",
            placeholder="Type your message here...",
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 Send", use_container_width=True)
    
    # Process user input
    if send_button and user_input.strip():
        with st.spinner("🔍 Searching memories and generating response..."):
            try:
                # Search for relevant memories
                relevant_mem = st.session_state.mem_client.search(
                    user_input, 
                    user_id=st.session_state.user_id
                )
                
                # Display found memories
                if relevant_mem:
                    with st.expander(f"📚 Found {len(relevant_mem)} relevant memories"):
                        for mem in relevant_mem:
                            st.markdown(f"""
                            <div class="memory-card">
                                💡 {mem['memory']}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Add new memories to context
                    for mem in relevant_mem:
                        if mem['memory'] not in st.session_state.processed_memories:
                            st.session_state.messages.append({
                                'role': 'user', 
                                'content': mem['memory']
                            })
                            st.session_state.processed_memories.add(mem['memory'])
                
                # Add current user input
                st.session_state.messages.append({
                    'role': 'user', 
                    'content': user_input
                })
                
                # Generate AI response
                stream = st.session_state.ai_client.chat.completions.create(
                    model='gemini-2.0-flash',
                    messages=st.session_state.messages,
                )
                
                ai_response = stream.choices[0].message.content
                
                # Add AI response to messages
                st.session_state.messages.append({
                    'role': 'assistant', 
                    'content': ai_response
                })
                
                # Save to memory
                st.session_state.mem_client.add(
                    user_id=st.session_state.user_id, 
                    messages=st.session_state.messages
                )
                
                st.success("✅ Response generated and saved to memory!")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        # Rerun to update the interface
        st.rerun()

else:
    # Welcome screen
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>🌟 Welcome to RecallBot!</h2>
        <p style="font-size: 1.2rem; color: #666;">
            Your intelligent AI assistant with perfect memory. 
            RecallBot remembers your conversations and provides contextual responses.
        </p>
        <br>
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
            <h3>✨ Features</h3>
            <ul style="text-align: left; max-width: 600px; margin: 0 auto;">
                <li>🧠 <strong>Persistent Memory:</strong> Remembers all your conversations</li>
                <li>🔍 <strong>Smart Search:</strong> Finds relevant past conversations</li>
                <li>🤖 <strong>AI-Powered:</strong> Uses advanced language models</li>
                <li>👤 <strong>Personalized:</strong> Tailored responses based on your history</li>
            </ul>
        </div>
        <p><strong>👈 Enter your name in the sidebar to get started!</strong></p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🚀 Powered by Mem0, OpenAI API, and Streamlit | Built with ❤️</p>
</div>
""", unsafe_allow_html=True)
# Imports
import os
from dotenv import load_dotenv
from openai import OpenAI
from mem0 import MemoryClient
import time

# load .env 
load_dotenv()
try: 
    mem_api_key = os.getenv('MEMO_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')
except Exception as e:
    print(f"❌ Error: {e}")

# Creating client for both openai and memory
try:
    mem_client = MemoryClient(api_key=mem_api_key)
    ai_client = OpenAI(
        api_key=google_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    print("✅ Successfully connected to AI services!")
except Exception as e:
    print(f"❌ Error: {e}")

# System Context for our model
system_prompt = "You are very polite and helpful assistant."
message = [
    {'role':'system', 'content':system_prompt}
]

# Keep track of processed memories to avoid duplicates
processed_memories = set()

print("\n🤖 Welcome to RecallBot - Your AI Memory Assistant!")
print("=" * 50)
user_name = input("👤 Please enter your name: ")
user_id = user_name.replace(" ","_").strip().lower()
print(f"👋 Hello, {user_name}! Your user ID is: {user_id}")
print("\n💡 Type 'quit', 'q', or 'exit' to end the conversation")
print("=" * 50)

# CLI chatbot 
while True:
    user_input = input("\n💭 You: ")
    if user_input.lower() in ['quit', 'q', 'exit']:
        print("\n👋 Thank you for using RecallBot! Goodbye!")
        break
    
    print("🔍 Searching for relevant memories...")
    # finding relevant memories
    relevant_mem = mem_client.search(user_input, user_id=user_id)
    
    if relevant_mem:
        print(f"📚 Found {len(relevant_mem)} relevant memories!")
        # Only add new memories that haven't been processed before
        for mem in relevant_mem:
            if mem['memory'] not in processed_memories:
                message.append({'role':'user', 'content':mem['memory']})
                processed_memories.add(mem['memory'])
    else:
        print("📝 No relevant memories found.")
    
    # Add current user input
    message.append({'role':'user', "content": user_input})
    print("🤔 Thinking...")
    stream = ai_client.chat.completions.create(
        model='gemini-2.0-flash',
        messages=message,
    )
    print(f"\n🤖 AI: {stream.choices[0].message.content}")
    message.append({'role':'assistant', 'content':stream.choices[0].message.content})
    
    print("💾 Saving conversation to memory...")
    try:
        mem_client.add(user_id=user_id, messages=message)
        print("✅ Memory added successfully!")
    except Exception as e:
        print(f"❌ Error saving memory: {e}")
    
    # Add a small delay for better readability
    time.sleep(0.5)
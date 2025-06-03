import os
import getpass
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def initialize_groq_llm():
    """Initialize GROQ LLM with error handling"""
    
    # Check if langchain_groq is installed
    try:
        from langchain_groq import ChatGroq
    except ImportError as e:
        print("❌ langchain_groq not installed. Run: uv pip install langchain-groq")
        return None
    
    # Get API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️  GROQ_API_KEY not found in environment variables")
        api_key = getpass.getpass("Enter your GROQ_API_KEY: ")
        if not api_key:
            print("❌ No API key provided")
            return None
    
    # Validate API key format
    if not api_key.startswith("gsk_"):
        print("⚠️  Warning: API key should start with 'gsk_'")
    
    # Try different models in order of preference
    models_to_try = [
        "llama3-8b-8192", 
        "llama3-70b-8192",
        "gemma-7b-it",
    ]
    
    for model in models_to_try:
        try:
            print(f"🧪 Trying model: {model}")
            
            llm = ChatGroq(
                model=model,
                temperature=0,
                max_tokens=None,
                timeout=60,
                max_retries=3,
                groq_api_key=api_key  # Explicitly pass API key
            )
            
            # Test with a simple message
            test_response = llm.invoke("Hi")
            print(f"✅ Success! Using model: {model}")
            return llm
            
        except Exception as e:
            print(f"❌ Failed with {model}: {str(e)}")
            continue
    
    print("❌ All models failed. Please check your API key and try again.")
    return None

# Initialize the LLM at module level so it can be imported
llm = initialize_groq_llm()

# Test when run as main
if __name__ == "__main__":
    if llm:
        print("\n🎉 LLM is ready to use!")
        
        # Optional: Test with a question
        try:
            response = llm.invoke("What is 2+2?")
            print(f"Test response: {response.content}")
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        print("\n❌ Failed to initialize LLM")
        sys.exit(1)
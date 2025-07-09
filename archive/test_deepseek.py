from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_deepseek():
    try:
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            logger.error("No DeepSeek API key found in environment variables")
            return
            
        logger.info("Creating OpenAI client...")
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        logger.info("Sending test request...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Say hello!"}
            ],
            temperature=0.7,
            max_tokens=100,  # Reduced for testing
            top_p=0.9,
            stream=False
        )
        
        logger.info("Response received!")
        content = response.choices[0].message.content
        logger.info(f"Response content: {content}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_deepseek()

from openai import OpenAI
import os
import logging
import json
from datetime import datetime

# Configure logging
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(
    log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log"
)

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Simple cache configuration
cache_file = "llm_cache.json"


# Function to estimate token count (rough estimate: ~4 chars = 1 token)
def estimate_tokens(text):
    """
    Estimate the number of tokens in a text string.
    This is a rough approximation based on the GPT tokenizer behavior.
    
    Args:
        text (str): Text to estimate token count for
        
    Returns:
        int: Estimated token count
    """
    # Simple estimation: ~4 characters per token
    return len(text) // 4


# By default, we use OpenAI GPT-4
def call_llm(prompt: str, use_cache: bool = True) -> str:
    # Log the prompt
    logger.info(f"PROMPT: {prompt}")
    
    # Estimate token count
    token_estimate = estimate_tokens(prompt)
    logger.info(f"Estimated token count: {token_estimate}")

    # Check cache if enabled
    if use_cache:
        # Load cache from disk
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")

        # Return from cache if exists
        if prompt in cache:
            logger.info(f"RESPONSE: {cache[prompt]}")
            return cache[prompt]

    # Call the OpenAI API if not in cache or cache disabled
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = response.choices[0].message.content

    # Log the response
    logger.info(f"RESPONSE: {response_text}")

    # Update cache if enabled
    if use_cache:
        # Load cache again to avoid overwrites
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")

        # Add to cache and save
        cache[prompt] = response_text
        try:
            with open(cache_file, "w") as f:
                json.dump(cache, f)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    return response_text


# # Google Gemini implementation (commented out)
# def call_llm_gemini(prompt: str, use_cache: bool = True) -> str:
#     from google import genai
#     # Log the prompt
#     logger.info(f"PROMPT: {prompt}")
#
#     # Check cache if enabled
#     if use_cache:
#         # Load cache from disk
#         cache = {}
#         if os.path.exists(cache_file):
#             try:
#                 with open(cache_file, "r") as f:
#                     cache = json.load(f)
#             except:
#                 logger.warning("Failed to load cache, starting with empty cache")
#
#         # Return from cache if exists
#         if prompt in cache:
#             logger.info(f"RESPONSE: {cache[prompt]}")
#             return cache[prompt]
#
#     client = genai.Client(
#         api_key=os.getenv("GEMINI_API_KEY", ""),
#     )
#     model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro-exp-03-25")
#     
#     response = client.models.generate_content(model=model, contents=[prompt])
#     response_text = response.text
#
#     # Log the response
#     logger.info(f"RESPONSE: {response_text}")
#
#     # Update cache if enabled
#     if use_cache:
#         # Load cache again to avoid overwrites
#         cache = {}
#         if os.path.exists(cache_file):
#             try:
#                 with open(cache_file, "r") as f:
#                     cache = json.load(f)
#             except:
#                 pass
#
#         # Add to cache and save
#         cache[prompt] = response_text
#         try:
#             with open(cache_file, "w") as f:
#                 json.dump(cache, f)
#         except Exception as e:
#             logger.error(f"Failed to save cache: {e}")
#
#     return response_text


# # Use Anthropic Claude 3.7 Sonnet Extended Thinking
# def call_llm_claude(prompt, use_cache: bool = True):
#     from anthropic import Anthropic
#     client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "your-api-key"))
#     response = client.messages.create(
#         model="claude-3-7-sonnet-20250219",
#         max_tokens=21000,
#         thinking={
#             "type": "enabled",
#             "budget_tokens": 20000
#         },
#         messages=[
#             {"role": "user", "content": prompt}
#         ]
#     )
#     return response.content[1].text

# # Use OpenRouter API
# def call_llm_openrouter(prompt: str, use_cache: bool = True) -> str:
#     import requests
#     # Log the prompt
#     logger.info(f"PROMPT: {prompt}")
#
#     # Check cache if enabled
#     if use_cache:
#         # Load cache from disk
#         cache = {}
#         if os.path.exists(cache_file):
#             try:
#                 with open(cache_file, "r") as f:
#                     cache = json.load(f)
#             except:
#                 logger.warning(f"Failed to load cache, starting with empty cache")
#
#         # Return from cache if exists
#         if prompt in cache:
#             logger.info(f"RESPONSE: {cache[prompt]}")
#             return cache[prompt]
#
#     # OpenRouter API configuration
#     api_key = os.getenv("OPENROUTER_API_KEY", "")
#     model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
#     
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#     }
#
#     data = {
#         "model": model,
#         "messages": [{"role": "user", "content": prompt}]
#     }
#
#     response = requests.post(
#         "https://openrouter.ai/api/v1/chat/completions",
#         headers=headers,
#         json=data
#     )
#
#     if response.status_code != 200:
#         error_msg = f"OpenRouter API call failed with status {response.status_code}: {response.text}"
#         logger.error(error_msg)
#         raise Exception(error_msg)
#     try:
#         response_text = response.json()["choices"][0]["message"]["content"]
#     except Exception as e:
#         error_msg = f"Failed to parse OpenRouter response: {e}; Response: {response.text}"
#         logger.error(error_msg)        
#         raise Exception(error_msg)
#     
#
#     # Log the response
#     logger.info(f"RESPONSE: {response_text}")
#
#     # Update cache if enabled
#     if use_cache:
#         # Load cache again to avoid overwrites
#         cache = {}
#         if os.path.exists(cache_file):
#             try:
#                 with open(cache_file, "r") as f:
#                     cache = json.load(f)
#             except:
#                 pass
#
#         # Add to cache and save
#         cache[prompt] = response_text
#         try:
#             with open(cache_file, "w") as f:
#                 json.dump(cache, f)
#         except Exception as e:
#             logger.error(f"Failed to save cache: {e}")
#
#     return response_text

if __name__ == "__main__":
    test_prompt = "Hello, how are you?"

    # First call - should hit the API
    print("Making call...")
    response1 = call_llm(test_prompt, use_cache=False)
    print(f"Response: {response1}")

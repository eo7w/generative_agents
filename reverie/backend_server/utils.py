import openai
import time
from openai import OpenAI

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)

key_owner = "User"
debug = False

maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"
fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/storage/temp"

def ChatGPT_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=300):
    """
    إرسال الطلبات مع نظام حماية وتأخير لتجنب خطأ 429 (Too Many Requests)
    """
    for i in range(6):
        try:
            completion = client.chat.completions.create(
              model=model,
              messages=[{"role": "user", "content": prompt}],
              temperature=temperature,
              max_tokens=max_tokens,
              top_p=1,
              stream=False
            )
            # تأخير بسيط جداً بين كل طلب وآخر لعدم الضغط على السيرفر
            time.sleep(1.5)
            return completion.choices[0].message.content
        except Exception as e:
            print(f"NVIDIA NIM API Error / Rate Limit (attempt {i}): {e}")
            # انتظار تصاعدي يتضاعف مع كل محاولة فاشلة
            sleep_time = (i + 1) * 4
            print(f"Waiting {sleep_time} seconds before retrying...")
            time.sleep(sleep_time)
            
    return ""

def GPT4_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=500):
    """
    الدالة البديلة لطلبات GPT-4
    """
    return ChatGPT_request(prompt, model=model, temperature=temperature, max_tokens=max_tokens)

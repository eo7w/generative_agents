import openai
import time
from openai import OpenAI

# إعداد عميل OpenAI ليعمل عبر NVIDIA NIM
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

def ChatGPT_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=500):
    """
    إرسال طلبات التفكير والحوار للشخصيات عبر NVIDIA NIM
    """
    for i in range(5):
        try:
            completion = client.chat.completions.create(
              model=model,
              messages=[{"role": "user", "content": prompt}],
              temperature=temperature,
              max_tokens=max_tokens,
              top_p=1,
              stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"NVIDIA NIM API Error (attempt {i}): {e}")
            time.sleep(2)
    return ""

def GPT4_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=1000):
    """
    الدالة البديلة لطلبات GPT-4 المتقدمة تستخدم أيضاً قوة Llama 3 عبر NVIDIA
    """
    return ChatGPT_request(prompt, model=model, temperature=temperature, max_tokens=max_tokens)

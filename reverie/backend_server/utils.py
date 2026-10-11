import openai
import time
import threading
from openai import OpenAI

# مفاتيحك الثلاثة لتوزيع الحمل
api_keys = [
    "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",
    "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",
    "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"
]

clients = [
    OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=key
    )
    for key in api_keys
]

client_index = 0
lock = threading.Lock()
last_request_time = 0

key_owner = "User"
debug = False

maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"
fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/storage/temp"

def ChatGPT_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=200):
    """
    إرسال الطلبات بفاصل زمني 12 ثانية لكل طلب لتفادي تجاوز الحد المسموح نهائياً
    """
    global client_index, last_request_time
    
    for i in range(15):
        with lock:
            # فرض فاصل زمني 12 ثانية كحد أدنى بين كل طلب وآخر
            elapsed = time.time() - last_request_time
            if elapsed < 12.0:
                time.sleep(12.0 - elapsed)
            
            curr_idx = client_index
            client_index = (client_index + 1) % len(clients)
            client = clients[curr_idx]
            last_request_time = time.time()

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
            print(f"Rate limit / 429 hit (Attempt {i+1}/15). Cooling down for 60 seconds... Error: {e}")
            # في حال ظهر خطأ، ننتظر دقيقة كاملة لضمان تصفير العداد لدى المزود
            time.sleep(60)
            
    return ""

def GPT4_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=300):
    """
    الدالة البديلة لطلبات GPT
    """
    return ChatGPT_request(prompt, model=model, temperature=temperature, max_tokens=max_tokens)

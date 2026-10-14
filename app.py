import os
import logging
from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import pyotp

# প্রোফেশনাল লগিং কনফিগারেশন
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    req_data = request.json
    input_data = req_data.get('data', '')
    results = []
    
    if not input_data.strip():
        return jsonify({"results": ["Error: No account data provided."]})
    
    lines = input_data.strip().split("\n")
    
    try:
        with sync_playwright() as p:
            # সার্ভার এনভায়রনমেন্টের জন্য অপ্টিমাইজড ব্রাউজার লঞ্চ সেটিংস
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            for line in lines:
                if not line.strip() or "|" not in line:
                    continue
                
                parts = [p.strip() for p in line.split("|")]
                username = parts[0]
                password = parts[1]
                totp_key = parts[2] if len(parts) > 2 and parts[2] else None
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                try:
                    logging.info(f"Processing account: {username}")
                    page.goto("https://www.instagram.com/accounts/login/", timeout=60000)
                    page.wait_for_selector('input[name="username"]', timeout=15000)
                    
                    # ইউজারনেম ও পাসওয়ার্ড ইনপুট
                    page.fill('input[name="username"]', username)
                    page.fill('input[name="password"]', password)
                    page.click('button[type="submit"]')
                    
                    page.wait_for_timeout(6000)
                    
                    # টু-ফ্যাক্টর অথেন্টিকেশন (2FA) বা চেকপয়েন্ট চেক
                    if "two_factor" in page.url or page.locator('input[name="verificationCode"]').count() > 0:
                        if totp_key:
                            logging.info(f"2FA detected for {username}. Generating OTP code...")
                            totp = pyotp.TOTP(totp_key.replace(" ", ""))
                            otp_code = totp.now()
                            page.fill('input[name="verificationCode"]', otp_code)
                            page.click('button[type="button"]')
                            page.wait_for_timeout(6000)
                        else:
                            results.append(f"{username}|{password}|2FA Required (Key Missing)")
                            context.close()
                            continue

                    # সফল লগইনের পর কুকিজ সংগ্রহ
                    cookies = context.cookies()
                    session_id = ""
                    for cookie in cookies:
                        if cookie["name"] == "sessionid":
                            session_id = cookie["value"]
                            break
                    
                    if session_id:
                        results.append(f"{username}|{password}|sessionid={session_id}")
                        logging.info(f"Successfully extracted session for {username}")
                    else:
                        results.append(f"{username}|{password}|Login Failed / Checkpoint Required")
                        logging.warning(f"Session ID not found for {username}")
                        
                except PlaywrightTimeoutError:
                    results.append(f"{username}|{password}|Error: Timeout during login")
                    logging.error(f"Timeout error for {username}")
                except Exception as e:
                    results.append(f"{username}|{password}|Error: {str(e)}")
                    logging.error(f"Exception for {username}: {str(e)}")
                finally:
                    context.close()
                
            browser.close()
    except Exception as e:
        return jsonify({"results": [f"System Error: {str(e)}"]})
        
    return jsonify({"results": results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
                            

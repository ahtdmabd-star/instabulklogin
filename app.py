import os
from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
import pyotp

app = Flask(__name__)

@app.route('/')
index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    req_data = request.json
    input_data = req_data.get('data', '')
    results = []
    
    lines = input_data.strip().split("\n")
    
    try:
        with sync_playwright() as p:
            # ক্লাউড সার্ভারে চালানোর জন্য headless=True থাকা জরুরি
            browser = p.chromium.launch(headless=True)
            
            for line in lines:
                if not line.strip() or "|" not in line:
                    continue
                
                parts = [p.strip() for p in line.split("|")]
                username = parts[0]
                password = parts[1]
                totp_key = parts[2] if len(parts) > 2 and parts[2] else None
                
                context = browser.new_context()
                page = context.new_page()
                
                try:
                    page.goto("https://www.instagram.com/accounts/login/", timeout=60000)
                    page.wait_for_selector('input[name="username"]', timeout=10000)
                    
                    page.fill('input[name="username"]', username)
                    page.fill('input[name="password"]', password)
                    page.click('button[type="submit"]')
                    
                    page.wait_for_timeout(6000)
                    
                    # 2FA চেক
                    if "two_factor" in page.url or page.locator('input[name="verificationCode"]').count() > 0:
                        if totp_key:
                            totp = pyotp.TOTP(totp_key.replace(" ", ""))
                            otp_code = totp.now()
                            page.fill('input[name="verificationCode"]', otp_code)
                            page.click('button[type="button"]')
                            page.wait_for_timeout(6000)
                        else:
                            results.append(f"{username}|{password}|2FA Required (Key Missing)")
                            context.close()
                            continue

                    # কুকিজ সংগ্রহ
                    cookies = context.cookies()
                    session_id = ""
                    for cookie in cookies:
                        if cookie["name"] == "sessionid":
                            session_id = cookie["value"]
                            break
                    
                    if session_id:
                        results.append(f"{username}|{password}|sessionid={session_id}")
                    else:
                        results.append(f"{username}|{password}|Login Failed / Checkpoint")
                        
                except Exception as e:
                    results.append(f"{username}|{password}|Error: {str(e)}")
                
                context.close()
                
            browser.close()
    except Exception as e:
        return jsonify({"results": [f"System Error: {str(e)}"]})
        
    return jsonify({"results": results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

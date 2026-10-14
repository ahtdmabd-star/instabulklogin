import os
import time
import requests
import pyotp
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    req_data = request.json
    input_data = req_data.get('data', '')
    results = []
    
    lines = input_data.strip().split("\n")
    
    for line in lines:
        if not line.strip() or "|" not in line:
            continue
        
        parts = [p.strip() for p in line.split("|")]
        username = parts[0]
        password = parts[1]
        totp_key = parts[2] if len(parts) > 2 and parts[2] else None
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-IG-App-ID': '936619743392459',
            'Referer': 'https://www.instagram.com/accounts/login/'
        })
        
        try:
            # ইনস্টাগ্রাম হোম পেজে রিকোয়েস্ট পাঠানো
            resp = session.get('https://www.instagram.com/accounts/login/')
            csrftoken = session.cookies.get('csrftoken', '')
            
            session.headers.update({
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            current_time = int(time.time())
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{current_time}:{password}',
                'queryParams': '{}',
                'optIntoOneTap': 'false'
            }
            
            # 2FA বা সিকিউরিটি চেক হ্যান্ডেল করার জন্য
            if totp_key:
                totp = pyotp.TOTP(totp_key.replace(" ", ""))
                otp_code = totp.now()
                # ওটিপি ভেরিফিকেশন লজিক এখানে যুক্ত করা যেতে পারে
            
            # সেশন কুকি চেক করা
            session_id = session.cookies.get('sessionid', '')
            
            if session_id:
                results.append(f"{username}|{password}|sessionid={session_id}")
            else:
                results.append(f"{username}|{password}|Login Failed / Checkpoint Required")
                
        except Exception as e:
            results.append(f"{username}|{password}|Error: {str(e)}")
            
    return jsonify({"results": results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

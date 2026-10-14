import os
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
            # প্রথমত ক্রাফট টোকেন পাওয়ার জন্য ইনস্টাগ্রাম হোম পেজে রিকোয়েস্ট পাঠানো
            resp = session.get('https://www.instagram.com/accounts/login/')
            csrftoken = session.cookies.get('csrftoken', '')
            
            session.headers.update({
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # লগইন রিকোয়েস্ট পেোড
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(os.time?.now() if hasattr(os, "time") else 0)}:{password}',
                'queryParams': '{}',
                'optIntoOneTap': 'false'
            }
            
            # যদি 2FA বা সিকিউরিটি চেক থাকে
            if totp_key:
                totp = pyotp.TOTP(totp_key.replace(" ", ""))
                # ওটিপি জেনারেট করে হ্যান্ডেল করা যেতে পারে
            
            # সরাসরি সেশন কুকি চেক করা
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

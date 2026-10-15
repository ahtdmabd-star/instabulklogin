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
    
    if not input_data.strip():
        return jsonify({"results": ["Error: No data provided."]})
    
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
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'X-IG-App-ID': '936619743392459',
            'Referer': 'https://www.instagram.com/accounts/login/'
        })
        
        try:
            # ইনস্টাগ্রাম লগইন পেজ থেকে কুক্ষিগত টোকেন নেওয়া
            resp = session.get('https://www.instagram.com/accounts/login/')
            csrftoken = session.cookies.get('csrftoken', '')
            
            session.headers.update({
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # যদি টু-ফ্যাক্টর কি থাকে, তবে ওটিপি জেনারেট করা
            if totp_key:
                totp = pyotp.TOTP(totp_key.replace(" ", ""))
                otp_code = totp.now()
            
            # সরাসরি সেশন কুকি চেক করা
            session_id = session.cookies.get('sessionid', '')
            
            if session_id:
                results.append(f"{username}|{password}|sessionid={session_id}")
            else:
                results.append(f"{username}|{password}|Login Failed / Security Check")
                
        except Exception as e:
            results.append(f"{username}|{password}|Error: {str(e)}")
            
    return jsonify({"results": results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
        

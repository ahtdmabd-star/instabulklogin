import os
from flask import Flask, render_template, request, jsonify
from instagrapi import Client

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
        
        cl = Client()
        if totp_key:
            cl.verification_code = totp_key.replace(" ", "")
            
        try:
            # ইনস্টাগ্রামে লগইন করার চেষ্টা
            cl.login(username, password)
            
            # কুকিজ বা সেশন ডেটা সংগ্রহ করা
            settings = cl.get_settings()
            session_id = settings.get("authorization_data", {}).get("sessionid", "")
            
            if session_id:
                results.append(f"{username}|{password}|sessionid={session_id}")
            else:
                results.append(f"{username}|{password}|Login Successful but Session ID not found")
                
        except Exception as e:
            results.append(f"{username}|{password}|Error: {str(e)}")
            
    return jsonify({"results": results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

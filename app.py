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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/accounts/login/'
        })
        
        try:
            # ১. ইনস্টাগ্রাম লগইন পেজ থেকে CSRF টোকেন সংগ্রহ করা
            resp = session.get('https://www.instagram.com/accounts/login/')
            csrftoken = session.cookies.get('csrftoken', '')
            
            session.headers.update({
                'X-CSRFToken': csrftoken
            })
            
            # ২. ইনস্টাগ্রাম অফিশিয়াল পাসওয়ার্ড এনক্রিপশন ফরম্যাট তৈরি
            timestamp = int(time.time())
            enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}"
            
            payload = {
                'username': username,
                'enc_password': enc_password,
                'queryParams': '{}',
                'optIntoOneTap': 'false',
                'trustedDeviceRecords': '{}'
            }
            
            # ৩. লগইন রিকোয়েস্ট পাঠানো
            login_url = 'https://www.instagram.com/api/v1/web/accounts/login/ajax/'
            login_resp = session.post(login_url, data=payload)
            res_json = login_resp.json()
            
            if res_json.get('authenticated'):
                session_id = session.cookies.get('sessionid', '')
                if session_id:
                    results.append(f"{username}|{password}|sessionid={session_id}")
                else:
                    results.append(f"{username}|{password}|Login Failed / Cookie Not Found")
                    
            elif res_json.get('two_factor_required'):
                if totp_key:
                    tf_info = res_json.get('two_factor_info', {})
                    identifier = tf_info.get('two_factor_identifier')
                    
                    # ৪. 2FA সিকিউরিটি কি দিয়ে ওটিপি কোড জেনারেট করা
                    totp = pyotp.TOTP(totp_key.replace(" ", ""))
                    otp_code = totp.now()
                    
                    tf_payload = {
                        'username': username,
                        'verification_code': otp_code,
                        'identifier': identifier,
                        'queryParams': '{}'
                    }
                    
                    tf_url = 'https://www.instagram.com/api/v1/web/accounts/login/ajax/two_factor/'
                    tf_resp = session.post(tf_url, data=tf_payload)
                    tf_json = tf_resp.json()
                    
                    if tf_json.get('authenticated'):
                        session_id = session.cookies.get('sessionid', '')
                        if session_id:
                            results.append(f"{username}|{password}|sessionid={session_id}")
                        else:
                            results.append(f"{username}|{password}|2FA Passed but Cookie Missing")
                    else:
                        results.append(f"{username}|{password}|2FA Failed: Invalid OTP or Checkpoint")
                else:
                    results.append(f"{username}|{password}|2FA Required (Key Missing)")
            else:
                error_msg = res_json.get('message', 'Checkpoint / Restricted')
                results.append(f"{username}|{password}|Login Failed: {error_msg}")
                
        except Exception as e:
            results.append(f"{username}|{password}|Error: {str(e)}")
            
    return jsonify({"results": results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
                            

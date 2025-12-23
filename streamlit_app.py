import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import urllib3

# 1. HTTPS 보안 인증서 경고 및 연결 오류 해결
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GRVT 통합 모니터", layout="wide")

def get_grvt_data(api_key, api_secret, sub_id):
    """
    GRVT API 통신 함수
    """
    try:
        base_url = "https://api.grvt.io"
        path = f"/v1/accounts/{sub_id}/summary"
        timestamp = str(int(time.time() * 1000))
        
        # 보안 서명 생성
        message = timestamp + "GET" + path
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": timestamp,
            "grvt-signature": signature,
            "Accept": "application/json"
        }
        
        # verify=False를 통해 HTTPS 연결 실패 문제를 강제로 해결합니다.
        response = requests.get(
            base_url + path, 
            headers=headers, 
            timeout=10, 
            verify=False
        )
        
        if response.status_code == 200:
            raw = response.json()
            # 데이터가 'result' 키 내부에 있을 경우를 대비합니다.
            data = raw.get('result', raw)
            
            equity = float(data.get('total_equity', 0))
            margin = float(data.get('margin_usage_ratio', 0)) * 100
            
            return {"Equity": equity, "Margin": margin, "Status": "✅ 연결됨"}
        elif response.status_code in [401, 403]:
            return {"Equity": 0, "Margin": 0, "Status": "❌ 권한오류"}
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 서버에러({response.status_code})"}
            
    except Exception as e:
        # 에러 발생 시 종류를 표시합니다.
        return {"Equity": 0, "Margin": 0, "Status": f"❌ 연결불가({type(e).__name__[:5]})

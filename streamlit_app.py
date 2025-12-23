import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import urllib3

# 1. HTTPS 인증서 경고 무시 (로그에 뜬 HTTPSConne 에러 해결책)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GRVT 자산 모니터", layout="wide")

def get_grvt_data(api_key, api_secret, sub_id):
    try:
        base_url = "https://api.grvt.io"
        # 사용자님의 숫자형 sub_id가 포함된 경로
        path = f"/v1/accounts/{sub_id}/summary"
        timestamp = str(int(time.time() * 1000))
        
        # 2. 서명 생성 (메인넷 규격 준수)
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
        
        # 3. 데이터 요청 (인증서 검증 우회로 연결 성공률 극대화)
        response = requests.get(
            base_url + path, 
            headers=headers, 
            timeout=10, 
            verify=False
        )
        
        if response.status_code == 200:
            raw = response.json()
            # GRVT 응답 구조에서 'result' 키 유무에 상관없이 데이터를 가져옴
            data = raw.get('result', raw)
            
            equity = float(data.get('total_equity', 0))
            margin = float(data.get('margin_usage_ratio', 0)) * 100
            
            return {"Equity": equity, "Margin": margin, "Status": "✅ 연결됨"}
        
        elif response.status_code in [401, 403]:
            return {"Equity": 0, "Margin": 0, "Status": "❌ 키 권한오류"}
        else:
            return {"Equity": 0, "Margin": 0, "Status":

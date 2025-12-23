import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import urllib3

# SSL 인증 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GRVT Multi-Monitor", layout="wide")

def get_grvt_data(api_key, api_secret, sub_id):
    try:
        base_url = "https://api.grvt.io"
        # 숫자형 sub_id를 문자열로 변환하여 경로 생성
        path = f"/v1/accounts/{str(sub_id).strip()}/summary"
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
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 세션을 사용하여 연결 안정성 강화
        session = requests.Session()
        response = session.get(
            base_url + path, 
            headers=headers, 
            timeout=20, # 타임아웃을 20초로 연장
            verify=False
        )
        
        if response.status_code == 200:
            raw = response.json()
            data = raw.get('result', raw)
            return {
                "Equity": float(data.get('total_equity', 0)),
                "Margin": float(data.get('margin_usage_ratio', 0)) * 100,
                "Status": "✅ 연결됨"
            }
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
            
    except Exception as e:
        # 에러 발생 시 로그에 상세 원인 출력 (디버깅용)
        print(f"Error: {str(e)}")
        return {"Equity": 0, "Margin": 0, "Status": "❌ 접속불가"}

st.title("🛡️ GRVT Multi-Account Monitor")

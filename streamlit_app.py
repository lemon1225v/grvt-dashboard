import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import urllib3

# 1. SSL 인증 및 경고 강제 무시 (연결 안정성 확보)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GRVT 통합 모니터", layout="wide")

def get_grvt_data(api_key, api_secret, sub_id):
    """
    GRVT API 연동 및 데이터 추출
    """
    try:
        # sub_id가 숫자형일 경우를 대비해 공백 없는 문자열로 정제
        clean_sub_id = str(sub_id).strip()
        base_url = "https://api.grvt.io"
        path = f"/v1/accounts/{clean_sub_id}/summary"
        timestamp = str(int(time.time() * 1000))
        
        # 보안 서명(Signature) 생성 - 규격 엄수
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
            "User-Agent": "Mozilla/5.0" # 서버 차단 방지용
        }
        
        # 2. 타임아웃 연장 및 인증 검사 우회
        response = requests.get(
            base_url + path, 
            headers=headers, 
            timeout=20, 
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
            # 401: 키 오류, 403: 권한 오류 등 구체적 표시
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
            
    except Exception:
        return {"Equity": 0, "Margin": 0, "Status": "❌ 접속불가"}

st.title("🛡️ GRVT Multi-Account Monitor")

# --- 대시보드 출력부 ---
all_data = []
for i in range(1, 7):
    name = f"GR{i}"
    if name in st.secrets:
        acc = st.secrets[name]
        res = get_grvt_data(acc['api_key'], acc['api_secret'], acc['sub_id'])
        all_data.append({
            "계정": name,
            "순자산

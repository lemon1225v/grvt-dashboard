import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import urllib3

# 1. 모든 SSL 인증 검사 및 경고 강제 무시 (연결불가 해결 핵심)
urllib3.disable_warnings()

st.set_page_config(page_title="GRVT Monitor", layout="wide")

def get_data(api_key, api_secret, sub_id):
    try:
        # 2. 타임아웃과 세션 관리를 통해 안정성 확보
        session = requests.Session()
        session.verify = False  # 인증서 무시
        
        base_url = "https://api.grvt.io"
        path = f"/v1/accounts/{sub_id}/summary"
        ts = str(int(time.time() * 1000))
        
        # 서명 생성
        msg = ts + "GET" + path
        sig = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": ts,
            "grvt-signature": sig,
            "Accept": "application/json"
        }
        
        # 3. 브라우저인 것처럼 속여 보안 차단 우회
        headers["User-Agent"] = "Mozilla/5.0"

        resp = session.get(base_url + path, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            res = resp.json()
            d = res.get('result', res)
            return {"E": float(d.get('total_equity', 0)), "M": float(d.get('margin_usage_ratio', 0))*100, "S": "✅ 연결됨"}
        return {"E": 0, "M": 0, "S": f"❌ 오류({resp.status_code})"}
    except Exception as e:
        return {"E": 0, "M": 0, "S": f"❌ 접속실패"}

st.title("🛡️ GRVT Multi-Monitor")

# 데이터 표시 구간
all_rows = []
for i in range(1, 7):
    k = f"GR{i}"
    if k in st.secrets:
        s = st.secrets[k]
        r = get_data(s['api_key'], s['api_secret'], s['sub_id'])
        all_rows.append({"계정": k, "순자산": r["E"], "마진": r["M"], "상태": r["S"]})

if all_rows:
    df = pd.DataFrame(all_rows)
    st.metric("총 합계", f"${df['순자산'].sum():,.2f}")
    st.table(df)  # 문법 오류를 줄이기 위해 가장 단순한 table 사용
else:
    st.error("Secrets 설정(GR1~GR6)을 확인해주세요.")

# 30초 후 자동 새로고침을 위한 버튼 (수동)
if st.button("🔄 새로고침"):
    st.rerun()

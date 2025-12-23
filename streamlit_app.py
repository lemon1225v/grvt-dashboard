import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import urllib3

# 1. SSL 인증서 경고 무시 (HTTPS 연결불가 에러 방지)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GRVT Monitor", layout="wide")

def get_grvt_data(api_key, api_secret, sub_id):
    try:
        base_url = "https://api.grvt.io"
        path = f"/v1/accounts/{sub_id}/summary"
        timestamp = str(int(time.time() * 1000))
        
        # 2. 서명 생성 규격 준수
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
        
        # 3. verify=False로 접속 성공률 극대화
        response = requests.get(base_url + path, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            res_json = response.json()
            data = res_json.get('result', res_json)
            return {
                "Equity": float(data.get('total_equity', 0)),
                "Margin": float(data.get('margin_usage_ratio', 0)) * 100,
                "Status": "✅ 연결됨"
            }
        return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
    except Exception:
        return {"Equity": 0, "Margin": 0, "Status": "❌ 연결불가"}

# --- 화면 구성 ---
st.title("🛡️ GRVT Multi-Account Monitor")

if st.button("🔄 데이터 새로고침"):
    st.rerun()

# 30초마다 자동 갱신 구간
@st.fragment(run_every=30)
def show_dashboard():
    all_results = []
    for i in range(1, 7):
        name = f"GR{i}"
        if name in st.secrets:
            s = st.secrets[name]
            res = get_grvt_data(s['api_key'], s['api_secret'], s['sub_id'])
            all_results.append({
                "계정": name,
                "순자산(Equity)": res["Equity"],
                "마진비율(%)": res["Margin"],
                "상태": res["Status"],
                "시간": time.strftime("%H:%M:%S")
            })

    if all_results:
        df = pd.DataFrame(all_results)
        st.metric("총 합계 자산", f"${df['순자산(Equity)'].sum():,.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("Secrets 설정(GR1~GR6)을 확인해주세요.")

# 함수 실행 (이 줄까지 반드시 복사해야 합니다)
show_dashboard()

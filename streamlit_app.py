import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests

st.set_page_config(page_title="GRVT 실시간 모니터", layout="wide")

# --- 1. 데이터 불러오기 함수 (동일) ---
def get_real_grvt_balance(api_key, api_secret, sub_id):
    try:
        base_url = "https://api.grvt.io"
        timestamp = str(int(time.time() * 1000))
        message = timestamp + "GET" + f"/v1/accounts/{sub_id}/summary"
        signature = hmac.new(api_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        
        headers = {"GRVT-API-KEY": api_key, "GRVT-TIMESTAMP": timestamp, "GRVT-SIGNATURE": signature}
        response = requests.get(f"{base_url}/v1/accounts/{sub_id}/summary", headers=headers, timeout=5)
        
        if response.status_code == 200:
            res_data = response.json()
            return {"Equity": float(res_data.get('total_equity', 0)), "Margin": float(res_data.get('margin_usage_ratio', 0)) * 100, "Status": "✅ 연결됨"}
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
    except:
        return {"Equity": 0, "Margin": 0, "Status": "❌ 통신실패"}

# --- 2. 화면 구성 ---
st.title("🛡️ GRVT Live Account Monitor")

# [추가] 수동 새로고침 버튼
# 버튼을 누르면 Streamlit이 코드를 처음부터 다시 읽으며 데이터를 갱신합니다.
if st.button('🔄 지금 수동 새로고침'):
    st.toast("데이터를 새로 불러오는 중...") # 폰 하단에 작게 알림이 뜹니다.

# 30초 자동 갱신 구역
@st.fragment(run_every=30)
def show_dashboard():
    all_results = []
    for i in range(1, 7):
        name = f"GR{i}"
        if name in st.secrets:
            sec = st.secrets[name]
            real_data = get_real_grvt_balance(sec['api_key'], sec['api_secret'], sec['sub_id'])
            all_results.append({
                "계정": name,
                "순자산(Equity)": real_data["Equity"],
                "마진비율(%)": real_data["Margin"],
                "상태": real_data["Status"],
                "갱신시간": time.strftime("%H:%M:%S")
            })

    if all_results:
        df = pd.DataFrame(all_results)
        st.metric("총 통합 순자산", f"${df['순자산(Equity)'].sum():,.2f}")
        st.dataframe(
            df.style.format({"순자산(Equity)": "{:,.2f}"}).background_gradient(subset=['마진비율(%)'], cmap="Reds"),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("Secrets 설정을 확인하세요!")

show_dashboard()

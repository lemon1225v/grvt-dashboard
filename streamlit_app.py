import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests

st.set_page_config(page_title="GRVT 통합 모니터", layout="wide")

# --- 1. SDK 없이 직접 API 호출하는 함수 ---
def get_grvt_data_direct(api_key, api_secret, sub_id):
    try:
        base_url = "https://api.grvt.io"
        timestamp = str(int(time.time() * 1000))
        path = f"/v1/accounts/{sub_id}/summary"
        
        # 보안 서명 생성 (GRVT 규격)
        message = timestamp + "GET" + path
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "GRVT-API-KEY": api_key,
            "GRVT-TIMESTAMP": timestamp,
            "GRVT-SIGNATURE": signature,
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{base_url}{path}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "Equity": float(data.get('total_equity', 0)),
                "Margin": float(data.get('margin_usage_ratio', 0)) * 100,
                "Status": "✅ 연결됨"
            }
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
    except Exception as e:
        return {"Equity": 0, "Margin": 0, "Status": "❌ 통신실패"}

# --- 2. 대시보드 화면 구성 ---
st.title("🛡️ GRVT Live Account Monitor")

if st.button('🔄 지금 수동 새로고침'):
    st.rerun()

@st.fragment(run_every=30)
def show_dashboard():
    all_results = []
    for i in range(1, 7):
        name = f"GR{i}"
        if name in st.secrets:
            sec = st.secrets[name]
            # 직접 호출 함수 사용
            res = get_grvt_data_direct(sec['api_key'], sec['api_secret'], sec['sub_id'])
            all_results.append({
                "계정": name,
                "순자산(Equity)": res["Equity"],
                "마진비율(%)": res["Margin"],
                "상태": res["Status"],
                "갱신시간": time.strftime("%H:%M:%S")
            })

    if all_results:
        df = pd.DataFrame(all_results)
        st.metric("총 통합 순자산", f"${df['순자산(Equity)'].sum():,.2f}")
        st.dataframe(
            df.style.format({"순자산(Equity)": "{:,.2f}", "마진비율(%)": "{:.1f}%"})
            .background_gradient(subset=['마진비율(%)'], cmap="Reds", vmin=0, vmax=100),
            use_container_width=True, hide_index=True
        )
    else:
        st.error("Secrets 설정을 확인하세요!")

show_dashboard()

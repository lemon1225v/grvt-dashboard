import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests

st.set_page_config(page_title="GRVT 실시간 모니터", layout="wide")

def get_grvt_data_final(api_key, api_secret, sub_id):
    try:
        base_url = "https://api.grvt.io"
        timestamp = str(int(time.time() * 1000))
        path = f"/v1/accounts/{sub_id}/summary"
        
        message = timestamp + "GET" + path
        signature = hmac.new(api_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": timestamp,
            "grvt-signature": signature,
            "Accept": "application/json"
        }
        
        response = requests.get(f"{base_url}{path}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # 데이터가 들어있을 수 있는 모든 경로를 탐색
            res = data.get('result', data) if isinstance(data, dict) else {}
            
            # 'total_equity' 또는 'equity' 중 존재하는 값을 가져옴
            equity = res.get('total_equity') or res.get('equity') or 0
            # 'margin_usage_ratio'가 없을 경우 0으로 처리
            margin = res.get('margin_usage_ratio') or res.get('margin_usage') or 0
            
            return {
                "Equity": float(equity),
                "Margin": float(margin) * 100,
                "Status": "✅ 연결됨"
            }
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
            
    except Exception as e:
        return {"Equity": 0, "Margin": 0, "Status": "❌ 연결불가"}

st.title("🛡️ GRVT Multi-Account Monitor")

if st.button('🔄 지금 수동 새로고침'):
    st.rerun()

@st.fragment(run_every=30)
def show_dashboard():
    all_results = []
    for i in range(1, 7):
        name = f"GR{i}"
        if name in st.secrets:
            sec = st.secrets[name]
            res = get_grvt_data_final(sec['api_key'], sec['api_secret'], sec['sub_id'])
            all_results.append({
                "계정": name,
                "순자산(Equity)": res["Equity"],
                "마진비율(%)": res["Margin"],
                "상태": res["Status"],
                "갱신": time.strftime("%H:%M:%S")
            })

    if all_results:
        df = pd.DataFrame(all_results)
        st.metric("총 통합 자산", f"${df['순자산(Equity)'].sum():,.2f}")
        st.dataframe(
            df.style.format({"순자산(Equity)": "{:,.2f}", "마진비율(%)": "{:.1f}%"})
            .background_gradient(subset=['마진비율(%)'], cmap="Reds", vmin=0, vmax=100),
            width='stretch', hide_index=True
        )

show_dashboard()

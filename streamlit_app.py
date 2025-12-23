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
        # 1. 타임스탬프 (밀리초 단위 문자열)
        timestamp = str(int(time.time() * 1000))
        method = "GET"
        path = f"/v1/accounts/{sub_id}/summary"
        
        # 2. 서명 생성 (이 순서와 대소문자가 틀리면 '연결불가'가 뜹니다)
        # GRVT 규격: timestamp + method + path
        message = timestamp + method + path
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 3. 헤더 구성 (모두 소문자로 작성하는 것이 안전합니다)
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": timestamp,
            "grvt-signature": signature,
            "accept": "application/json"
        }
        
        # 4. 실제 데이터 요청
        response = requests.get(base_url + path, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # 데이터 추출 (구조가 중첩되어 있을 경우를 대비)
            res = data.get('result', data)
            return {
                "Equity": float(res.get('total_equity', 0)),
                "Margin": float(res.get('margin_usage_ratio', 0)) * 100,
                "Status": "✅ 연결됨"
            }
        elif response.status_code == 401:
            return {"Equity": 0, "Margin": 0, "Status": "❌ 키/비밀번호 오류"}
        elif response.status_code == 404:
            return {"Equity": 0, "Margin": 0, "Status": "❌ 계정ID(SubID) 오류"}
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 서버에러({response.status_code})"}
            
    except Exception as e:
        # 접속 자체가 안될 때 에러 메시지를 구체적으로 표시
        return {"Equity": 0, "Margin": 0, "Status": f"❌ 연결실패({str(e)[:10]})"}

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

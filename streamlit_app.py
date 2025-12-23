import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests

st.set_page_config(page_title="GRVT 실시간 모니터", layout="wide")

def get_grvt_data_final(api_key, api_secret, sub_id):
    try:
        # 1. 주소 설정 (가장 최신 메인넷 주소)
        base_url = "https://api.grvt.io"
        timestamp = str(int(time.time() * 1000))
        path = f"/v1/accounts/{sub_id}/summary"
        
        # 2. 보안 서명 생성 (이 순서가 아주 중요합니다)
        message = timestamp + "GET" + path
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 3. 헤더 구성
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": timestamp,
            "grvt-signature": signature
        }
        
        # 4. 데이터 요청
        response = requests.get(base_url + path, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # 서버 응답에서 숫자를 찾는 경로를 2중으로 확인합니다
            res = data.get('result', data)
            
            # 소수점이 길게 올 수 있으므로 안전하게 변환
            equity = float(res.get('total_equity', 0))
            margin = float(res.get('margin_usage_ratio', 0)) * 100
            
            return {"Equity": equity, "Margin": margin, "Status": "✅ 연결됨"}
        
        elif response.status_code in [401, 403]:
            return {"Equity": 0, "Margin": 0, "Status": "❌ 키 권한오류"}
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
            
    except Exception as e:
        # 에러가 나면 괄호 안에 에러 앞부분을 살짝 보여줍니다
        return {"Equity": 0, "Margin": 0, "Status": f"❌ 연결불가({str(e)[:5]})"}

# --- 화면 UI ---
st.title("🛡️ GRVT Multi-Account Monitor")

if st.button('🔄 지금 수동 새로고침'):
    st.rerun()

# 30초마다 자동 갱신
@st.fragment(run_every=30)
def show_dashboard():
    all_results = []
    # 1번부터 6번 계정까지 반복
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
                "갱신시간": time.strftime("%H:%M:%S")
            })

    if all_results:
        df = pd.DataFrame(all_results)
        # 총 합계 표시
        total_val = df["순자산(Equity)"].sum()
        st.metric("총 통합 순자산", f"${total_val:,.2f}")
        
        # 표 그리기
        st.dataframe(
            df.style.format({"순자산(Equity)": "{:,.2f}", "마진비율(%)": "{:.1f}%"})
            .background_gradient(subset=['마진비율(%)'], cmap="Reds", vmin=0, vmax=100),
            width='stretch', hide_index=True
        )
    else:
        st.error("Secrets 설정에 GR1~GR6 정보가 없습니다.")

show_dashboard()

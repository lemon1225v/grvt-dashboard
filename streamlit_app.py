import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests

st.set_page_config(page_title="GRVT 실시간 모니터", layout="wide")

def get_grvt_data_final(api_key, api_secret, sub_id):
    try:
        # 1. 환경 설정 (메인넷 주소)
        base_url = "https://api.grvt.io"
        timestamp = str(int(time.time() * 1000))
        method = "GET"
        # 정확한 엔드포인트 경로
        path = f"/v1/accounts/{sub_id}/summary"
        
        # 2. GRVT 전용 보안 서명(Signature) 생성
        # 주의: 메서드(GET)는 대문자여야 하며 경로가 정확해야 합니다.
        message = timestamp + method + path
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 3. 헤더 구성
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": timestamp,
            "grvt-signature": signature,
            "Accept": "application/json"
        }
        
        # 4. 요청 보내기
        response = requests.get(f"{base_url}{path}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # API 결과값에서 데이터 추출 (GRVT 응답 구조에 맞춤)
            return {
                "Equity": float(data.get('total_equity', 0)),
                "Margin": float(data.get('margin_usage_ratio', 0)) * 100,
                "Status": "✅ 연결됨"
            }
        elif response.status_code == 401 or response.status_code == 403:
            return {"Equity": 0, "Margin": 0, "Status": "❌ 키오류(권한)"}
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
            
    except Exception as e:
        return {"Equity": 0, "Margin": 0, "Status": "❌ 연결불가"}

# --- 화면 UI ---
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
            # 최종 함수 호출
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
        # 최신 Streamlit 규격에 맞게 width='stretch' 사용
        st.dataframe(
            df.style.format({"순자산(Equity)": "{:,.2f}", "마진비율(%)": "{:.1f}%"})
            .background_gradient(subset=['마진비율(%)'], cmap="Reds", vmin=0, vmax=100),
            width='stretch', hide_index=True
        )
    else:
        st.error("Secrets에 [GR1]~[GR6] 정보가 없습니다!")

show_dashboard()

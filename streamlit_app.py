import streamlit as st
import pandas as pd
import time
from grvt_pysdk.api import GrvtApi # 공식 SDK 사용

st.set_page_config(page_title="GRVT 통합 모니터", layout="wide")

# --- 1. 진짜 데이터 불러오기 함수 (공식 SDK 버전) ---
def get_grvt_data(api_key, api_secret, sub_id):
    try:
        # 공식 SDK를 사용하여 보안 연결 (서명 자동 처리)
        client = GrvtApi(api_key=api_key, api_secret=api_secret)
        
        # 계정 요약 정보 요청
        summary = client.get_sub_account_summary(sub_account_id=sub_id)
        
        return {
            "Equity": float(summary.total_equity),
            "Margin": float(summary.margin_usage_ratio) * 100,
            "Status": "✅ 연결됨"
        }
    except Exception as e:
        # 에러 발생 시 로그 확인용 (필요시)
        return {"Equity": 0, "Margin": 0, "Status": "❌ 인증실패"}

# --- 2. 화면 구성 ---
st.title("🛡️ GRVT Live Account Monitor")

if st.button('🔄 지금 수동 새로고침'):
    st.toast("최신 데이터를 불러오는 중...")

@st.fragment(run_every=30)
def show_dashboard():
    all_results = []
    
    # Secrets에서 GR1~GR6 정보를 가져와 연동
    for i in range(1, 7):
        name = f"GR{i}"
        if name in st.secrets:
            sec = st.secrets[name]
            # 진짜 정보를 가져옵니다
            real_data = get_grvt_data(sec['api_key'], sec['api_secret'], sec['sub_id'])
            
            all_results.append({
                "계정": name,
                "순자산(Equity)": real_data["Equity"],
                "마진비율(%)": real_data["Margin"],
                "상태": real_data["Status"],
                "갱신시간": time.strftime("%H:%M:%S")
            })

    if all_results:
        df = pd.DataFrame(all_results)
        
        # 총 자산 표시
        total_equity = df["순자산(Equity)"].sum()
        st.metric("총 통합 순자산", f"${total_equity:,.2f}")
        
        # 표 출력 (마진 80% 이상 빨간색 강조)
        st.dataframe(
            df.style.format({"순자산(Equity)": "{:,.2f}", "마진비율(%)": "{:.1f}%"})
            .background_gradient(subset=['마진비율(%)'], cmap="Reds", vmin=0, vmax=100),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("Secrets 설정을 확인하세요! [GR1] 형식이 맞나요?")

show_dashboard()

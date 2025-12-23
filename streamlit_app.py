import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="GRVT 실시간 모니터", layout="wide")

# --- 1. 실시간 업데이트용 '조각(Fragment)' 설정 ---
# run_every=30 은 30초마다 이 함수만 다시 실행하라는 뜻입니다.
@st.fragment(run_every=30)
def show_realtime_data():
    all_data = []
    
    # Secrets에서 6개 계정 읽어오기
    for i in range(1, 7):
        acc_name = f"account{i}"
        if acc_name in st.secrets:
            # 여기에 실제 API 호출 함수를 넣습니다. (지금은 예시 데이터)
            acc_info = st.secrets[acc_name]
            all_data.append({
                "계정": f"Account {i}",
                "Equity": 12500.0 + (i * 100), # 실제 자산 데이터가 들어갈 자리
                "마진비율(%)": 15.0 + (i * 5),  # 실제 마진 데이터
                "업데이트": time.strftime("%H:%M:%S") # 현재 시간 표시
            })
    
    if all_data:
        df = pd.DataFrame(all_data)
        
        # 화면 출력 (표)
        st.subheader("📊 실시간 계정 상태 (30초마다 갱신)")
        st.dataframe(df, use_container_width=True)
        
        # 합산 자산
        total = df["Equity"].sum()
        st.metric("총 통합 자산", f"${total:,.2f}")
    else:
        st.error("Secrets 설정을 확인해주세요!")

# --- 2. 메인 화면 실행 ---
st.title("🛡️ GRVT Multi-Account Live Monitor")
show_realtime_data()

st.caption("화면이 깜빡이지 않고 데이터만 30초마다 조용히 업데이트됩니다.")

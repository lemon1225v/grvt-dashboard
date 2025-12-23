import streamlit as st
import pandas as pd
import time

# 페이지 설정
st.set_page_config(page_title="GRVT 통합 모니터", layout="wide", page_icon="🛡️")

# --- 1. 실시간 데이터 업데이트 조각 (Fragment) ---
@st.fragment(run_every=30)
def show_grvt_dashboard():
    all_data = []
    
    # GR1부터 GR6까지 반복하며 Secrets에서 정보를 가져옵니다.
    for i in range(1, 7):
        acc_label = f"GR{i}"  # Secrets에서 [GR1], [GR2]... 를 찾음
        
        if acc_label in st.secrets:
            acc_info = st.secrets[acc_label]
            
            # [참고] 현재는 틀을 잡기 위한 샘플 데이터입니다.
            # 나중에 실제 API 연동 코드가 들어가면 이 부분이 실시간 잔고로 바뀝니다.
            all_data.append({
                "계정명": acc_label,
                "ID": acc_info.get('sub_id', 'N/A')[:8],
                "순자산(Equity)": 10000.0 + (i * 500), # 임시값
                "마진비율(%)": 20.0 + (i * 7),       # 임시값
                "상태": "✅ 정상",
                "최근갱신": time.strftime("%H:%M:%S")
            })
    
    if all_data:
        df = pd.DataFrame(all_data)
        
        # 상단 요약 지표
        total_equity = df["순자산(Equity)"].sum()
        cols = st.columns(3)
        cols[0].metric("총 통합 자산", f"${total_equity:,.2f}")
        cols[1].metric("활성 계정 수", f"{len(df)}개")
        cols[2].metric("평균 마진율", f"{df['마진비율(%)'].mean():.1f}%")

        st.divider()

        # 데이터 표 출력
        st.subheader("📊 계정별 상세 리스크 상황")
        
        # 마진비율이 80%를 넘으면 빨간색으로 표시하는 스타일 적용
        def color_margin(val):
            color = 'red' if isinstance(val, float) and val > 80 else 'none'
            return f'background-color: {color}'

        st.dataframe(
            df.style.applymap(color_margin, subset=['마진비율(%)']),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"🔄 30초마다 자동으로 데이터를 불러옵니다. (마지막 갱신: {time.strftime('%H:%M:%S')})")
    else:
        st.error("Secrets에서 [GR1] ~ [GR6] 설정을 찾을 수 없습니다.")
        st.info("Streamlit App Settings -> Secrets 칸에 [GR1], [GR2] 형식이 맞는지 확인해주세요.")

# --- 2. 메인 실행부 ---
st.title("🛡️ GRVT Multi-Account Live Monitor")
st.write(f"현재 접속 중인 관리자: **초보 트레이더님**")

# 대시보드 실행
show_grvt_dashboard()

import streamlit as st
import pandas as pd
import requests # 초보자를 위해 SDK 대신 직접 API 호출 방식을 사용합니다

st.set_page_config(page_title="GRVT 통합 관리", layout="wide")
st.title("📱 GRVT 실시간 리스크 대시보드")

# 보안을 위해 실제 키는 3단계에서 입력합니다.
def get_data(api_key, sub_id):
    # 이 부분은 GRVT의 공개 API 주소로 정보를 가져오는 가상의 예시입니다.
    # 실제 연동 시에는 Streamlit Secrets에 저장된 키를 사용하게 됩니다.
    return {"Account": sub_id[:8], "Equity": 10250.5, "Margin_Ratio": 15.2, "uPnL": +150.2}

# 화면 구성
st.subheader("모든 계정 요약")
# 실제로는 반복문을 통해 여러 계정 데이터를 합칩니다.
data = [get_data("key1", "acc_main"), get_data("key2", "acc_sub1")]
df = pd.DataFrame(data)

# 리스크 시각화 (마진 비율이 높으면 빨간색)
st.data_editor(df, column_config={
    "Margin_Ratio": st.column_config.ProgressColumn("리스크(%)", min_value=0, max_value=100)
})

st.info("💡 30분마다 자동 새로고침됩니다.")

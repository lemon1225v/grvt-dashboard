import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import urllib3

# HTTPS 보안 경고 메시지 끄기 (연결불가 방지용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GRVT 통합 모니터", layout="wide")

def get_grvt_data_final(api_key, api_secret, sub_id):
    """
    GRVT API에서 자산 및 마진 데이터를 가져오는 핵심 함수
    """
    try:
        base_url = "https://api.grvt.io"
        timestamp = str(int(time.time() * 1000))
        path = f"/v1/accounts/{sub_id}/summary"
        
        # 1. 서명(Signature) 생성 - 순서와 대소문자 엄격 준수
        message = timestamp + "GET" + path
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 2. 헤더 구성
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": timestamp,
            "grvt-signature": signature,
            "Accept": "application/json"
        }
        
        # 3. 데이터 요청 - verify=False로 HTTPS 인증서 문제 해결
        response = requests.get(
            base_url + path, 
            headers=headers, 
            timeout=10, 
            verify=False
        )
        
        if response.status_code == 200:
            raw_data = response.json()
            # 데이터가 'result' 키 안에 들어있는 최신 API 규격 대응
            data = raw_data.get('result', raw_data)
            
            # 값이 없을 경우를 대비해 안전하게 추출
            equity = float(data.get('total_equity', 0))
            margin_ratio = float(data.get('margin_usage_ratio', 0)) * 100
            
            return {
                "Equity": equity,
                "Margin": margin_ratio,
                "Status": "✅ 연결됨"
            }
        elif response.status_code in [401, 403]:
            return {"Equity": 0, "Margin": 0, "Status": "❌ 키 권한 오류"}
        elif response.status_code == 404:
            return {"Equity": 0, "Margin": 0, "Status": "❌ sub_id 오류"}
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
            
    except Exception as e:
        # 에러 발생 시 종류를 짧게 표시 (예: ConnectionError)
        return {"Equity": 0, "Margin": 0, "Status": f"❌ 연결불가({type(e).__name__[:5]})"}

# --- 화면 레이아웃 시작 ---
st.title("🛡️ GRVT Multi-Account Real-time Monitor")

# 수동 새로고침 버튼
if st.button('🔄 데이터 즉시 갱신'):
    st.rerun()

# 30초마다 자동으로 데이터를 새로고침하는 구간
@st.fragment(run_every=30)
def show_dashboard():
    results = []
    # GR1부터 GR6까지 반복 확인
    for i in range(1, 7):
        key_name = f"GR{i}"
        if key_name in st.secrets:
            s = st.secrets[key_name]
            # API 데이터 가져오기
            res = get_grvt_data_final(s['api_key'], s['api_secret'], s['sub_id'])
            results.append({
                "계정": key_name,
                "순자산(Equity)": res["Equity"],
                "마진비율(%)": res["Margin"],
                "상태": res["Status"],
                "최근갱신": time.strftime("%H:%M:%S")
            })

    if results:
        df = pd.DataFrame(results)
        
        # 상단 통합 지표
        total_equity = df["순자산(Equity)"].sum()
        st.metric("총 통합 순자산", f"${total_equity:,.2f}")
        
        # 데이터 테이블 스타일링
        def color_margin(val):
            # 마진 비율에 따른 배경색 경고 (80% 이상은 진한 빨강)
            color = 'transparent'
            if val >= 90: color = '#ff4b4b'
            elif val >= 70: color = '#ffa5a5'
            return f'background-color: {color}'

        # 테이블 출력
        st.dataframe(
            df.style.format({
                "순자산(Equity)": "${:,.2f}",
                "마진비율(%)": "{:.1f}%"
            }).applymap(color_margin, subset=['마진비율(%)']),
            width='stretch',
            hide_index=True
        )
    else:
        st.warning("Secrets 설정에서 [GR1] ~ [GR6] 정보를 찾을 수 없습니다.")

show_dashboard()

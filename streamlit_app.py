def get_grvt_data_final(api_key, api_secret, sub_id):
    try:
        base_url = "https://api.grvt.io"
        timestamp = str(int(time.time() * 1000))
        path = f"/v1/accounts/{sub_id}/summary"
        
        message = timestamp + "GET" + path
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "grvt-api-key": api_key,
            "grvt-timestamp": timestamp,
            "grvt-signature": signature,
            "Accept": "application/json"
        }
        
        # HTTPS 인증 오류를 방지하기 위해 verify=False 추가
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        response = requests.get(base_url + path, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            # 데이터가 'result' 키 안에 들어있는지 확인 후 추출
            res = data.get('result', data)
            
            return {
                "Equity": float(res.get('total_equity', 0)),
                "Margin": float(res.get('margin_usage_ratio', 0)) * 100,
                "Status": "✅ 연결됨"
            }
        else:
            return {"Equity": 0, "Margin": 0, "Status": f"❌ 오류({response.status_code})"}
            
    except Exception as e:
        # 에러 메시지를 더 자세히 표시하여 원인 파악
        return {"Equity": 0, "Margin": 0, "Status": f"❌ 연결불가({type(e).__name__})"}

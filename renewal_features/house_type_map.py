# 데이터셋의 '주택구분' 8종 → 국토부 전월세 실거래가 API 4종 매핑
# 단독다가구 API는 houseType 필드로 단독/다가구를 함께 반환하므로
# 다가구/다중/단독/주상복합을 전부 이 API로 근사한다. (9-3절 매칭 방식)

HOUSE_TYPE_TO_API = {
    "아파트": "apt",
    "다세대주택": "rh",
    "연립주택": "rh",
    "오피스텔": "offi",
    "다가구주택": "sh",
    "다중주택": "sh",
    "단독주택": "sh",
    "주상복합": "sh",
}

API_TYPES = ("apt", "rh", "sh", "offi")

# apis.data.go.kr 활용신청 완료 후 마이페이지에 표시되는 실제 URL과
# 다르면 이 값을 마이페이지 기준으로 교체할 것.
API_ENDPOINTS = {
    "apt": "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent",
    "rh": "https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent",
    "sh": "https://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent",
    "offi": "https://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent",
}

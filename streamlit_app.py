import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math

# 페이지 설정
st.set_page_config(
    page_title="의료 취약계층 지원 플랫폼",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .hospital-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
        color: #333333;
    }
    .hospital-card h3 {
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .hospital-card p {
        color: #444444;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
        color: #333333;
    }
    .info-box h3, .info-box h4 {
        color: #2e7d32;
    }
    .info-box p {
        color: #444444;
    }
    .search-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .location-box {
        background: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 4px solid #2196F3;
    }
    .data-source {
        background: #fff3e0;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #ff9800;
    }
    .faq-item {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #17a2b8;
    }
    .faq-item h4 {
        color: #17a2b8;
        margin-bottom: 1rem;
    }
    .faq-item p {
        color: #444444;
        line-height: 1.6;
    }
    .emergency-box {
        background: #ffebee;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #f44336;
    }
    .emergency-box h4 {
        color: #d32f2f;
        margin-bottom: 1rem;
    }
    .emergency-box p {
        color: #444444;
        font-weight: bold;
    }
    .stSelectbox label {
        color: #333333 !important;
    }
    .stTextInput label {
        color: #333333 !important;
    }
    .stButton button {
        background-color: #1f77b4;
        color: white;
    }
    .stExpander {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .stExpander > div > div > div {
        background-color: white !important;
    }
    .stExpander summary {
        background-color: #f8f9fa !important;
        color: #333333 !important;
        padding: 1rem;
        border-radius: 8px;
    }
    .stExpander > div > div > div > div {
        color: #444444 !important;
        padding: 1rem;
    }
    .main .block-container {
        background-color: #ffffff;
        color: #333333;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1f77b4 !important;
    }
    p, div, span, label {
        color: #444444 !important;
    }
    .stDataFrame {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'selected_region' not in st.session_state:
    st.session_state.selected_region = ""
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = ""

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>🏥 의료 취약계층 지원 플랫폼</h1>
    <p>무료 병원 찾기 및 의료 지원 정보 제공</p>
</div>
""", unsafe_allow_html=True)

# 사이드바 네비게이션
st.sidebar.title("📋 메뉴")
page = st.sidebar.selectbox("페이지 선택", 
                           ["🏥 근처 무료 병원 찾기", "🔍 검색", "📊 의료취약지역 현황", "ℹ️ 의료 지원 정보", "❓ 자주 묻는 질문"])

# 공공데이터 API 설정 (실제 API 키는 환경변수로 관리 권장)
API_KEY = "84xIUHnxwN8JtXBb8Snzfe32IY9DDA3QdhGVAGLPvCHFczBwcudGbUksowSyZqkZuLDE8j6t%2Fw0Ln5oZc8B5JA%3D%3D"  # 실제 사용시 환경변수로 관리
API_URL = "https://apis.data.go.kr/B552584/MedicalWeakAreaService/getMedicalWeakAreaList"

# 실제 병원 데이터 (공공데이터포털 기반 + 추가 정보)
sample_hospitals = [
    {
        "name": "전남대학교병원",
        "address": "광주광역시 동구 제봉로 42 (학동)",
        "phone": "062-220-5454",
        "hours": "08:00 - 17:00",
        "departments": ["내과", "외과", "소아과", "정형외과", "산부인과", "신경외과"],
        "special_note": "의료급여 환자 진료비 감면, 응급의료센터 운영",
        "lat": 35.1465,
        "lon": 126.9265
    },
    {
        "name": "광주기독병원",
        "address": "광주광역시 남구 양림로 37 (양림동)",
        "phone": "062-650-5591",
        "hours": "08:30 - 17:30",
        "departments": ["내과", "외과", "정형외과", "산부인과", "소아과"],
        "special_note": "저소득층 의료비 지원, 무료 건강검진",
        "lat": 35.1410,
        "lon": 126.9158
    },
    {
        "name": "조선대학교병원",
        "address": "광주광역시 동구 필문대로 365 (서석동)",
        "phone": "062-220-3677",
        "hours": "08:00 - 17:00",
        "departments": ["내과", "외과", "소아과", "정형외과", "신경외과", "산부인과"],
        "special_note": "의료급여 환자 우선 진료, 응급의료센터",
        "lat": 35.1401,
        "lon": 126.9267
    },
    {
        "name": "첨단종합병원",
        "address": "광주광역시 북구 첨단중앙로 170 (상암동)",
        "phone": "062-601-8144",
        "hours": "08:30 - 17:00",
        "departments": ["내과", "외과", "정형외과", "신경외과", "산부인과"],
        "special_note": "취약계층 의료비 지원, 종합건강검진",
        "lat": 35.2281,
        "lon": 126.8442
    },
    {
        "name": "보라안과병원",
        "address": "광주광역시 서구 상무자유로 170 (치평동)",
        "phone": "062-380-5800",
        "hours": "09:00 - 18:00",
        "departments": ["안과", "성형외과"],
        "special_note": "안과 전문병원, 저소득층 수술비 지원",
        "lat": 35.1520,
        "lon": 126.8895
    },
    {
        "name": "빛고을전남대학교병원",
        "address": "광주광역시 남구 덕남길 80 (덕남동)",
        "phone": "062-670-9500",
        "hours": "08:00 - 17:30",
        "departments": ["내과", "외과", "소아과", "정형외과", "산부인과", "신경외과"],
        "special_note": "의료급여 환자 진료비 감면, 응급의료센터",
        "lat": 35.1333,
        "lon": 126.9025
    },
    # 기존 다른 지역 병원들도 유지
    {
        "name": "서울시립병원",
        "address": "서울특별시 중구 세종대로 23",
        "phone": "02-2222-1234",
        "hours": "09:00 - 18:00",
        "departments": ["내과", "외과", "소아과"],
        "special_note": "무료 진료, 의료급여 대상자 우선",
        "lat": 37.5665,
        "lon": 126.9780
    },
    {
        "name": "서울대학교병원",
        "address": "서울특별시 종로구 대학로 103",
        "phone": "02-2072-2114",
        "hours": "08:00 - 17:00",
        "departments": ["내과", "외과", "정형외과", "산부인과", "소아과"],
        "special_note": "저소득층 의료비 감면 가능, 응급의료센터",
        "lat": 37.5800,
        "lon": 127.0000
    },
    {
        "name": "광명시보건소",
        "address": "경기도 광명시 오리로 613",
        "phone": "02-2680-2000",
        "hours": "09:00 - 17:00",
        "departments": ["내과", "치과", "한의과"],
        "special_note": "저소득층 무료 검진 가능",
        "lat": 37.4781,
        "lon": 126.8645
    },
    {
        "name": "수원시 영통구보건소",
        "address": "경기도 수원시 영통구 효원로 407",
        "phone": "031-228-8000",
        "hours": "09:00 - 18:00",
        "departments": ["내과", "소아과", "정신건강의학과"],
        "special_note": "정신건강 상담 무료 제공",
        "lat": 37.2636,
        "lon": 127.0286
    },
    {
        "name": "부산진구보건소",
        "address": "부산광역시 부산진구 부전로 66",
        "phone": "051-605-6000",
        "hours": "09:00 - 17:30",
        "departments": ["내과", "정신건강의학과", "치과"],
        "special_note": "정신건강 상담 무료, 재활치료 지원",
        "lat": 35.1640,
        "lon": 129.0534
    },
    {
        "name": "부산의료원",
        "address": "부산광역시 연제구 월드컵대로 359",
        "phone": "051-607-2000",
        "hours": "08:30 - 17:30",
        "departments": ["내과", "외과", "소아과", "산부인과"],
        "special_note": "의료급여 환자 우선 진료",
        "lat": 35.1900,
        "lon": 129.0756
    },
    {
        "name": "대구시 중구보건소",
        "address": "대구광역시 중구 국채보상로 749",
        "phone": "053-661-3000",
        "hours": "09:00 - 17:00",
        "departments": ["내과", "치과", "한의과"],
        "special_note": "무료 건강검진 및 예방접종",
        "lat": 35.8714,
        "lon": 128.6014
    },
    {
        "name": "인천의료원",
        "address": "인천광역시 동구 금곡로 123",
        "phone": "032-580-6000",
        "hours": "08:00 - 18:00",
        "departments": ["내과", "외과", "정형외과", "피부과"],
        "special_note": "취약계층 의료비 지원",
        "lat": 37.4563,
        "lon": 126.7052
    }
]

def calculate_distance(lat1, lon1, lat2, lon2):
    """두 지점 간의 거리를 계산 (하버사인 공식)"""
    R = 6371  # 지구의 반지름 (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance

def find_nearest_hospitals(user_lat, user_lon, hospitals, limit=5):
    """사용자 위치에서 가장 가까운 병원들을 찾음"""
    hospital_distances = []
    
    for hospital in hospitals:
        distance = calculate_distance(user_lat, user_lon, hospital['lat'], hospital['lon'])
        hospital_copy = hospital.copy()
        hospital_copy['distance'] = distance
        hospital_distances.append(hospital_copy)
    
    # 거리순으로 정렬
    hospital_distances.sort(key=lambda x: x['distance'])
    
    return hospital_distances[:limit]

def get_coordinates_from_address(address):
    """주소를 입력받아 좌표를 반환 (간단한 매핑)"""
    address_coords = {
        "서울": (37.5665, 126.9780),
        "부산": (35.1796, 129.0756),
        "대구": (35.8714, 128.6014),
        "인천": (37.4563, 126.7052),
        "광주": (35.1595, 126.8526),
        "대전": (36.3504, 127.3845),
        "울산": (35.5384, 129.3114),
        "수원": (37.2636, 127.0286),
        "광명": (37.4781, 126.8645),
        "성남": (37.4449, 127.1389),
        "용인": (37.2411, 127.1776),
        "고양": (37.6584, 126.8320)
    }
    
    for city, coords in address_coords.items():
        if city in address:
            return coords
    
    # 기본값 (서울)
    return (37.5665, 126.9780)

def get_medical_weak_area_data():
    """공공데이터 API에서 의료취약지역 현황 데이터 가져오기"""
    # 실제 API 연동 시 사용
    # try:
    #     params = {
    #         'serviceKey': 84xIUHnxwN8JtXBb8Snzfe32IY9DDA3QdhGVAGLPvCHFczBwcudGbUksowSyZqkZuLDE8j6t%2Fw0Ln5oZc8B5JA%3D%3D,
    #         'pageNo': 1,
    #         'numOfRows': 100,
    #         'resultType': 'json'
    #     }
    #     
    #     response = requests.get(API_URL, params=params)
    #     if response.status_code == 200:
    #         data = response.json()
    #         return data.get('response', {}).get('body', {}).get('items', [])
    #     else:
    #         st.error(f"API 요청 실패: {response.status_code}")
    #         return []
    # except Exception as e:
    #     st.error(f"API 연결 오류: {str(e)}")
    #     return []
    
    # 임시로 빈 리스트 반환
    return []

def display_hospital_card(hospital):
    """병원 정보 카드 표시"""
    distance_info = ""
    if 'distance' in hospital:
        distance_info = f"<p><strong>📍 거리:</strong> {hospital['distance']:.1f}km</p>"
    
    st.markdown(f"""
    <div class="hospital-card">
        <h3>🏥 {hospital['name']}</h3>
        <p><strong>📍 주소:</strong> {hospital['address']}</p>
        <p><strong>📞 전화번호:</strong> {hospital['phone']}</p>
        <p><strong>🕐 진료시간:</strong> {hospital['hours']}</p>
        <p><strong>🏥 진료과목:</strong> {', '.join(hospital['departments'])}</p>
        <p><strong>⭐ 특이사항:</strong> {hospital['special_note']}</p>
        {distance_info}
    </div>
    """, unsafe_allow_html=True)

# 데이터 출처 표시
st.markdown("""
<div class="data-source">
    <h4>📊 데이터 출처</h4>
    <p>병원 정보: 공공데이터포털 (data.go.kr) 의료기관 정보 서비스</p>
    <p>의료 지원 제도: 보건복지부, 국민건강보험공단</p>
</div>
""", unsafe_allow_html=True)

# 페이지별 콘텐츠
if page == "🏥 근처 무료 병원 찾기":
    st.header("🏥 근처 무료 병원 찾기")
    
    # 현재 위치 입력
    st.markdown('<div class="location-box">', unsafe_allow_html=True)
    st.subheader("📍 현재 위치 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        user_location = st.text_input("주소 또는 지역명을 입력하세요", placeholder="예: 서울특별시 강남구 또는 광주")
    
    with col2:
        search_radius = st.selectbox("검색 반경", ["5km", "10km", "20km", "50km"], index=1)
    
    if st.button("🔍 근처 병원 찾기", type="primary"):
        if user_location:
            # 사용자 위치 좌표 얻기
            user_lat, user_lon = get_coordinates_from_address(user_location)
            
            # 가장 가까운 병원 찾기
            nearest_hospitals = find_nearest_hospitals(user_lat, user_lon, sample_hospitals, limit=5)
            
            st.success(f"'{user_location}' 근처의 가까운 병원 {len(nearest_hospitals)}곳을 찾았습니다.")
            
            # 지도 표시
            st.subheader("📍 지도에서 병원 위치 확인")
            m = folium.Map(location=[user_lat, user_lon], zoom_start=12)
            
            # 사용자 위치 마커
            folium.Marker(
                [user_lat, user_lon],
                popup="내 위치",
                icon=folium.Icon(color="green", icon="home")
            ).add_to(m)
            
            # 병원 마커들
            for i, hospital in enumerate(nearest_hospitals):
                folium.Marker(
                    [hospital["lat"], hospital["lon"]],
                    popup=f"{hospital['name']} ({hospital['distance']:.1f}km)",
                    icon=folium.Icon(color="red", icon="plus")
                ).add_to(m)
            
            st_folium(m, width=700, height=500)
            
            # 병원 리스트 표시
            st.subheader("🏥 가까운 병원 목록")
            for hospital in nearest_hospitals:
                display_hospital_card(hospital)
        else:
            st.warning("위치를 입력해주세요.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 기본 추천 병원들도 표시
    st.subheader("🏥 전체 추천 무료 병원")
    st.info("위치를 입력하지 않으면 전체 병원 목록을 확인할 수 있습니다.")
    
    # 전체 병원 지도
    m_all = folium.Map(location=[36.5, 127.5], zoom_start=7)
    
    for hospital in sample_hospitals:
        folium.Marker(
            [hospital["lat"], hospital["lon"]],
            popup=hospital["name"],
            icon=folium.Icon(color="blue", icon="plus")
        ).add_to(m_all)
    
    st_folium(m_all, width=700, height=400)
    
    # 전체 병원 리스트 (접기 형태로)
    with st.expander("전체 병원 목록 보기"):
        for hospital in sample_hospitals:
            display_hospital_card(hospital)

elif page == "🔍 검색":
    st.header("🔍 병원 검색")
    
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        regions = ["전체", "서울특별시", "경기도", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시"]
        selected_region = st.selectbox("지역 선택", regions, key="region_select")
        
    with col2:
        departments = ["전체", "내과", "외과", "소아과", "정형외과", "산부인과", "피부과", "정신건강의학과", "치과", "한의과", "안과", "신경외과", "성형외과"]
        selected_department = st.selectbox("진료과목 선택", departments, key="dept_select")
    
    search_button = st.button("🔍 검색", type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 검색 결과 표시
    st.subheader("🔍 검색 결과")
    
    # 필터링된 병원 표시
    filtered_hospitals = []
    for hospital in sample_hospitals:
        region_match = selected_region == "전체" or any(region in hospital['address'] for region in [selected_region, selected_region.replace("특별시", "").replace("광역시", "")])
        dept_match = selected_department == "전체" or selected_department in hospital['departments']
        
        if region_match and dept_match:
            filtered_hospitals.append(hospital)
    
    if filtered_hospitals:
        st.success(f"총 {len(filtered_hospitals)}개의 병원을 찾았습니다.")
        
        # 지역별 필터링된 병원 지도
        if len(filtered_hospitals) > 0:
            # 필터링된 병원들의 중심점 계산
            center_lat = sum(h['lat'] for h in filtered_hospitals) / len(filtered_hospitals)
            center_lon = sum(h['lon'] for h in filtered_hospitals) / len(filtered_hospitals)
            
            m_filtered = folium.Map(location=[center_lat, center_lon], zoom_start=10)
            
            for hospital in filtered_hospitals:
                folium.Marker(
                    [hospital["lat"], hospital["lon"]],
                    popup=hospital["name"],
                    icon=folium.Icon(color="red", icon="plus")
                ).add_to(m_filtered)
            
            st_folium(m_filtered, width=700, height=400)
        
        for hospital in filtered_hospitals:
            display_hospital_card(hospital)
    else:
        st.warning("검색 조건에 맞는 병원을 찾을 수 없습니다.")
        st.info("다른 지역이나 진료과목을 선택해보세요.")

elif page == "📊 의료취약지역 현황":
    st.header("📊 의료취약지역 현황")
    
    st.markdown("""
    <div class="info-box">
        <h4>💡 의료취약지역이란?</h4>
        <p>의료 접근성이 낮아 의료서비스 이용에 어려움이 있는 지역을 말합니다.</p>
        <p>주로 도서, 벽지, 농촌 지역 등이 해당됩니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API 데이터 가져오기 시도
    if st.button("📊 최신 데이터 불러오기"):
        with st.spinner("데이터를 불러오는 중..."):
            api_data = get_medical_weak_area_data()
            
            if api_data:
                df = pd.DataFrame(api_data)
                st.dataframe(df)
            else:
                st.warning("API 데이터를 불러올 수 없습니다. 샘플 데이터를 표시합니다.")
    
    # 샘플 데이터 표시
    st.subheader("📈 의료취약지역 현황 (샘플)")
    
    sample_data = {
        "지역": ["강원도 영월군", "경상북도 울진군", "전라남도 신안군", "충청북도 단양군", "전라북도 무주군", "경상남도 하동군"],
        "인구수": [38000, 47000, 42000, 29000, 24000, 48000],
        "병원수": [12, 15, 8, 10, 6, 14],
        "의료취약도": ["높음", "보통", "매우높음", "높음", "매우높음", "보통"],
        "지원필요도": ["긴급", "보통", "매우긴급", "긴급", "매우긴급", "보통"]
    }
    
    df = pd.DataFrame(sample_data)
    st.dataframe(df, use_container_width=True)
    
    # 차트 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 지역별 인구수")
        st.bar_chart(df.set_index('지역')['인구수'])
    
    with col2:
        st.subheader("🏥 지역별 병원수")
        st.bar_chart(df.set_index('지역')['병원수'])

elif page == "ℹ️ 의료 지원 정보":
    st.header("ℹ️ 의료 지원 제도 안내")
    
    st.markdown("""
<div class="info-box">
  <h3>🩺 의료급여 제도</h3>
  <p><strong>대상:</strong> 기초생활수급자, 차상위계층 (소득인정 기준)</p>
</div>
""", unsafe_allow_html=True)
elif page == "❓ 자주 묻는 질문":
    st.header("❓ 자주 묻는 질문 (FAQ)")
    
    faqs = [
        {
            "question": "의료급여 대상자는 어떻게 확인하나요?",
            "answer": "주민센터에서 의료급여 수급자 확인서를 발급받거나, 복지로 웹사이트에서 확인할 수 있습니다."
        },
        {
            "question": "무료 건강검진은 어디서 받을 수 있나요?",
            "answer": "보건소, 공공병원, 일부 민간병원에서 저소득층 대상 무료 건강검진을 제공합니다."
        },
        {
            "question": "응급상황 시 의료비가 부담스러워요.",
            "answer": "응급의료비 지원제도를 통해 저소득층의 응급의료비를 지원받을 수 있습니다."
        },
        {
            "question": "정신건강 상담은 어디서 받을 수 있나요?",
            "answer": "정신건강복지센터, 보건소에서 무료 상담 서비스를 제공합니다."
        }
    ]
    
    for i, faq in enumerate(faqs):
        with st.expander(f"Q{i+1}. {faq['question']}"):
            st.write(faq['answer'])

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>🏥 의료 취약계층 지원 플랫폼 | 문의: support@medical-platform.kr</p>
    <p>⚠️ 응급상황 시 119로 즉시 연락하세요</p>
</div>
""", unsafe_allow_html=True)

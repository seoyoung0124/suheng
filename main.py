import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="나에게 딱 맞는 노트북 찾기",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sample Laptop Dataset
@st.cache_data
def load_data():
    data = {
        "제품명": [
            "맥북 에어 15 (M3)", "삼성 갤럭시북4 프로", "LG 그램 프로 16", 
            "에이수스 터프 게이밍 A15", "레노버 리전 프로 5", "애플 맥북 프로 14 (M3 Pro)",
            "HP 오멘 16", "레노버 아이디어패드 슬림 3"
        ],
        "브랜드": ["Apple", "Samsung", "LG", "ASUS", "Lenovo", "Apple", "HP", "Lenovo"],
        "용도": ["사무/인강용", "사무/인강용", "사무/인강용", "게이밍", "게이밍", "영상편집/전문가", "게이밍", "사무/인강용"],
        "가격(만원)": [189, 175, 199, 135, 210, 269, 185, 65],
        "무게(kg)": [1.51, 1.23, 1.28, 2.20, 2.50, 1.61, 2.35, 1.41],
        "RAM(GB)": [16, 16, 16, 16, 32, 18, 32, 8],
        "CPU": ["Apple M3", "Intel Core Ultra 7", "Intel Core Ultra 7", "AMD Ryzen 7", "AMD Ryzen 7", "Apple M3 Pro", "Intel i7-14700HX", "AMD Ryzen 5"],
        "화면크기(인치)": [15.3, 16.0, 16.0, 15.6, 16.0, 14.2, 16.1, 15.6],
        "평점": [4.9, 4.8, 4.7, 4.5, 4.8, 5.0, 4.6, 4.3],
        "특징": ["압도적 배터리, 무소음", "선명한 AMOLED, 가벼움", "초경량 대화면", "가성비 게이밍", "성능과 쿨링의 완벽한 조화", "전문가용 최고급 성능", "고성능 그래픽 작업", "극가성비 웹서핑/과제"]
    }
    return pd.DataFrame(data)

df = load_data()

# Custom CSS Styling for a cleaner look
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation Menu
st.sidebar.title("💻 노트북 내비게이션")
menu = st.sidebar.radio(
    "메뉴를 선택하세요",
    ["홈 (대시보드)", "맞춤 추천 찾기", "스펙 비교실", "노트북 구매 가이드"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 스트림릿 클라우드 배포용 단일 파일 앱입니다. 언제 어디서나 최적의 노트북을 찾아보세요!")

# 1. Home Dashboard
if menu == "홈 (대시보드)":
    st.markdown('<p class="main-header">✨ 나에게 딱 맞는 노트북 찾기</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">복잡한 스펙 비교는 그만! 용도와 예산에 맞는 최적의 제품을 한눈에 확인하세요.</p>', unsafe_allow_html=True)
    
    # Quick Search Bar
    st.subheader("🚀 빠른 검색")
    col1, col2 = st.columns(2)
    with col1:
        selected_purpose = st.selectbox("원하는 주 사용 목적을 선택하세요", ["전체"] + list(df["용도"].unique()))
    with col2:
        max_budget = st.slider("최대 예산 한도 (만 원)", 50, 300, 200, step=10)
        
    # Filter logic
    filtered_df = df.copy()
    if selected_purpose != "전체":
        filtered_df = filtered_df[filtered_df["용도"] == selected_purpose]
    filtered_df = filtered_df[filtered_df["가격(만원)"] <= max_budget]
    
    st.markdown(f"### 🔍 검색 결과 ({len.shape[0] if hasattr(filtered_df, 'shape') else 0}개 모델 발견)" if len(filtered_df) > 0 else "### 🔍 검색 결과")
    
    if len(filtered_df) > 0:
        for idx, row in filtered_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h4><b>{row['제품명']}</b> ({row['브랜드']})</h4>
                    <p><b>💰 가격:</b> {row['가격(만원)']}만 원 &nbsp;|&nbsp; <b>⚖️ 무게:</b> {row['무게(kg)']}kg &nbsp;|&nbsp; <b>🧠 RAM:</b> {row['RAM(GB)']}GB &nbsp;|&nbsp; <b>⭐ 평점:</b> {row['평점']}</p>
                    <p><b>✨ 주요 특징:</b> {row['특징']} (CPU: {row['CPU']})</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("조건에 맞는 노트북이 없습니다. 예산이나 용도를 조정해 보세요!")

    # Trending Section
    st.markdown("---")
    st.subheader("🔥 금주의 베스트 인기 모델 추천")
    top_models = df.sort_values(by="평점", ascending=False).head(3)
    c1, c2, c3 = st.columns(3)
    
    for i, (_, row) in enumerate(top_models.iterrows()):
        col = [c1, c2, c3][i]
        with col:
            st.metric(label=row['제품명'], value=f"{row['가격(만원']}만 원", delta=f"평점 {row['평점']}")
            st.write(f"특징: {row['특징']}")

# 2. Detailed Recommendation
elif menu == "맞춤 추천 찾기":
    st.markdown('<p class="main-header">🔍 상세 맞춤 추천 설문</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">몇 가지 질문에 답해주시면 가장 적합한 노트북을 정밀 매칭해 드립니다.</p>', unsafe_allow_html=True)
    
    with st.form("recommendation_form"):
        p_use = st.selectbox("1. 주로 어떤 용도로 사용하시나요?", ["사무/인강용", "게이밍", "영상편집/전문가"])
        p_budget = st.slider("2. 예산 범위를 선택해주세요 (만 원 단위)", 50, 300, 150)
        p_weight = st.radio("3. 휴대성(무게)이 얼마나 중요하신가요?", ["상관없음 (성능 위주)", "가벼운 편이 좋음 (1.5kg 이하)"])
        
        submitted = st.form_submit_button("맞춤 노트북 추천받기!")
        
        if submitted:
            st.success("🎉 분석 완료! 회원님께 추천하는 노트북 리스트입니다.")
            result_df = df[(df["용도"] == p_use) & (df["가격(만원)"] <= p_budget)]
            if "1.5kg 이하" in p_weight:
                result_df = result_df[result_df["무게(kg)"] <= 1.5]
                
            if len(result_df) > 0:
                st.dataframe(result_df[["제품명", "브랜드", "가격(만원)", "무게(kg)", "RAM(GB)", "CPU", "특징"]], use_container_width=True)
            else:
                st.info("입력하신 조건과 정확히 일치하는 모델이 없어, 예산 내 동급 모델을 추천합니다.")
                fallback_df = df[df["용도"] == p_use].head(3)
                st.dataframe(fallback_df[["제품명", "브랜드", "가격(만원)", "무게(kg)", "RAM(GB)", "CPU", "특징"]], use_container_width=True)

# 3. Spec Comparison
elif menu == "스펙 비교실":
    st.markdown('<p class="main-header">📊 노트북 스펙 비교실</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">비교하고 싶은 노트북을 선택하여 스펙을 나란히 비교해 보세요.</p>', unsafe_allow_html=True)
    
    selected_laptops = st.multiselect(
        "비교할 노트북을 선택하세요 (최대 3개 권장)",
        df["제품명"].tolist(),
        default=df["제품명"].tolist()[:2]
    )
    
    if selected_laptops:
        compare_df = df[df["제품명"].isin(selected_laptops)].set_index("제품명")
        st.table(compare_df.T)
    else:
        st.warning("비교할 노트북을 하나 이상 선택해주세요.")

# 4. Buying Guide
elif menu == "노트북 구매 가이드":
    st.markdown('<p class="main-header">📖 초보자를 위한 노트북 구매 가이드</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">어떤 스펙을 골라야 할지 모르겠다면 아래 가이드를 확인해보세요.</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🧠 CPU & RAM", "⚖️ 무게와 휴대성", "💰 용도별 권장 예산"])
    
    with tab1:
        st.subheader("CPU와 RAM의 핵심 요약")
        st.markdown("""
        - **CPU (중앙처리장치)**: 노트북의 두뇌입니다.
          - *인텔 i3 / AMD 라이젠 3*: 간단한 문서 작업 및 웹서핑
          - *인텔 i5 / 라이젠 5 (또는 울트라 7, M시리즈)*: 대학생 과제, 멀티태스킹, 캐주얼 게임 (가장 추천)
          - *인텔 i7/i9, 라이젠 7/9*: 고사양 게임, 4K 영상 편집, 3D 렌더링
        - **RAM (메모리)**: 작업할 때 책상 크기입니다.
          - *8GB*: 간단한 용도 (추천하지 않음, 업그레이드 불가 모델 많음)
          - *16GB*: 표준 권장 사양 (대부분의 용도에 적합)
          - *32GB 이상*: 전문가 및 고사양 게이머
        """)
        
    with tab2:
        st.subheader("무게에 따른 휴대성 기준")
        st.markdown("""
        - **1.0kg ~ 1.3kg**: 매우 가벼움 (매일 들고 다니는 대학생/직장인 추천, 예: LG 그램, 갤럭시북 프로)
        - **1.4kg ~ 1.7kg**: 무난함 (가끔 가방에 넣어 다니는 용도, 맥북 에어 등)
        - **1.8kg 이상**: 주로 거치해두고 사용하는 용도 (게이밍 노트북 및 고성능 작업용)
        """)
        
    with tab3:
        st.subheader("용도별 추천 예산 가이드")
        st.markdown("""
        - **사무/인강용**: 70만 원 ~ 120만 원 선
        - **대학생 과제/일반용**: 100만 원 ~ 170만 원 선
        - **고사양 게이밍 / 영상 편집용**: 150만 원 ~ 250만 원 이상
        """)

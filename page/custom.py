import pandas as pd
import streamlit as st

# 페이지 설정 (사이드바 확장 등 와이드 레이아웃 적용)
st.set_page_config(
    page_title="맞춤 노트북 추천", page_icon="🔍", layout="wide"
)

# -------------------------------------------------------------------------
# [데이터 준비] 메인 페이지와 동일한 노트북 데이터셋
# -------------------------------------------------------------------------


@st.cache_data
def load_data():
  data = {
      "모델명": [
          "삼성전자 갤럭시북4 프로",
          "LG전자 그램 16",
          "Apple 맥북 에어 15 (M3)",
          "에이수스 ROG 제피러스 G14",
          "레노버 100e 크롬북 Gen 4",
          "HP 오멘 16",
          "MSI 사이보그 15",
          "애플 맥북 프로 14 (M3 Pro)",
      ],
      "브랜드": [
          "삼성",
          "LG",
          "Apple",
          "ASUS",
          "Lenovo",
          "HP",
          "MSI",
          "Apple",
      ],
      "가격(만원)": [165, 170, 189, 230, 35, 180, 115, 260],
      "용도": [
          "사무/인강용",
          "사무/인강용",
          "사무/인강용",
          "게이밍/작업용",
          "사무/인강용",
          "게이밍/작업용",
          "게이밍/작업용",
          "게이밍/작업용",
      ],
      "CPU": [
          "Intel Core Ultra 5",
          "Intel Core Ultra 5",
          "Apple M3",
          "AMD Ryzen 9",
          "Intel N100",
          "Intel i7-14700HX",
          "Intel i5-12450H",
          "Apple M3 Pro",
      ],
      "RAM(GB)": [16, 16, 16, 32, 4, 16, 16, 18],
      "무게(kg)": [1.23, 1.19, 1.51, 1.50, 1.45, 2.32, 1.98, 1.61],
      "화면크기": [
          "14인치",
          "16인치",
          "15.3인치",
          "14인치",
          "14인치",
          "16.1인치",
          "15.6인치",
          "14.2인치",
      ],
  }
  return pd.DataFrame(data)


df = load_data()

# -------------------------------------------------------------------------
# 상단 타이틀 영역
# -------------------------------------------------------------------------
st.title("🎯 상세 조건 맞춤 노트북 추천")
st.markdown(
    "원하시는 예산, 브랜드, 성능 조건을 사이드바에서 선택하시면 꼭 맞는"
    " 노트북을 추천해 드립니다."
)
st.divider()

# -------------------------------------------------------------------------
# 사이드바 세부 필터 구성
# -------------------------------------------------------------------------
st.sidebar.header("🎛️ 맞춤 필터 설정")

# 1. 예산 슬라이더
min_p, max_p = int(df["가격(만원)"].min()), int(df["가격(만원)"].max())
selected_price = st.sidebar.slider(
    "예산 범위 (만원)",
    min_value=min_p,
    max_value=max_p,
    value=(min_p, max_p),
    step=10,
)

# 2. 용도 선택 다중 체크박스 또는 셀렉트박스
selected_purpose = st.sidebar.multiselect(
    "희망 용도",
    options=df["용도"].unique(),
    default=df["용도"].unique(),  # 기본적으로 전체 선택
)

# 3. 브랜드 선택
selected_brands = st.sidebar.multiselect(
    "선호 브랜드",
    options=df["브랜드"].unique(),
    default=df["브랜드"].unique(),
)

# 4. 최소 RAM 요구사항
selected_ram = st.sidebar.selectbox("최소 RAM (GB)", options=[4, 16, 32], index=0)

# 5. 최대 무게 제한 슬라이더
max_w = float(df["무게(kg)"].max())
selected_weight = st.sidebar.slider(
    "최대 허용 무게 (kg)", min_value=1.0, max_value=max_w, value=max_w, step=0.1
)

# -------------------------------------------------------------------------
# 필터 데이터 적용 로직
# -------------------------------------------------------------------------
filtered_df = df[
    (df["가격(만원)"].between(selected_price[0], selected_price[1]))
    & (df["용도"].isin(selected_purpose))
    & (df["브랜드"].isin(selected_brands))
    & (df["RAM(GB)"] >= selected_ram)
    & (df["무게(kg)"] <= selected_weight)
]

# -------------------------------------------------------------------------
# 결과 출력 영역
# -------------------------------------------------------------------------
st.subheader(f"✨ 조건에 맞는 추천 모델 ({len(filtered_df)}개 발견)")

if not filtered_df.empty:
  # 1. 표 형태로 전체 보기 제공
  with st.expander("📊 데이터 테이블로 한눈에 보기", expanded=True):
    st.dataframe(filtered_df, use_container_width=True)

  st.markdown("### 🛒 추천 모델 상세 카드")

  # 2. 카드 형태의 UI로 개별 노트북 강조 표시
  for idx, row in filtered_df.iterrows():
    with st.container():
      col1, col2, col3 = st.columns([1, 2, 1])

      with col1:
        st.markdown(f"### **{row['브랜드']}**")
        st.write(f"🏷️ **{row['모델명']}**")

      with col2:
        st.write(f"💰 **가격**: {row['가격(만원)']}만원")
        st.write(
            f"⚙️ **CPU**: {row['CPU']} | **RAM**: {row['RAM(GB)']}GB"
        )
        st.write(
            f"⚖️ **무게**: {row['무게(kg)']}kg | **화면**: {row['화면크기']}"
        )

      with col3:
        st.write("")
        # 상세 보기 버튼이나 구매 링크 연결 시뮬레이션
        if st.button(
            "상세 스펙 확인", key=f"detail_{idx}"
        ):  # 고유 키 부여
          st.success(f"'{row['모델명']}' 선택됨!")

      st.divider()
else:
  st.warning(
      "⚠️ 선택하신 조건에 일치하는 노트북이 없습니다. 사이드바의 필터 범위를"
      " 조금 더 넓혀보세요!"
  )

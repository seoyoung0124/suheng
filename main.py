import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="노트북 추천 사이트", page_icon="💻", layout="wide"
)

# -------------------------------------------------------------------------
# [데이터 준비] 가상의 노트북 데이터셋
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
st.title("💻 나에게 딱 맞는 노트북 추천 사이트")
st.markdown(
    "복잡한 노트북 스펙 속에서 헤매지 마세요! 예산과 용도에 맞는 최적의"
    " 모델을 찾아드립니다."
)
st.divider()

# -------------------------------------------------------------------------
# 탭 구성 (멀티탭 인터페이스로 하나의 파일에서 깔끔하게 페이지 분리 효과)
# -------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 홈 & 퀵서치", "🔍 맞춤 추천", "📊 스펙 비교", "💬 구매 가이드"]
)

# =========================================================================
# [탭 1] 홈 & 퀵서치
# =========================================================================
with tab1:
  st.subheader("🚀 빠른 맞춤 검색")
  col1, col2 = st.columns(2)

  with col1:
    q_purpose = st.selectbox(
        "주요 용도를 선택하세요",
        ["전체", "사무/인강용", "게이밍/작업용"],
        key="quick_purpose",
    )
  with col2:
    q_max_price = st.slider(
        "최대 예산 (만원)",
        min_value=30,
        max_value=300,
        value=200,
        step=10,
        key="quick_price",
    )

  # 퀵서치 필터링 적용 (오류 수정 완료 부분)
  q_df = df.copy()
  if q_purpose != "전체":
    q_df = q_df[q_df["용도"] == q_purpose]
  q_df = q_df[q_df["가격(만원)"] <= q_max_price]

  st.markdown(f"### 🔍 검색 결과 ({len(q_df)}개 모델 발견)")
  if not q_df.empty:
    st.dataframe(q_df, use_container_width=True)
  else:
    st.info("조건에 일치하는 노트북이 없습니다. 예산이나 용도를 조정해 보세요.")

  st.divider()
  st.subheader("🔥 이번 주 인기 추천 모델 TOP 3")
  top3 = df.head(3)
  cols = st.columns(3)
  for idx, row in top3.iterrows():
    with cols[idx]:
      st.markdown(f"**{row['모델명']}**")
      st.write(f"💰 가격: {row['가격(만원)']}만원")
      st.write(f"⚙️ CPU: {row['CPU']}")
      st.write(f"⚖️ 무게: {row['무게(kg)']}kg")

# =========================================================================
# [탭 2] 맞춤 추천 (상세 필터)
# =========================================================================
with tab2:
  st.subheader("🎯 상세 조건 맞춤 추천")
  st.write("사이드바 또는 아래 설정으로 정밀하게 노트북을 찾아보세요.")

  st.sidebar.header("🔍 상세 필터 옵션")
  s_brand = st.sidebar.multiselect(
      "브랜드 선택", options=df["브랜드"].unique(), default=df["브랜드"].unique()
  )
  s_min_ram = st.sidebar.selectbox("최소 RAM 용량", [4, 16, 32], index=1)
  s_max_weight = st.sidebar.slider(
      "최대 무게 제한 (kg)", min_value=1.0, max_value=3.0, value=2.5, step=0.1
  )

  # 상세 필터 적용
  filtered_df = df[
      (df["브랜드"].isin(s_brand))
      & (df["RAM(GB)"] >= s_min_ram)
      & (df["무게(kg)"] <= s_max_weight)
  ]

  st.markdown(f"### 📋 필터링된 추천 목록 ({len(filtered_df)}개)")
  st.dataframe(filtered_df, use_container_width=True)

# =========================================================================
# [탭 3] 스펙 비교
# =========================================================================
with tab3:
  st.subheader("📊 노트북 스펙 비교함")
  st.write("비교하고 싶은 모델을 2개 이상 선택해 주세요.")

  selected_models = st.multiselect(
      "비교할 모델 선택",
      options=df["모델명"].tolist(),
      default=df["모델명"].tolist()[:2],
  )

  if selected_models:
    compare_df = df[df["모델명"].isin(selected_models)]
    # 표 형태를 보기 좋게 전치(T)해서 비교하기 쉽게 구성
    st.table(compare_df.set_index("모델명"))
  else:
    st.warning("비교할 모델을 최소 1개 이상 선택해 주세요.")

# =========================================================================
# [탭 4] 구매 가이드 & 용어 사전
# =========================================================================
with tab4:
  st.subheader("💡 노트북 구매 가이드 및 기초 용어")

  with st.expander("📌 CPU란 무엇인가요? (인텔 vs AMD vs 애플실리콘)"):
    st.write(
        "- **인텔/AMD**: 범용성이 좋고 윈도우(Windows) 운영체제와 호환성이"
        " 뛰어납니다.\n- **애플 M시리즈(M2, M3 등)**: 맥북에 들어가는 칩으로,"
        " 뛰어난 전력 효율과 긴 배터리 타임이 장점입니다."
    )

  with st.expander("📌 RAM(램)은 다소 큰 게 좋을까요?"):
    st.write(
        "- **8GB**: 문서 작업, 웹서핑, 간단한 인강용으로 최소한의 용량입니다.\n-"
        " **16GB 이상**: 다중 작업(멀티태스킹), 대학생 과제, 가벼운 게임 및"
        " 영상 편집을 하신다면 강력히 추천합니다."
    )

  with st.expander("📌 무게 기준은 어떻게 잡아야 할까요?"):
    st.write(
        "- **1.5kg 미만**: 매일 가방에 넣고 등하교/출퇴근하는 분들께 추천 (휴대성"
        " 최우선)\n- **1.5kg ~ 2.0kg**: 가끔 들고 다니며 주로 책상 위에 두고"
        " 쓰는 용도\n- **2.0kg 이상**: 고사양 게이밍 및 크리에이터 작업용 (주로"
        " 거치용)"
    )

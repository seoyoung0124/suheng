import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 (와이드 레이아웃 적용)
st.set_page_config(
    page_title="블루투스 멀티포인트 배터리 시뮬레이터",
    page_icon="🔋",
    layout="wide"
)

# 2. 사이드바 - 공통 설정 패널
st.sidebar.header("⚙️ 스마트폰 환경 설정")
battery_capacity = st.sidebar.slider("스마트폰 배터리 총 용량 (mAh)", 3000, 5000, 4000, 100)
bt_version = st.sidebar.selectbox(
    "블루투스 버전 선택",
    ["Bluetooth 4.2", "Bluetooth 5.0", "Bluetooth 5.3 (최신)"]
)

# 블루투스 버전에 따른 전력 효율 계수 설정
version_coefficient = {"Bluetooth 4.2": 1.4, "Bluetooth 5.0": 1.1, "Bluetooth 5.3 (최신)": 1.0}
eff_factor = version_coefficient[bt_version]

# 3. 메인 타이틀 및 소개
st.title("🔋 블루투스 멀티포인트 연결 시 배터리 소모 예측 앱")
st.markdown("스마트폰에 여러 블루투스 기기를 동시에 연결했을 때, 백그라운드 통신량과 기기별 부하에 따른 **배터리 잔량 감소 추이**를 시뮬레이션하는 웹 앱입니다.")
st.markdown("---")

# 4. 상단 탭(Tab) 메뉴 구성 (페이지 전환 역할)
tab1, tab2, tab3 = st.tabs([
    "📊 실시간 배터리 시뮬레이터", 
    "📚 멀티포인트 기술 원리", 
    "💡 전력 절약 가이드"
])

# ==========================================
# [Tab 1] 실시간 배터리 소모 시뮬레이터 (메인 기능)
# ==========================================
with tab1:
    st.subheader("🛠️ 연결된 블루투스 기기 설정 (멀티포인트)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_earphone = st.checkbox("무선 이어폰 (음악 스트리밍 중)", value=True)
        earphone_codec = st.selectbox("오디오 코덱 선택", ["SBC", "AAC", "LDAC (고음질)"])
        
        use_watch = st.checkbox("스마트워치 (헬스케어 동기화)", value=True)
        
    with col2:
        use_keyboard = st.checkbox("블루투스 키보드 / 마우스", value=False)
        use_gamepad = st.checkbox("블루투스 게임 패드 (고주사율)", value=False)

    st.markdown("---")
    st.subheader("📉 시간 경과에 따른 배터리 잔량 시뮬레이션 (12시간 기준)")

    # 시뮬레이션 데이터 계산 로직
    hours = np.arange(0, 13, 1)  션 시간 (0~12시간)
    
    # 기본 소모율 (화면 켜짐/기본 시스템 둥작)
    base_drain_per_hour = 350 * (4000 / battery_capacity) 
    
    # 기기별 추가 시간당 소모 전력 (mAh) 계산
    extra_drain = 0
    if use_earphone:
        codec_add = {"SBC": 40, "AAC": 50, "LDAC (고음질 곡)": 80}
        extra_drain += codec_add[earphone_codec]
    if use_watch:
        extra_drain += 30
    if use_keyboard:
        extra_drain += 15
    if use_gamepad:
        extra_drain += 60

    # 멀티포인트 오버헤드 (기기가 늘어날수록 통신 프로토콜 유지 전력 증가)
    active_devices_count = sum([use_earphone, use_watch, use_keyboard, use_gamepad])
    overhead = (active_devices_count ** 1.3) * 20 if active_devices_count > 1 else 0
    
    total_hourly_drain = (base_drain_per_hour + extra_drain + overhead) * eff_factor

    # 시간별 배터리 잔량 계산 (%)
    battery_levels = []
    for h in hours:
        remaining_mAh = battery_capacity - (total_hourly_drain * h)
        remaining_pct = max(0, (remaining_mAh / battery_capacity) * 100)
        battery_levels.append(round(remaining_pct, 1))

    # 데이터프레임 생성 및 차트 렌더링
    df_chart = pd.DataFrame({
        "시간 (Hour)": hours,
        "배터리 잔량 (%)": battery_levels
    })
    df_chart.set_index("시간 (Hour)", inplace=True)

    st.line_chart(df_chart, height=350)

    # 주요 지표 요약 (Metric)
    m_col1, m_col2, m_col3 = st.columns(3)
    
    # 방전될 때까지 걸리는 예상 시간 계산
    zero_indices = [i for i, val in enumerate(battery_levels) if val == 0]
    if zero_indices:
        estimated_hours = zero_indices[0]
        life_str = f"약 {estimated_hours}시간"
    else:
        life_str = "12시간 이상 유지"
        
    m_col1.metric("동시 연결 기기 수", f"{active_devices_count}개")
    m_col2.metric("시간당 예상 소모 전력", f"{int(total_hourly_drain)} mAh/h")
    m_col3.metric("예상 최대 사용 가능 시간", life_str)


# ==========================================
# [Tab 2] 멀티포인트 기술 원리 및 분석 리포트
# ==========================================
with tab2:
    st.subheader("📖 멀티포인트(Multipoint) 통신 원리")
    st.markdown("""
    * **블루투스 피코넷(Piconet):** 하나의 마스터 기기(스마트폰)가 여러 슬레이브 기기(이어폰, 워치 등)와 동시에 연결을 유지하는 네트워크 구조입니다.
    * **패킷 교환 주기 (Polling Interval):** 기기가 많아질수록 스마트폰의 블루투스 칩셋이 각 기기와 데이터를 주고받기 위해 인터럽트와 폴링 주기를 바쁘게 오가며 **오버헤드(Overhead)**가 발생합니다.
    * **버전별 효율 차이:** 블루투스 5.0 이상부터는 저에너지(BLE) 기술과 데이터 전송 효율이 개선되어 동일한 멀티포인트 환경에서도 전력 소모가 줄어듭니다.
    """)
    
    st.info("💡 **생기부 작성 팁:** 이 시뮬레이터는 기기 개수 증가에 따른 지수 함수적 부하 증가 모델을 적용하여 백그라운드 전력 소모의 상관관계를 분석했습니다.")


# ==========================================
# [Tab 3] 스마트한 블루투스 전력 절약 가이드
# ==========================================
with tab3:
    st.subheader("💡 맞춤형 전력 절약 피드백")
    
    if active_devices_count >= 3:
        st.error("⚠️ **주의:** 현재 3개 이상의 블루투스 기기가 동시에 연결되어 있습니다. 스마트폰 배터리 소모 속도가 평소보다 훨씬 빠릅니다.")
    elif active_devices_count == 0:
        st.warning("⚠️ 연결된 블루투스 기기가 없습니다. 시뮬레이터를 위해 기기를 체크해 보세요!")
    else:
        st.success("✨ **안전:** 적절한 수의 블루투스 기기가 연결되어 있어 효율적인 전력 관리가 가능합니다.")
        
    st.markdown("""
    ### 🔋 배터리 수명을 지키는 3가지 팁
    1. **미사용 기기 연결 해제:** 사용하지 않는 스마트워치나 키보드는 백그라운드 연결을 끊어두세요.
    2. **고음질 코덱 조절:** 대중교통 등 소음이 심한 곳에서는 전력 소모가 큰 고음질 코덱(LDAC 등) 대신 표준 코덱을 사용하는 것이 유리합니다.
    3. **최신 블루투스 버전 유지:** 가급적 블루투스 5.0 이상을 지원하는 주변 기기를 사용하는 것이 전력 효율에 도움을 줍니다.
    """)

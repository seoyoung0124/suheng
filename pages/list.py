
import streamlit as st
from datetime import datetime, date

st.set_page_config(
    page_title="To-do 리스트",
    page_icon="📝",
    layout="wide"
)

# -----------------------------
# 페이지 디자인
# -----------------------------
st.title("📝 To-do 리스트")
st.write("캘린더에 등록한 일정을 확인하고 할 일을 관리해 보세요.")
st.divider()

# 캘린더 페이지에서 저장한 일정 불러오기
schedules = st.session_state.get("schedules", [])

# 일정 데이터가 리스트 형태가 아닌 경우 처리
if not isinstance(schedules, list):
    st.error("일정 데이터 형식이 올바르지 않습니다.")
    st.stop()


# -----------------------------
# 일정 데이터 정리
# -----------------------------
def get_schedule_date(item):
    """일정의 날짜를 정렬할 수 있는 형태로 변환"""
    value = item.get("date", item.get("날짜", ""))

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        for fmt in (
            "%Y-%m-%d",
            "%Y.%m.%d",
            "%Y/%m/%d",
            "%Y년 %m월 %d일"
        ):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue

    return date.max


def get_schedule_title(item):
    """일정 제목 가져오기"""
    return (
        item.get("title")
        or item.get("제목")
        or item.get("일정")
        or item.get("내용")
        or item.get("name")
        or "제목 없는 일정"
    )


def get_schedule_time(item):
    """일정 시간 가져오기"""
    return (
        item.get("time")
        or item.get("시간")
        or item.get("start_time")
        or ""
    )


# 날짜순으로 정렬
sorted_schedules = sorted(
    schedules,
    key=lambda item: (
        get_schedule_date(item),
        str(get_schedule_time(item))
    )
    if isinstance(item, dict)
    else (date.max, "")
)

# 잘못된 데이터 제외
sorted_schedules = [
    item for item in sorted_schedules
    if isinstance(item, dict)
]


# -----------------------------
# 할 일 목록 표시
# -----------------------------
if not sorted_schedules:
    st.info(
        "아직 등록된 일정이 없어요. "
        "캘린더 페이지에서 일정을 먼저 추가해 주세요."
    )

else:
    # 할 일 완료 상태 저장
    if "todo_completed" not in st.session_state:
        st.session_state["todo_completed"] = {}

    completed = st.session_state["todo_completed"]

    # 전체 진행 상황
    total = len(sorted_schedules)
    done = sum(
        1 for i, item in enumerate(sorted_schedules)
        if completed.get(str(i), False)
    )

    progress = done / total if total else 0

    st.subheader("오늘의 진행 상황")
    st.progress(progress)
    st.write(f"완료한 할 일: **{done} / {total}개**")

    st.divider()

    # 날짜별로 일정 그룹화
    grouped = {}

    for item in sorted_schedules:
        schedule_date = get_schedule_date(item)
        grouped.setdefault(schedule_date, []).append(item)

    for schedule_date, items in grouped.items():

        if schedule_date == date.max:
            heading = "📌 날짜 미지정"
        else:
            heading = f"📅 {schedule_date.strftime('%Y년 %m월 %d일')}"

            if schedule_date == date.today():
                heading += " (오늘)"

        st.subheader(heading)

        for item in items:
            title = get_schedule_title(item)
            time_text = get_schedule_time(item)
            description = (
                item.get("description")
                or item.get("설명")
                or item.get("메모")
                or ""
            )

            # 일정마다 고유한 체크박스 키 생성
            schedule_id = str(
                item.get("id")
                or item.get("일정_id")
                or f"{schedule_date}_{time_text}_{title}"
            )

            checkbox_key = f"todo_{schedule_id}"

            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = completed.get(
                    schedule_id, False
                )

            col1, col2 = st.columns([5, 1])

            with col1:
                checked = st.checkbox(
                    title,
                    key=checkbox_key
                )

            with col2:
                if time_text:
                    st.caption(f"🕒 {time_text}")

            # 완료 여부 저장
            completed[schedule_id] = checked

            if description:
                st.caption(f"　{description}")

            if checked:
                st.caption("　✅ 완료")

            st.divider()

    # 전체 완료 처리
    if st.button("모든 할 일 완료 처리", use_container_width=True):
        for item in sorted_schedules:
            schedule_date = get_schedule_date(item)
            title = get_schedule_title(item)
            time_text = get_schedule_time(item)

            schedule_id = str(
                item.get("id")
                or item.get("일정_id")
                or f"{schedule_date}_{time_text}_{title}"
            )

            st.session_state[f"todo_{schedule_id}"] = True
            completed[schedule_id] = True

        st.rerun()

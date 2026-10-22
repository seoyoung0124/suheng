import json
import uuid
from datetime import date, datetime
from pathlib import Path

import streamlit as st
from streamlit_calendar import calendar


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="하루결 | 일정 관리",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_FILE = Path("events.json")

CATEGORIES = [
    "수행평가", "시험", "동아리", "개인일정",
    "과제", "학교행사", "기타",
]

IMPORTANCE_COLORS = {
    "상": "#F87171",
    "중": "#FACC15",
    "하": "#4ADE80",
    "없음": "#C4B5FD",
}
PERSONAL_COLOR = "#7DD3FC"


# =========================================================
# 데이터 검증 및 저장
# =========================================================
def normalize_date(value):
    """YYYY-MM-DD 또는 ISO 날짜/시간 문자열을 날짜로 정규화한다."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except (ValueError, TypeError):
            return None


def normalize_event(raw):
    """오래된 형식이나 일부 필드가 빠진 일정도 안전한 형식으로 변환한다."""
    if not isinstance(raw, dict):
        return None

    # 예전 데이터가 date 대신 start 또는 start_date를 썼을 경우도 처리
    event_date = normalize_date(
        raw.get("date") or raw.get("start") or raw.get("start_date")
    )
    if not event_date:
        return None

    raw_categories = raw.get("categories", [])
    if isinstance(raw_categories, str):
        raw_categories = [raw_categories]
    if not isinstance(raw_categories, list):
        raw_categories = []

    categories = [
        str(category) for category in raw_categories
        if str(category) in CATEGORIES
    ]

    importance = str(raw.get("importance", "없음"))
    if importance not in IMPORTANCE_COLORS:
        importance = "없음"

    return {
        "id": str(raw.get("id") or uuid.uuid4()),
        "date": event_date,
        "title": str(raw.get("title") or ""),
        "description": str(raw.get("description") or ""),
        "importance": importance,
        "categories": categories,
    }


def load_events():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):

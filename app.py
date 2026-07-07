import streamlit as st
import json
import uuid
from datetime import date, datetime, timedelta
import calendar

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="CertAlert – 화장품 ODM RA 일정 트래커",
    page_icon="📅",
    layout="wide",
)

# ── 상수 ──────────────────────────────────────────────────────
TYPE_ICON  = {"export": "🌍", "submit": "📋", "test": "🧪"}
TYPE_LABEL = {"export": "수출국 등록", "submit": "고객사 제출", "test": "시험 완료"}

DEFAULT_ITEMS = [
    {"id": "seed-1",  "product": "리페어 앰플",         "type": "export", "dueDate": "2026-06-30"},
    {"id": "seed-2",  "product": "비타민C 부스터 세럼", "type": "export", "dueDate": "2026-07-10"},
    {"id": "seed-3",  "product": "글로우 수분크림",      "type": "export", "dueDate": "2026-07-15"},
    {"id": "seed-4",  "product": "클렌징폼 딥클린",      "type": "submit", "dueDate": "2026-08-01"},
    {"id": "seed-5",  "product": "브라이트닝 세럼",      "type": "submit", "dueDate": "2026-07-25"},
    {"id": "seed-6",  "product": "선크림 SPF50",         "type": "test",   "dueDate": "2026-08-10"},
    {"id": "seed-7",  "product": "안티에이징 아이크림",  "type": "export", "dueDate": "2026-09-05"},
    {"id": "seed-8",  "product": "모이스처 로션",        "type": "submit", "dueDate": "2026-09-28"},
    {"id": "seed-9",  "product": "톤업크림",             "type": "test",   "dueDate": "2026-10-20"},
    {"id": "seed-10", "product": "콜라겐 마스크팩",      "type": "test",   "dueDate": "2026-12-15"},
]

# ── 스타일 ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 배경 */
.stApp { background: #F7F9FB; }

/* 헤더 */
.cert-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 0 16px 0; border-bottom: 2px solid #e5e7eb; margin-bottom: 20px;
}
.cert-title { color: #1E3A5F; font-size: 22px; font-weight: 700; margin: 0; }
.cert-sub   { color: #6b7280; font-size: 13px; margin: 2px 0 0; }

/* 알림 배너 */
.alert-banner {
    background: #fdecec; color: #e53e3e; border: 1px solid #f8c9c9;
    border-radius: 8px; padding: 12px 16px; font-size: 14px;
    font-weight: 600; margin-bottom: 16px;
}

/* 달력 */
.cal-wrapper { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 20px; }
.cal-nav     { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 12px; }
.cal-month   { font-size: 16px; font-weight: 700; color: #1E3A5F; min-width: 120px; text-align: center; }
.cal-grid    { display: grid; grid-template-columns: repeat(7,1fr); gap: 3px; }
.cal-dow     { text-align: center; font-size: 12px; font-weight: 700; color: #6b7280; padding: 4px 0; }
.cal-dow.sun { color: #e53e3e; }
.cal-dow.sat { color: #1c7ed6; }
.cal-cell    {
    min-height: 80px; border: 1px solid #e5e7eb; border-radius: 6px;
    padding: 4px; font-size: 11px; overflow: hidden; background: #fff;
}
.cal-cell.other  { background: #fafafa; color: #c3c7cf; }
.cal-cell.today  { border: 2px solid #1E3A5F; }
.cal-num         { font-size: 11px; margin-bottom: 3px; color: #6b7280; }
.cal-num.sun     { color: #e53e3e; }
.cal-num.sat     { color: #1c7ed6; }
.cal-cell.today .cal-num { color: #1E3A5F; font-weight: 700; }
.badge {
    display: block; font-size: 10px; font-weight: 700; border-radius: 4px;
    padding: 1px 4px; margin-bottom: 2px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; color: #fff;
}
.badge.red    { background: #e53e3e; }
.badge.yellow { background: #d69e0a; }
.badge.green  { background: #2f9e44; }
.badge.gray   { background: #868e96; }

/* 목록 행 */
.list-row {
    display: grid; grid-template-columns: 100px 1fr 120px 80px;
    align-items: center; gap: 8px; padding: 10px 8px;
    border-bottom: 1px solid #e5e7eb; font-size: 14px;
    background: #fff; cursor: pointer;
}
.list-row:hover { background: #eaf3f3; }
.pill {
    display: inline-block; font-size: 12px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px; color: #fff;
    text-align: center;
}
.pill.red    { background: #e53e3e; }
.pill.yellow { background: #d69e0a; }
.pill.green  { background: #2f9e44; }
.pill.gray   { background: #868e96; }

/* Streamlit 기본 버튼 오버라이드 */
div[data-testid="stButton"] > button {
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


# ── 세션 초기화 ──────────────────────────────────────────────
if "items" not in st.session_state:
    st.session_state["items"] = [dict(it) for it in DEFAULT_ITEMS]
if "view_year" not in st.session_state:
    st.session_state.view_year = date.today().year
if "view_month" not in st.session_state:
    st.session_state.view_month = date.today().month
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None


# ── 헬퍼 함수 ──────────────────────────────────────────────
def dday_of(due_str: str) -> int:
    due = datetime.strptime(due_str, "%Y-%m-%d").date()
    return (due - date.today()).days

def urgency_of(d: int) -> str:
    if d < 0:  return "gray"
    if d <= 30: return "red"
    if d <= 90: return "yellow"
    return "green"

def dday_label(d: int) -> str:
    if d < 0:  return f"만료 D+{abs(d)}"
    if d == 0: return "D-day"
    return f"D-{d}"


# ── 헤더 ──────────────────────────────────────────────────────
st.markdown("""
<div class="cert-header">
  <div>
    <p class="cert-title">📅 CertAlert</p>
    <p class="cert-sub">화장품 ODM RA 일정 트래커</p>
  </div>
</div>
""", unsafe_allow_html=True)

col_title, col_add = st.columns([6, 1])
with col_add:
    if st.button("＋ 항목 추가", use_container_width=True):
        st.session_state.show_form = True
        st.session_state.editing_id = None


# ── 알림 배너 ──────────────────────────────────────────────
items = st.session_state["items"]
urgent  = sum(1 for it in items if 0 <= dday_of(it["dueDate"]) <= 30)
expired = sum(1 for it in items if dday_of(it["dueDate"]) < 0)
if urgent or expired:
    parts = []
    if expired: parts.append(f"만료 {expired}건")
    if urgent:  parts.append(f"긴급(D-30 이내) {urgent}건")
    st.markdown(f'<div class="alert-banner">🚨 {" · ".join(parts)} 확인이 필요합니다.</div>',
                unsafe_allow_html=True)


# ── 항목 추가 / 수정 폼 ──────────────────────────────────────
if st.session_state.show_form:
    editing = next((it for it in items if it["id"] == st.session_state.editing_id), None)
    with st.container(border=True):
        st.subheader("항목 수정" if editing else "항목 추가")
        with st.form("item_form", clear_on_submit=True):
            product = st.text_input("제품명", value=editing["product"] if editing else "", max_chars=40)
            type_val = st.selectbox(
                "항목 종류",
                options=list(TYPE_LABEL.keys()),
                format_func=lambda k: f"{TYPE_ICON[k]} {TYPE_LABEL[k]}",
                index=list(TYPE_LABEL.keys()).index(editing["type"]) if editing else 0,
            )
            due_date = st.date_input(
                "기한 날짜",
                value=datetime.strptime(editing["dueDate"], "%Y-%m-%d").date() if editing else date.today(),
            )

            col_del, col_cancel, col_save = st.columns([2, 1, 1])
            with col_save:
                submitted = st.form_submit_button("💾 저장", use_container_width=True, type="primary")
            with col_cancel:
                cancelled = st.form_submit_button("취소", use_container_width=True)
            with col_del:
                deleted = st.form_submit_button("🗑 삭제", use_container_width=True,
                                                disabled=(editing is None))

        if submitted and product and due_date:
            data = {"product": product, "type": type_val, "dueDate": str(due_date)}
            if editing:
                idx = next(i for i, it in enumerate(items) if it["id"] == editing["id"])
                items[idx] = {**items[idx], **data}
            else:
                items.append({"id": str(uuid.uuid4()), **data})
            st.session_state["items"] = items
            st.session_state.show_form = False
            st.session_state.editing_id = None
            st.rerun()

        if cancelled:
            st.session_state.show_form = False
            st.session_state.editing_id = None
            st.rerun()

        if deleted and editing:
            st.session_state["items"] = [it for it in items if it["id"] != editing["id"]]
            st.session_state.show_form = False
            st.session_state.editing_id = None
            st.rerun()


# ── 달력 ──────────────────────────────────────────────────────
vy, vm = st.session_state.view_year, st.session_state.view_month
today  = date.today()

nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 3, 1, 1])
with nav1:
    if st.button("‹", use_container_width=True, key="prev"):
        if vm == 1: st.session_state.view_year -= 1; st.session_state.view_month = 12
        else:       st.session_state.view_month -= 1
        st.rerun()
with nav2:
    if st.button("오늘", use_container_width=True, key="today_btn"):
        st.session_state.view_year  = today.year
        st.session_state.view_month = today.month
        st.rerun()
with nav3:
    st.markdown(f"<p style='text-align:center;font-weight:700;font-size:16px;color:#1E3A5F;margin:6px 0'>"
                f"{vy}년 {vm}월</p>", unsafe_allow_html=True)
with nav5:
    if st.button("›", use_container_width=True, key="next"):
        if vm == 12: st.session_state.view_year += 1; st.session_state.view_month = 1
        else:        st.session_state.view_month += 1
        st.rerun()

# 날짜별 아이템 매핑
items_by_date: dict[str, list] = {}
for it in items:
    items_by_date.setdefault(it["dueDate"], []).append(it)

# 달력 HTML 생성
first_weekday, days_in_month = calendar.monthrange(vy, vm)
# Python: Monday=0 … Sunday=6 → 일요일 시작으로 변환
start_offset = (first_weekday + 1) % 7

cal_html = ['<div class="cal-grid">']
for dow, name in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
    cls = " sun" if dow == 0 else (" sat" if dow == 6 else "")
    cal_html.append(f'<div class="cal-dow{cls}">{name}</div>')

for cell in range(42):
    day_num = cell - start_offset + 1
    if day_num < 1:
        cell_date = date(vy, vm, 1) - timedelta(days=-day_num)
        other = True
    elif day_num > days_in_month:
        cell_date = date(vy, vm, days_in_month) + timedelta(days=day_num - days_in_month)
        other = True
    else:
        cell_date = date(vy, vm, day_num)
        other = False

    is_today = (cell_date == today)
    dow = cell_date.weekday()  # Mon=0…Sun=6
    dow_sun_start = (dow + 1) % 7  # Sun=0…Sat=6

    cell_cls = "cal-cell"
    if other:   cell_cls += " other"
    if is_today: cell_cls += " today"

    num_cls = "cal-num"
    if dow_sun_start == 0: num_cls += " sun"
    if dow_sun_start == 6: num_cls += " sat"

    date_str = str(cell_date)
    badges_html = ""
    for it in items_by_date.get(date_str, []):
        d = dday_of(it["dueDate"])
        color = urgency_of(d)
        label = f"{TYPE_ICON[it['type']]} {it['product']}"
        badges_html += f'<span class="badge {color}" title="{it["product"]} · {TYPE_LABEL[it["type"]]} · {dday_label(d)}">{label}</span>'

    cal_html.append(
        f'<div class="{cell_cls}">'
        f'<div class="{num_cls}">{cell_date.day}</div>'
        f'{badges_html}</div>'
    )

cal_html.append("</div>")
st.markdown('<div class="cal-wrapper">' + "".join(cal_html) + "</div>", unsafe_allow_html=True)


# ── 전체 목록 ──────────────────────────────────────────────────
st.subheader("전체 항목")
search = st.text_input("검색", placeholder="제품명 또는 종류로 검색…", label_visibility="collapsed")

sorted_items = sorted(items, key=lambda it: dday_of(it["dueDate"]))
if search:
    kw = search.lower()
    sorted_items = [it for it in sorted_items
                    if kw in it["product"].lower() or kw in TYPE_LABEL[it["type"]].lower()]

if not sorted_items:
    st.markdown('<p style="color:#6b7280;text-align:center;padding:20px 0">등록된 항목이 없습니다.</p>',
                unsafe_allow_html=True)
else:
    # 헤더 행
    st.markdown("""
    <div class="list-row" style="font-weight:700;background:#f1f2f4;cursor:default">
      <span>종류</span><span>제품명</span><span>기한</span><span style="text-align:right">D-day</span>
    </div>""", unsafe_allow_html=True)

    for it in sorted_items:
        d = dday_of(it["dueDate"])
        color = urgency_of(d)
        label = dday_label(d)
        st.markdown(f"""
        <div class="list-row">
          <span>{TYPE_ICON[it['type']]} {TYPE_LABEL[it['type']]}</span>
          <span style="font-weight:700">{it['product']}</span>
          <span style="color:#6b7280">{it['dueDate']}</span>
          <span style="text-align:right"><span class="pill {color}">{label}</span></span>
        </div>""", unsafe_allow_html=True)

        # 수정 버튼 (목록 행 클릭 대신 버튼 제공)
        btn_col = st.columns([5, 1])[1]
        with btn_col:
            if st.button("수정", key=f"edit_{it['id']}", use_container_width=True):
                st.session_state.show_form = True
                st.session_state.editing_id = it["id"]
                st.rerun()

st.markdown("---")
st.caption("CertAlert · 화장품 ODM RA 일정 트래커 · Powered by Streamlit")

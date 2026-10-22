
import streamlit as st
from urllib.parse import urlparse

st.set_page_config(
    page_title="시각장애인 도우미",
    page_icon="🔔",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f8fc; }
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .hero {
        background: linear-gradient(135deg, #12345a, #176b87);
        color: white;
        text-align: center;
        padding: 32px 16px;
        border-radius: 20px;
        margin-bottom: 24px;
    }
    .hero h1 { color: white; font-size: 2.5rem; }
    .stButton button, .stLinkButton a {
        min-height: 56px;
        width: 100%;
        border-radius: 12px;
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def valid_url(url):
    """http:// 또는 https:// 주소인지 검사한다."""
    try:
        parsed = urlparse(url.strip())
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
            and "." in parsed.netloc
        )
    except (ValueError, AttributeError):
        return False


# 메인 제목
st.markdown(
    """
    <div class="hero">
        <h1>시각장애인 도우미</h1>
        <p>더 안전하고 편리한 이동을 위한 도우미</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("원하는 기능을 선택하세요")

# 링크 입력값 유지
if "bell_url" not in st.session_state:
    st.session_state.bell_url = ""
if "voice_url" not in st.session_state:
    st.session_state.voice_url = ""
if "vibrate_url" not in st.session_state:
    st.session_state.vibrate_url = ""

# 세 개의 기능 버튼
col1, col2, col3 = st.columns(3, gap="small")

with col1:
    if valid_url(st.session_state.bell_url):
        st.link_button("🔔 알림벨", st.session_state.bell_url)
    else:
        st.button("🔔 알림벨", disabled=True, key="bell_button")
        st.caption("링크 삽입")

with col2:
    if valid_url(st.session_state.voice_url):
        st.link_button("🗣️ 음성 주의", st.session_state.voice_url)
    else:
        st.button("🗣️ 음성 주의", disabled=True, key="voice_button")
        st.caption("링크 삽입")

with col3:
    if valid_url(st.session_state.vibrate_url):
        st.link_button("📳 진동 알림", st.session_state.vibrate_url)
    else:
        st.button("📳 진동 알림", disabled=True, key="vibrate_button")
        st.caption("링크 삽입")

st.divider()

st.subheader("기능별 링크 삽입")
st.write("연결할 페이지의 주소를 입력하세요. 입력한 주소는 아래 버튼에 적용됩니다.")

st.text_input(
    "알림벨 페이지 주소",
    key="bell_url",
    placeholder="https://blindmaid.streamlit.app/%EB%8F%84%EC%B0%A9%EC%A7%80%EC%84%A4%EC%A0%95",
    help="예: https://example.com/bell",
)

st.text_input(
    "음성 주의 페이지 주소",
    key="voice_url",
    placeholder="https://blindmaid.streamlit.app/%EC%86%8C%EB%A6%AC%EB%A1%9C_%EC%95%88%EB%82%B4%ED%95%98%EB%8A%94_%EA%B8%B8%EC%9E%A1%EC%9D%B4",
    help="예: https://example.com/voice",
)

st.text_input(
    "진동 알림 페이지 주소",
    key="vibrate_url",
    placeholder="https://blindmaid.streamlit.app/%EC%A3%BC%EB%B3%80%EC%97%90_%EB%B0%A9%ED%95%B4%EB%AC%BC%EC%9D%84_%EC%A7%84%EB%8F%99%EC%9C%BC%EB%A1%9C_%EC%95%8C%EB%A0%A4%EC%A4%8C.py",
    help="예: https://example.com/vibrate",
)

# 링크 입력 검증 결과
urls = [
    ("알림벨", st.session_state.bell_url),
    ("음성 주의", st.session_state.voice_url),
    ("진동 알림", st.session_state.vibrate_url),
]

invalid = [
    name for name, url in urls
    if url.strip() and not valid_url(url)
]

if invalid:
    st.error(
        "올바른 웹 주소를 입력해 주세요: "
        + ", ".join(invalid)
        + " (http:// 또는 https://로 시작해야 합니다.)"
    )

st.info(
    "링크를 입력하면 위의 해당 버튼이 활성화됩니다. "
    "주소를 비워 두면 버튼은 비활성화됩니다."
)

st.caption(
    "안내: 이 앱은 링크 연결용 메인 페이지입니다. "
    "실제 이동 안전을 위해 검증된 보행 안내 수단을 함께 이용하세요."
)


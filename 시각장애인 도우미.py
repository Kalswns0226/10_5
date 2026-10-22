
import streamlit as st

# --------------------------------------------------
# 페이지 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="Blind Maid - 시각장애인 도우미",
    page_icon="🦯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# 이동할 주소
# --------------------------------------------------
DESTINATION_URL = (
    "https://blindmaid.streamlit.app/"
    "%EB%8F%84%EC%B0%A9%EC%A7%80%EC%84%A4%EC%A0%95"
)

GUIDE_URL = (
    "http://blindmaid.streamlit.app/"
    "%EB%8F%84%EC%B0%A9%EC%A7%80%EC%84%A4%EC%A0%95"
)

VIBRATION_URL = (
    "https://blindmaid.streamlit.app/"
    "%EC%A3%BC%EB%B3%80%EC%97%90_"
    "%EB%B0%A9%ED%95%B4%EB%AC%BC%EC%9D%84_"
    "%EC%A7%84%EB%8F%99%EC%9C%BC%EB%A1%9C_"
    "%EC%95%8C%EB%A0%A4%EC%A4%8C.py"
)

# --------------------------------------------------
# 화면 디자인
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F3F7FC;
        color: #172B4D;
    }

    .block-container {
        max-width: 760px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: #12345A;
        padding: 30px 24px;
        border-radius: 20px;
        margin-bottom: 24px;
        text-align: center;
    }

    .hero h1 {
        color: #FFFFFF !important;
        font-size: 2.2rem;
        margin-bottom: 12px;
    }

    .hero p {
        color: #FFFFFF !important;
        font-size: 1.1rem;
        line-height: 1.7;
        margin-bottom: 0;
    }

    .feature {
        background: #FFFFFF;
        border: 2px solid #C7D5E8;
        border-radius: 15px;
        padding: 18px;
        margin-top: 14px;
        margin-bottom: 8px;
    }

    .feature h3 {
        color: #12345A;
        font-size: 1.25rem;
        margin: 0 0 8px 0;
    }

    .feature p {
        color: #27364B;
        font-size: 1rem;
        line-height: 1.6;
        margin: 0;
    }

    .stLinkButton a {
        width: 100%;
        min-height: 60px;
        border-radius: 12px;
        border: 2px solid #12345A;
        font-size: 1.15rem;
        font-weight: 700;
        justify-content: center;
        background-color: #FFFFFF;
        color: #12345A;
    }

    .stLinkButton a:hover {
        background-color: #E1EDFF;
        color: #12345A;
        border-color: #12345A;
    }

    .stLinkButton a:focus-visible {
        outline: 4px solid #F2B705;
        outline-offset: 3px;
    }

    .footer {
        background: #E4ECF6;
        padding: 16px;
        border-radius: 12px;
        margin-top: 24px;
        line-height: 1.7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 메인 화면
# --------------------------------------------------
def main():
    st.markdown(
        """
        <div class="hero">
            <h1>🦯 Blind Maid</h1>
            <p>
                시각장애인의 이동과 일상생활을 돕는 도우미<br>
                필요한 기능을 선택해 주세요.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 기능 1: 도착지 설정
    st.markdown(
        """
        <div class="feature">
            <h3>📍 도착지 설정</h3>
            <p>이동할 목적지를 설정하는 페이지로 이동합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "도착지 설정",
        DESTINATION_URL,
        use_container_width=True,
    )

    # 기능 2: 소리로 안내하는 길잡이
    st.markdown(
        """
        <div class="feature">
            <h3>🔊 소리로 안내하는 길잡이</h3>
            <p>소리를 이용한 안내 기능 페이지로 이동합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "소리로 안내하는 길잡이",
        GUIDE_URL,
        use_container_width=True,
    )

    # 기능 3: 사물 진동 알림이
    st.markdown(
        """
        <div class="feature">
            <h3>📳 사물 진동 알림이</h3>
            <p>주변 방해물을 진동으로 알려주는 페이지로 이동합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "사물 진동 알림이",
        VIBRATION_URL,
        use_container_width=True,
    )

    st.markdown(
        """
        <div class="footer">
            <strong>안전 안내</strong><br>
            이 앱은 기능 페이지로 연결하는 도우미입니다.
            실제 보행 시에는 주변 교통 상황을 확인하고,
            흰지팡이 등 검증된 보행 보조 수단을 함께 사용하세요.
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# 오류 처리
# --------------------------------------------------
try:
    main()
except Exception:
    st.error(
        "앱을 표시하는 중 오류가 발생했습니다. "
        "페이지를 새로고침한 뒤 다시 시도해 주세요."
    )

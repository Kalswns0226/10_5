
import math
import html
import streamlit as st
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(
    page_title="안심도착 | 안전 도착 알림",
    page_icon="🔔",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 접근성 중심의 고대비 디자인
st.markdown(
    """
    <style>
    .stApp {
        background-color: #071426;
        color: #FFFFFF;
    }
    .block-container {
        max-width: 780px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3, p, label, li {
        color: #FFFFFF !important;
    }
    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 1.8rem !important; }
    p, label, li { font-size: 1.15rem !important; }
    div.stButton > button {
        min-height: 64px;
        width: 100%;
        border: 2px solid #FFFFFF;
        border-radius: 14px;
        background: #FFD54F;
        color: #071426;
        font-size: 1.25rem;
        font-weight: 800;
    }
    div.stButton > button:focus {
        outline: 4px solid #00E5FF;
        outline-offset: 4px;
    }
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        min-height: 48px;
        font-size: 1.15rem;
    }
    .status-card {
        background: #102A43;
        border: 2px solid #7DD3FC;
        border-radius: 18px;
        padding: 22px;
        margin: 12px 0;
    }
    .status-title {
        color: #FFD54F;
        font-size: 1.55rem;
        font-weight: 800;
    }
    .big-distance {
        color: #FFFFFF;
        font-size: 2rem;
        font-weight: 800;
    }
    .hint {
        color: #D9E7F5;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def haversine_m(lat1, lon1, lat2, lon2):
    """두 좌표 사이의 직선거리를 미터 단위로 계산합니다."""
    earth_radius = 6_371_000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    a = max(0.0, min(1.0, a))
    return 2 * earth_radius * math.asin(math.sqrt(a))


def valid_coordinates(lat, lon):
    return (
        isinstance(lat, (int, float))
        and isinstance(lon, (int, float))
        and math.isfinite(lat)
        and math.isfinite(lon)
        and -90 <= lat <= 90
        and -180 <= lon <= 180
    )


def play_arrival_alert(destination):
    """브라우저가 허용하는 경우 음성, 소리, 진동을 실행합니다."""
    safe_destination = html.escape(destination, quote=True)
    components.html(
        f"""
        <div role="alert" aria-live="assertive">
          <p style="font-size:24px;font-weight:bold;color:#075985">
            목적지 도착 알림
          </p>
          <button id="repeat-alert"
            style="font-size:22px;padding:18px;width:100%;
                   background:#ffe082;border-radius:12px">
            🔔 도착 알림 다시 듣기
          </button>
        </div>
        <script>
        (() => {{
          const destination = "{safe_destination}";
          function alertUser() {{
            try {{
              if ("vibrate" in navigator) {{
                navigator.vibrate([300, 150, 300, 150, 600]);
              }}
            }} catch (e) {{}}

            try {{
              if ("speechSynthesis" in window) {{
                window.speechSynthesis.cancel();
                const message = new SpeechSynthesisUtterance(
                  "목적지에 도착했습니다. " + destination
                );
                message.lang = "ko-KR";
                message.rate = 0.85;
                window.speechSynthesis.speak(message);
              }}
            }} catch (e) {{}}

            try {{
              const AudioContext =
                window.AudioContext || window.webkitAudioContext;
              if (AudioContext) {{
                const ctx = new AudioContext();
                const beep = (start, frequency) => {{
                  const osc = ctx.createOscillator();
                  const gain = ctx.createGain();
                  osc.frequency.value = frequency;
                  gain.gain.value = 0.18;
                  osc.connect(gain);
                  gain.connect(ctx.destination);
                  osc.start(ctx.currentTime + start);
                  osc.stop(ctx.currentTime + start + 0.25);
                }};
                beep(0, 880);
                beep(0.35, 1100);
                setTimeout(() => ctx.close(), 1200);
              }}
            }} catch (e) {{}}
          }}
          document.getElementById("repeat-alert")
            .addEventListener("click", alertUser);
          alertUser();
        }})();
        </script>
        """,
        height=150,
        scrolling=False,
    )


st.title("🔔 안심도착")
st.markdown("### 목적지까지, 안심하고 이동하세요.")
st.markdown(
    "목적지를 설정한 뒤 **현재 위치 확인**을 누르세요. "
    "도착 반경 안에 들어오면 도착 알림을 받을 수 있습니다."
)

if "destination" not in st.session_state:
    st.session_state.destination = "내 목적지"
if "arrived" not in st.session_state:
    st.session_state.arrived = False
if "last_distance" not in st.session_state:
    st.session_state.last_distance = None
if "alerted" not in st.session_state:
    st.session_state.alerted = False

st.markdown("---")
st.header("1. 목적지 설정")

with st.form("destination_form"):
    destination = st.text_input(
        "목적지 이름",
        value=st.session_state.destination,
        help="예: 학교 정문, 집, 지하철역 출구",
    )
    col1, col2 = st.columns(2)
    with col1:
        dest_lat = st.number_input(
            "목적지 위도",
            min_value=-90.0,
            max_value=90.0,
            value=37.5665,
            format="%.6f",
            help="지도 앱에서 목적지의 위도를 확인하세요.",
        )
    with col2:
        dest_lon = st.number_input(
            "목적지 경도",
            min_value=-180.0,
            max_value=180.0,
            value=126.9780,
            format="%.6f",
            help="지도 앱에서 목적지의 경도를 확인하세요.",
        )

    radius = st.select_slider(
        "도착으로 판단할 거리",
        options=[20, 30, 50, 75, 100, 150, 200],
        value=50,
        format_func=lambda x: f"{x}미터",
        help="GPS 오차를 고려해 적절한 반경을 선택하세요.",
    )

    save_destination = st.form_submit_button(
        "목적지 저장", use_container_width=True
    )

if save_destination:
    if not destination.strip():
        st.error("목적지 이름을 입력해 주세요.")
    elif not valid_coordinates(dest_lat, dest_lon):
        st.error("위도와 경도를 올바르게 입력해 주세요.")
    else:
        st.session_state.destination = destination.strip()
        st.session_state.dest_lat = float(dest_lat)
        st.session_state.dest_lon = float(dest_lon)
        st.session_state.radius = int(radius)
        st.session_state.arrived = False
        st.session_state.alerted = False
        st.session_state.last_distance = None
        st.success("목적지를 저장했습니다.")

# 저장된 목적지가 없으면 기본값을 사용합니다.
if "dest_lat" not in st.session_state:
    st.session_state.dest_lat = 37.5665
    st.session_state.dest_lon = 126.9780
    st.session_state.radius = 50

st.markdown(
    f"""
    <div class="status-card">
      <div class="status-title">현재 목적지</div>
      <p style="font-size:25px;font-weight:bold">
        {html.escape(st.session_state.destination)}
      </p>
      <p class="hint">
        도착 반경: {st.session_state.radius}미터
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")
st.header("2. 현재 위치 확인")
st.write(
    "아래 위치 확인 기능을 실행하고 브라우저의 위치 권한을 허용하세요. "
    "실내나 건물 사이에서는 GPS 오차가 커질 수 있습니다."
)

try:
    location = streamlit_geolocation()
except Exception:
    location = None
    st.error(
        "위치 확인 기능을 불러오지 못했습니다. "
        "페이지를 새로고침하고 위치 권한을 확인해 주세요."
    )

if isinstance(location, dict):
    lat = location.get("latitude")
    lon = location.get("longitude")

    if lat is not None and lon is not None:
        if valid_coordinates(lat, lon):
            distance = haversine_m(
                float(lat),
                float(lon),
                st.session_state.dest_lat,
                st.session_state.dest_lon,
            )
            st.session_state.last_distance = distance
            st.session_state.arrived = (
                distance <= st.session_state.radius
            )

            st.markdown(
                f"""
                <div class="status-card" role="status" aria-live="polite">
                  <div class="status-title">
                    {"목적지 도착" if st.session_state.arrived else "이동 중"}
                  </div>
                  <div class="big-distance">
                    {"도착 반경 안입니다" if st.session_state.arrived
                     else f"약 {distance:.0f}미터 남았습니다"}
                  </div>
                  <p class="hint">
                    직선거리 기준이며 실제 보행 경로와 다를 수 있습니다.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.arrived and not st.session_state.alerted:
                play_arrival_alert(st.session_state.destination)
                st.session_state.alerted = True

            if st.session_state.arrived:
                st.success("목적지에 도착했습니다. 주변을 확인하고 안전하게 이동하세요.")
                if st.button("도착 알림 다시 듣기"):
                    play_arrival_alert(st.session_state.destination)
            else:
                st.info(
                    "아직 도착 반경 밖입니다. 위치를 다시 확인해 주세요."
                )
        else:
            st.warning("위치 정보가 올바르지 않습니다. 다시 확인해 주세요.")
    else:
        st.info(
            "아직 위치 정보가 없습니다. 위치 확인 버튼을 눌러 "
            "위치 정보를 가져오세요."
        )
else:
    st.info(
        "위치 정보를 기다리고 있습니다. 위의 위치 확인 버튼을 눌러 주세요."
    )

st.markdown("---")
st.header("3. 안전하게 사용하기")
st.markdown(
    """
    - 이동 중에는 주변 소리와 보행 환경에 집중하세요.
    - 이 앱은 길 안내나 장애물 감지 기능을 제공하지 않습니다.
    - GPS 위치와 도착 판정에는 오차가 있을 수 있습니다.
    - 진동은 지원되는 기기와 브라우저에서만 작동합니다.
    - 위치 확인이 되지 않으면 브라우저의 위치 권한과 인터넷 연결을 확인하세요.
    """
)
st.caption(
    "안심도착은 도착 확인을 보조하는 도구입니다. "
    "흰지팡이, 안내견, 익숙한 안전 경로 등 기존의 보행 안전 수단을 함께 사용하세요."
)

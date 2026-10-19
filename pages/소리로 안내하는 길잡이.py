
import streamlit as st
import requests
import folium
import html
import json
from streamlit_folium import st_folium

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="소리로 안내하는 길잡이",
    page_icon="🔊",
    layout="wide"
)

# -----------------------------
# 디자인
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef7ff, #f5f0ff);
}
.main .block-container {
    max-width: 1050px;
    padding-top: 2rem;
}
.hero {
    background: linear-gradient(120deg, #b9ddff, #ded0ff);
    padding: 28px;
    border-radius: 24px;
    text-align: center;
    color: #24365b;
    margin-bottom: 20px;
}
.hero h1 {
    font-size: 34px;
}
.panel {
    background: white;
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #e1e9f5;
    margin-bottom: 14px;
}
div.stButton > button {
    border-radius: 14px;
    min-height: 48px;
    font-weight: bold;
}
</style>

<div class="hero">
    <h1>🔊 소리로 안내하는 길잡이</h1>
    <p>귀로 듣고, 길을 확인하고, 더 안전하게 이동해요.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="panel">
<strong>💙 사용 방법</strong><br>
출발지와 도착지를 입력한 다음 경로를 검색하세요.
검색 결과를 글자로 확인하고 한국어 음성 안내를 들을 수 있어요.
</div>
""", unsafe_allow_html=True)

# -----------------------------
# 장소 검색
# -----------------------------
@st.cache_data(ttl=3600)
def find_place(place):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "SoriroGiljabiStudentProject/1.0"}
    response = requests.get(
        url,
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1
        },
        headers=headers,
        timeout=15
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(
            f"'{place}' 장소를 찾지 못했어요. "
            "지역명이나 역 이름을 더 정확하게 입력해 주세요."
        )

    return float(results[0]["lat"]), float(results[0]["lon"])


# -----------------------------
# 도보 경로 검색
# -----------------------------
def find_route(start, end):
    start_lat, start_lon = find_place(start)
    end_lat, end_lon = find_place(end)

    url = (
        "https://routing.openstreetmap.de/routed-foot/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        },
        headers={"User-Agent": "SoriroGiljabiStudentProject/1.0"},
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("경로를 찾지 못했어요. 장소를 다시 확인해 주세요.")

    route = data["routes"][0]
    return start_lat, start_lon, end_lat, end_lon, route


# -----------------------------
# 입력 화면
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    start = st.text_input("📍 출발지", "서울역")

with col2:
    end = st.text_input("🏁 도착지", "두정역")

search = st.button("🗺️ 경로 검색하기", type="primary", use_container_width=True)

if "route_data" not in st.session_state:
    st.session_state.route_data = None

if search:
    if not start.strip() or not end.strip():
        st.warning("출발지와 도착지를 모두 입력해 주세요.")
    else:
        with st.spinner("장소와 경로를 찾고 있어요..."):
            try:
                st.session_state.route_data = find_route(
                    start.strip(), end.strip()
                )
                st.session_state.route_names = (
                    start.strip(), end.strip()
                )
            except ValueError as e:
                st.error(str(e))
                st.session_state.route_data = None
            except requests.exceptions.Timeout:
                st.error("서버 응답 시간이 초과됐어요. 잠시 후 다시 시도해 주세요.")
                st.session_state.route_data = None
            except requests.exceptions.RequestException:
                st.error("지도 서버에 연결할 수 없어요. 인터넷 연결 후 다시 시도해 주세요.")
                st.session_state.route_data = None
            except (KeyError, IndexError, TypeError):
                st.error("경로 정보를 읽지 못했어요. 다시 검색해 주세요.")
                st.session_state.route_data = None
            except Exception:
                st.error("예상하지 못한 오류가 발생했어요. 잠시 후 다시 시도해 주세요.")
                st.session_state.route_data = None

# -----------------------------
# 경로 결과 화면
# -----------------------------
if st.session_state.route_data:
    start_lat, start_lon, end_lat, end_lon, route = (
        st.session_state.route_data
    )
    start_name, end_name = st.session_state.route_names

    distance_km = route["distance"] / 1000
    duration_min = route["duration"] / 60

    st.markdown("## 🧭 경로 안내 결과")

    a, b = st.columns(2)
    a.metric("📏 예상 거리", f"{distance_km:.1f} km")
    b.metric("⏱️ 예상 시간", f"{duration_min:.0f}분")

    # 지도 표시
    coordinates = route["geometry"]["coordinates"]
    points = [(lat, lon) for lon, lat in coordinates]

    route_map = folium.Map(
        location=[start_lat, start_lon],
        zoom_start=13
    )

    folium.Marker(
        [start_lat, start_lon],
        tooltip="출발지",
        popup=html.escape(start_name),
        icon=folium.Icon(color="green", icon="play")
    ).add_to(route_map)

    folium.Marker(
        [end_lat, end_lon],
        tooltip="도착지",
        popup=html.escape(end_name),
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(route_map)

    folium.PolyLine(
        points,
        color="#6C8DFF",
        weight=6,
        opacity=0.85,
        tooltip="검색된 경로"
    ).add_to(route_map)

    st_folium(
        route_map,
        use_container_width=True,
        height=420,
        returned_objects=[]
    )

    # 길 안내 문장 만들기
    instructions = []

    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            name = step.get("name") or "앞쪽 길"
            distance = step.get("distance", 0)

            maneuver = step.get("maneuver", {})
            kind = maneuver.get("type", "")
            modifier = maneuver.get("modifier", "")

            if kind == "depart":
                sentence = f"{name} 방향으로 출발하세요."
            elif kind == "arrive":
                sentence = "목적지에 도착했어요."
            elif kind == "turn":
                direction = {
                    "left": "왼쪽",
                    "right": "오른쪽",
                    "slight left": "약간 왼쪽",
                    "slight right": "약간 오른쪽",
                    "sharp left": "크게 왼쪽",
                    "sharp right": "크게 오른쪽",
                    "uturn": "유턴"
                }.get(modifier, "안내된 방향으로")
                sentence = f"{direction}으로 방향을 바꾸세요. {name}"
            elif kind in ("roundabout", "rotary"):
                sentence = f"회전 구간에서 안내를 확인하세요. {name}"
            else:
                sentence = f"{name} 방향으로 계속 이동하세요."

            if distance >= 100:
                sentence += f" 약 {distance:.0f}미터 이동하세요."
            elif distance > 0:
                sentence += f" 약 {distance:.0f}미터 앞까지 이동하세요."

            instructions.append(sentence)

    if not instructions:
        instructions = ["검색된 경로를 지도로 확인해 주세요."]

    st.markdown("## 🗣️ 음성 및 글자 안내")

    st.info(
        "아래 안내는 지도 경로 정보를 바탕으로 만든 체험용 안내예요. "
        "실제 횡단보도, 계단, 공사 구간을 자동으로 감지하지는 않아요."
    )

    for i, sentence in enumerate(instructions, start=1):
        st.markdown(f"**{i}.** {sentence}")

    # 브라우저의 한국어 음성 기능
    speech_text = " ".join(instructions)
    safe_speech_text = json.dumps(speech_text, ensure_ascii=False)

    st.components.v1.html(
        f"""
        <div style="font-family: sans-serif; padding: 8px 0;">
          <button id="speakBtn"
            style="background:#6c8dff;color:white;border:0;
            border-radius:12px;padding:13px 18px;font-size:16px;
            cursor:pointer;margin-right:8px;">
            🔊 음성 안내 듣기
          </button>
          <button id="stopBtn"
            style="background:#e8e5f8;color:#28345a;border:0;
            border-radius:12px;padding:13px 18px;font-size:16px;
            cursor:pointer;">
            ⏹️ 음성 멈추기
          </button>
          <p id="status" aria-live="polite">
            버튼을 누르면 한국어 음성 안내가 시작돼요.
          </p>
        </div>
        <script>
          const textToSpeak = {safe_speech_text};
          const status = document.getElementById("status");

          document.getElementById("speakBtn").onclick = () => {{
            if (!("speechSynthesis" in window)) {{
              status.textContent =
                "이 브라우저에서는 음성 안내를 지원하지 않아요.";
              return;
            }}
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance(textToSpeak);
            msg.lang = "ko-KR";
            msg.rate = 0.9;
            msg.onstart = () => {{
              status.textContent = "음성 안내를 재생하고 있어요.";
            }};
            msg.onend = () => {{
              status.textContent = "음성 안내가 끝났어요.";
            }};
            window.speechSynthesis.speak(msg);
          }};

          document.getElementById("stopBtn").onclick = () => {{
            if ("speechSynthesis" in window) {{
              window.speechSynthesis.cancel();
              status.textContent = "음성 안내를 멈췄어요.";
            }}
          }};
        </script>
        """,
        height=110
    )

    st.markdown("## ⚠️ 안전하게 이동하기")

    st.warning("""
    - 횡단보도에서는 반드시 신호와 주변 차량을 직접 확인하세요.
    - 계단, 턱, 공사 구간은 이 앱이 자동으로 감지하지 못해요.
    - 지도 경로와 예상 시간은 실제 상황과 다를 수 있어요.
    - 이 앱은 학교 프로젝트용 시제품이며, 실제 보행 안전을 보장하지 않아요.
    """)

else:
    st.markdown("""
    <div class="panel">
      <h3>✨ 준비됐어요!</h3>
      출발지와 도착지를 입력하고 <strong>경로 검색하기</strong>를 눌러 보세요.
      경로를 찾으면 지도와 글자 안내, 음성 안내가 표시돼요.
    </div>
    """, unsafe_allow_html=True)

st.caption(
    "지도 데이터: OpenStreetMap · 경로 검색 서버 이용 가능 여부에 따라 "
    "결과가 표시되지 않을 수 있어요."
)

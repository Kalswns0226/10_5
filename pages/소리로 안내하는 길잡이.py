
import json
from urllib.parse import urlencode

import folium
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

# =====================================
# 1. 기본 설정
# =====================================
st.set_page_config(
    page_title="소리로 안내하는 길잡이",
    page_icon="🐰",
    layout="wide",
)

HEADERS = {
    "User-Agent": "SoriroGiljabiStudentProject/3.0"
}

# =====================================
# 2. 귀여운 파스텔 디자인
# =====================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        145deg, #eff8ff 0%, #f3efff 60%, #fff2f8 100%
    );
    color: #34415e;
}
.block-container {
    max-width: 1050px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}
.hero {
    background: linear-gradient(120deg, #c7e7ff, #e1d6ff, #ffe2f0);
    border: 2px solid white;
    border-radius: 30px;
    padding: 25px 16px;
    text-align: center;
    box-shadow: 0 8px 24px #9daed522;
    margin-bottom: 20px;
}
.hero h1 {
    color: #34456b;
    font-size: 31px;
    margin-bottom: 7px;
}
.hero p {
    color: #526080;
    margin-bottom: 0;
}
div.stButton > button {
    border-radius: 16px;
    min-height: 46px;
    font-weight: 600;
    border: 1px solid #dce5ff;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(100deg, #8abaff, #b5a3ff);
    color: white;
    border: none;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e4e9ff;
    border-radius: 18px;
    padding: 14px;
}
.step-card {
    background: white;
    border: 1px solid #e2e8ff;
    border-radius: 16px;
    padding: 12px 15px;
    margin: 8px 0;
    color: #34415e;
}
.small-note {
    background: #f0edff;
    border-radius: 16px;
    padding: 14px;
    color: #4e527a;
}
</style>

<div class="hero">
    <div style="font-size:42px;">🐰 🔊 🐾</div>
    <h1>소리로 안내하는 길잡이</h1>
    <p>한 걸음씩, 쉽고 편안하게 목적지까지 💙</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="small-note">
<b>🩵 반가워요!</b><br>
출발지와 도착지를 입력하고 이동 방법을 선택해 보세요.
경로를 찾으면 지도와 짧은 안내 문장, 음성 안내를 확인할 수 있어요.
</div>
""", unsafe_allow_html=True)

st.write("")

# =====================================
# 3. 장소 검색
# =====================================
@st.cache_data(ttl=3600)
def find_place(place):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "kr",
        },
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(
            f"'{place}' 장소를 찾지 못했어요. "
            "역 이름이나 지역명을 더 정확하게 입력해 주세요."
        )

    return float(results[0]["lat"]), float(results[0]["lon"])


# =====================================
# 4. 도보 / 자동차 경로 검색
# =====================================
@st.cache_data(ttl=600)
def get_route(start, end, mode):
    start_lat, start_lon = find_place(start)
    end_lat, end_lon = find_place(end)

    if mode == "도보":
        base_url = (
            "https://routing.openstreetmap.de/"
            "routed-foot/route/v1/driving/"
        )
    else:
        base_url = "https://router.project-osrm.org/route/v1/driving/"

    url = (
        f"{base_url}{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
        },
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(
            "경로를 찾지 못했어요. 장소를 다시 확인해 주세요."
        )

    return {
        "start": (start_lat, start_lon),
        "end": (end_lat, end_lon),
        "route": data["routes"][0],
    }


# =====================================
# 5. 짧은 길 안내 문장 생성
# =====================================
def make_short_steps(route):
    steps = []

    for leg in route.get("legs", []):
        for item in leg.get("steps", []):
            maneuver = item.get("maneuver", {})
            kind = maneuver.get("type", "")
            modifier = maneuver.get("modifier", "")
            distance = item.get("distance", 0)
            road = item.get("name") or "앞쪽 길"

            if kind == "depart":
                sentence = f"{road} 방향으로 출발하세요."
            elif kind == "arrive":
                sentence = "목적지에 도착했어요!"
            elif kind in ("turn", "end of road", "fork"):
                directions = {
                    "left": "왼쪽",
                    "right": "오른쪽",
                    "slight left": "약간 왼쪽",
                    "slight right": "약간 오른쪽",
                    "sharp left": "크게 왼쪽",
                    "sharp right": "크게 오른쪽",
                    "straight": "직진",
                    "uturn": "유턴",
                }
                direction = directions.get(modifier, "안내된 방향")
                sentence = f"{direction}으로 이동하세요."
            elif kind in ("roundabout", "rotary"):
                sentence = "회전 구간에서는 방향을 확인하세요."
            else:
                sentence = f"{road} 방향으로 계속 이동하세요."

            if distance >= 100:
                sentence += f" 약 {round(distance / 10) * 10:.0f}미터 이동하세요."
            elif distance >= 20:
                sentence += f" 약 {round(distance / 10) * 10:.0f}미터 이동하세요."

            steps.append(sentence)

    # 같은 안내가 반복되는 것을 줄이기
    unique_steps = []
    for sentence in steps:
        if not unique_steps or sentence != unique_steps[-1]:
            unique_steps.append(sentence)

    if not unique_steps:
        unique_steps = ["지도에서 경로를 확인해 주세요."]

    # 안내가 너무 길어지지 않도록 최대 5개만 표시
    if len(unique_steps) > 5:
        unique_steps = unique_steps[:4] + [
            "이후 경로는 지도를 확인해 주세요."
        ]

    return unique_steps


# =====================================
# 6. 출발지 / 도착지 / 이동 방법
# =====================================
with st.container(border=True):
    st.subheader("📍 어디로 가고 싶나요?")

    col1, col2 = st.columns(2)

    with col1:
        start = st.text_input("출발지", "서울역")

    with col2:
        end = st.text_input("도착지", "두정역")

    st.markdown("### 🐾 이동 방법을 선택해 주세요")

    mode_label = st.radio(
        "이동 방법",
        ["🚶 도보", "🚗 자동차", "🚌 대중교통", "🚇 지하철"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if st.button(
        "💜 길 찾기!",
        type="primary",
        use_container_width=True,
    ):
        if not start.strip() or not end.strip():
            st.warning("출발지와 도착지를 모두 입력해 주세요.")
        elif start.strip() == end.strip():
            st.warning("출발지와 도착지를 다르게 입력해 주세요.")
        else:
            st.session_state.pop("route_result", None)
            st.session_state["search_request"] = (
                start.strip(),
                end.strip(),
                mode_label,
            )

# =====================================
# 7. 검색 결과
# =====================================
if "search_request" in st.session_state:
    start_name, end_name, selected_mode = (
        st.session_state["search_request"]
    )

    st.markdown("---")

    # 대중교통 / 지하철
    if selected_mode in ["🚌 대중교통", "🚇 지하철"]:
        params = {
            "api": "1",
            "origin": start_name,
            "destination": end_name,
            "travelmode": "transit",
        }

        if selected_mode == "🚇 지하철":
            params["transit_mode"] = "subway"

        maps_url = (
            "https://www.google.com/maps/dir/?"
            + urlencode(params)
        )

        if selected_mode == "🚇 지하철":
            st.subheader("🚇 지하철 경로")
            st.write("지하철 노선과 환승 정보를 확인해 보세요.")
        else:
            st.subheader("🚌 대중교통 경로")
            st.write("버스와 지하철을 포함한 대중교통 경로를 확인해 보세요.")

        st.link_button(
            "💙 경로 및 환승 정보 확인하기",
            maps_url,
            use_container_width=True,
        )

        st.info(
            "대중교통 경로는 외부 지도 서비스에서 제공해요. "
            "실시간 도착 시간과 환승 안내는 해당 서비스에서 확인해 주세요."
        )

    # 도보 / 자동차
    else:
        route_mode = (
            "도보" if selected_mode == "🚶 도보" else "자동차"
        )

        with st.spinner("🐾 길을 찾고 있어요..."):
            try:
                result = get_route(
                    start_name,
                    end_name,
                    route_mode,
                )
                st.session_state["route_result"] = (
                    result,
                    start_name,
                    end_name,
                    route_mode,
                )

            except ValueError as e:
                st.error(str(e))
                st.session_state.pop("route_result", None)

            except requests.exceptions.Timeout:
                st.error("서버 응답이 늦어요. 잠시 후 다시 시도해 주세요.")
                st.session_state.pop("route_result", None)

            except requests.exceptions.RequestException:
                st.error("지도 서버에 연결할 수 없어요. 다시 시도해 주세요.")
                st.session_state.pop("route_result", None)

            except Exception:
                st.error("오류가 발생했어요. 장소를 확인하고 다시 시도해 주세요.")
                st.session_state.pop("route_result", None)


# =====================================
# 8. 지도 / 거리 / 시간 / 음성 안내
# =====================================
if "route_result" in st.session_state:
    result, start_name, end_name, route_mode = (
        st.session_state["route_result"]
    )

    route = result["route"]
    start_lat, start_lon = result["start"]
    end_lat, end_lon = result["end"]

    icon = "🚶" if route_mode == "도보" else "🚗"

    st.subheader(f"{icon} {route_mode} 안내")

    col1, col2 = st.columns(2)

    col1.metric("📏 예상 거리", f'{route["distance"] / 1000:.1f} km')
    col2.metric("⏰ 예상 시간", f'{route["duration"] / 60:.0f}분')

    # 지도 만들기
    coordinates = route["geometry"]["coordinates"]
    points = [(lat, lon) for lon, lat in coordinates]

    route_map = folium.Map(
        location=[start_lat, start_lon],
        zoom_start=12,
    )

    folium.Marker(
        [start_lat, start_lon],
        tooltip="출발지",
        popup=start_name,
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(route_map)

    folium.Marker(
        [end_lat, end_lon],
        tooltip="도착지",
        popup=end_name,
        icon=folium.Icon(color="red", icon="flag"),
    ).add_to(route_map)

    folium.PolyLine(
        points,
        color="#8C91FF",
        weight=6,
        opacity=0.9,
    ).add_to(route_map)

    st_folium(
        route_map,
        use_container_width=True,
        height=350,
        returned_objects=[],
    )

    # 짧은 안내
    instructions = make_short_steps(route)

    st.subheader("🗣️ 귀로 듣는 길 안내")

    for i, sentence in enumerate(instructions, start=1):
        st.markdown(
            f'<div class="step-card"><b>{i}.</b> '
            f'{sentence}</div>',
            unsafe_allow_html=True,
        )

    # 한국어 음성 합성
    speech_text = " ".join(instructions)
    safe_text = json.dumps(speech_text, ensure_ascii=False)

    components.html(
        f"""
        <div style="
            background:linear-gradient(120deg,#d8edff,#eee2ff);
            border-radius:20px;
            padding:18px;
            text-align:center;
            font-family:sans-serif;
        ">
          <div style="font-size:30px;">🐰🔊</div>
          <h3 style="color:#34456b;">귀로 듣는 길 안내</h3>
          <p style="color:#526080;">
            버튼을 누르면 한국어 음성으로 읽어 줘요.
          </p>

          <button id="play" style="
            background:#7e9fff;color:white;border:0;
            border-radius:14px;padding:13px 18px;
            font-size:16px;font-weight:bold;cursor:pointer;
          ">🔊 안내 듣기</button>

          <button id="stop" style="
            background:white;color:#465477;border:1px solid #cbd6ff;
            border-radius:14px;padding:13px 18px;
            font-size:16px;cursor:pointer;
          ">⏹️ 멈추기</button>

          <p id="status" aria-live="polite" style="color:#465477;">
            음성 안내를 시작할 준비가 됐어요.
          </p>
        </div>

        <script>
          const textToSpeak = {safe_text};
          const status = document.getElementById("status");

          document.getElementById("play").onclick = function() {{
            if (!("speechSynthesis" in window)) {{
              status.textContent =
                "이 브라우저에서는 음성 안내를 지원하지 않아요.";
              return;
            }}

            window.speechSynthesis.cancel();

            const message = new SpeechSynthesisUtterance(textToSpeak);
            message.lang = "ko-KR";
            message.rate = 0.9;
            message.pitch = 1.05;

            message.onstart = function() {{
              status.textContent = "🐾 길 안내를 읽고 있어요.";
            }};

            message.onend = function() {{
              status.textContent = "💙 안내가 끝났어요!";
            }};

            message.onerror = function() {{
              status.textContent =
                "음성 재생에 실패했어요. 브라우저 설정을 확인해 주세요.";
            }};

            window.speechSynthesis.speak(message);
          }};

          document.getElementById("stop").onclick = function() {{
            if ("speechSynthesis" in window) {{
              window.speechSynthesis.cancel();
            }}
            status.textContent = "음성 안내를 멈췄어요.";
          }};
        </script>
        """,
        height=240,
    )

    st.markdown("""
    <div class="small-note">
    🩵 <b>안전 약속</b><br>
    이 앱은 횡단보도, 계단, 공사 구간이나 주변 차량을
    실시간으로 감지하지 못해요. 실제 이동 시에는 주변 안전을
    확인하고 신뢰할 수 있는 보행 안내를 이용해 주세요.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption(
    "🐰 소리로 안내하는 길잡이 · 학교 프로젝트용 시제품"
)

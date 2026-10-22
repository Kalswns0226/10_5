
import json
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="소리로 안내하는 길잡이",
    page_icon="🩵",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #F1F7FF, #FBF8FF);
}
.block-container {
    max-width: 850px;
    padding-top: 2rem;
}
h1, h2, h3 {
    color: #536A9D;
}
div.stButton > button {
    border-radius: 15px;
    border: 0;
    background-color: #DCD6FF;
    color: #35345A;
    font-weight: bold;
    min-height: 44px;
}
div[data-testid="stForm"] {
    background: white;
    border-radius: 20px;
    padding: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("🩵 소리로 안내하는 길잡이")
st.write("음성과 지도 안내를 이용해 목적지를 찾아봐요!")
st.info("학교 프로젝트용 체험 앱입니다. 실제 이동 시에는 주변을 직접 확인하고 보호자나 안전한 길 안내를 함께 이용하세요.")

st.subheader("📍 어디로 갈까요?")

start = st.text_input("출발지", placeholder="예: 서울역")
destination = st.text_input("도착지", placeholder="예: 서울시청")

transport = st.radio(
    "이동 방법을 선택해 주세요",
    ["🚶 도보", "🚗 자동차", "🚌 대중교통", "🚇 지하철"],
    horizontal=True
)

def find_place(place):
    url = "https://nominatim.openstreetmap.org/search"
    response = requests.get(
        url,
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "kr"
        },
        headers={"User-Agent": "SoriroGiljabiSchoolProject/1.0"},
        timeout=15
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    return [
        float(results[0]["lat"]),
        float(results[0]["lon"])
    ]

def get_route(origin, target, walking=False):
    if walking:
        base = "https://routing.openstreetmap.de/routed-foot/route/v1/driving/"
    else:
        base = "https://router.project-osrm.org/route/v1/driving/"

    url = (
        base
        + f"{origin[1]},{origin[0]};{target[1]},{target[0]}"
    )

    response = requests.get(
        url,
        params={"overview": "full", "geometries": "geojson", "steps": "true"},
        timeout=25
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("routes"):
        return None

    return data["routes"][0]

def format_distance(meters):
    if meters < 1000:
        return f"{round(meters)}m"
    return f"{meters / 1000:.1f}km"

def make_instructions(route, walking):
    instructions = []

    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            name = step.get("name") or "현재 길"
            distance = step.get("distance", 0)

            if distance < 20:
                continue

            if walking:
                sentence = f"{name} 방향으로 약 {format_distance(distance)} 걸어가세요."
            else:
                sentence = f"{name} 도로를 따라 약 {format_distance(distance)} 이동하세요."

            instructions.append(sentence)

            if len(instructions) >= 6:
                break

        if len(instructions) >= 6:
            break

    if not instructions:
        instructions = ["지도에 표시된 경로를 따라 이동해 주세요."]

    instructions.append("목적지에 도착했습니다.")
    return instructions

if "guidance_text" not in st.session_state:
    st.session_state.guidance_text = (
        "안녕하세요! 소리로 안내하는 길잡이입니다. "
        "출발지와 도착지를 입력하고 길 찾기를 눌러 주세요."
    )

if st.button("🔎 길 찾기", use_container_width=True):
    if not start.strip() or not destination.strip():
        st.warning("출발지와 도착지를 모두 입력해 주세요.")
    else:
        try:
            with st.spinner("장소와 경로를 찾고 있어요..."):
                origin = find_place(start.strip())
                target = find_place(destination.strip())

                if origin is None:
                    st.error("출발지를 찾지 못했어요. 장소 이름을 조금 더 자세히 입력해 주세요.")
                elif target is None:
                    st.error("도착지를 찾지 못했어요. 장소 이름을 조금 더 자세히 입력해 주세요.")
                elif transport in ["🚌 대중교통", "🚇 지하철"]:
                    mode = "transit"
                    url = (
                        "https://www.google.com/maps/dir/?api=1"
                        f"&origin={requests.utils.quote(start.strip())}"
                        f"&destination={requests.utils.quote(destination.strip())}"
                        f"&travelmode={mode}"
                    )
                    if transport == "🚇 지하철":
                        url += "&transit_mode=subway"

                    st.session_state.guidance_text = (
                        f"{transport[2:]} 경로를 확인해 주세요. "
                        f"출발지는 {start}, 도착지는 {destination}입니다. "
                        "아래 링크를 열어 실제 대중교통 경로를 확인하세요."
                    )
                    st.session_state.route_url = url
                    st.session_state.route_map = None
                    st.session_state.instructions = [
                        f"출발지 {start}에서 출발합니다.",
                        f"목적지 {destination}까지 {transport[2:]} 경로를 확인해 주세요.",
                        "환승과 도착 정보를 지도 앱에서 확인해 주세요."
                    ]
                    st.success("경로 안내를 준비했어요!")

                else:
                    walking = transport == "🚶 도보"
                    route = get_route(origin, target, walking=walking)

                    if route is None:
                        st.error("경로를 찾지 못했어요. 잠시 후 다시 시도해 주세요.")
                    else:
                        instructions = make_instructions(route, walking)
                        st.session_state.instructions = instructions
                        st.session_state.guidance_text = (
                            f"출발지 {start}에서 출발합니다. "
                            + " ".join(instructions)
                        )
                        st.session_state.route_url = None

                        route_map = folium.Map(
                            location=origin,
                            zoom_start=13,
                            tiles="OpenStreetMap"
                        )
                        folium.Marker(
                            origin,
                            tooltip="출발지",
                            popup=start,
                            icon=folium.Icon(color="green")
                        ).add_to(route_map)

                        folium.Marker(
                            target,
                            tooltip="도착지",
                            popup=destination,
                            icon=folium.Icon(color="red")
                        ).add_to(route_map)

                        coordinates = [
                            [point[1], point[0]]
                            for point in route["geometry"]["coordinates"]
                        ]

                        folium.PolyLine(
                            coordinates,
                            color="#8A83E8",
                            weight=6,
                            opacity=0.85
                        ).add_to(route_map)

                        route_map.fit_bounds(coordinates)
                        st.session_state.route_map = route_map
                        st.session_state.route_summary = (
                            f"거리: {format_distance(route['distance'])} · "
                            f"예상 시간: {round(route['duration'] / 60)}분"
                        )
                        st.success("길을 찾았어요!")

        except requests.RequestException:
            st.error("경로 서비스에 연결하지 못했어요. 인터넷 연결을 확인하고 다시 시도해 주세요.")
        except (KeyError, ValueError, TypeError):
            st.error("경로 정보를 처리하는 중 문제가 생겼어요. 다시 시도해 주세요.")

if st.session_state.get("route_url"):
    st.markdown(
        f"[🗺️ 대중교통 경로 열기]({st.session_state.route_url})"
    )

if st.session_state.get("route_map") is not None:
    st.subheader("🗺️ 경로 지도")
    st.write(st.session_state.get("route_summary", ""))
    st_folium(
        st.session_state.route_map,
        width=None,
        height=400,
        key="route_map_display"
    )

if st.session_state.get("instructions"):
    st.subheader("🧭 길 안내")
    for i, instruction in enumerate(st.session_state.instructions, 1):
        st.markdown(f"**{i}.** {instruction}")

st.divider()
st.subheader("🔊 음성 안내")

st.write("아래 버튼을 누르면 안내 내용을 한국어 음성으로 읽어 줘요.")

speech_text = st.session_state.guidance_text

components.html(
    f"""
    <div style="
        display:flex;
        gap:10px;
        flex-wrap:wrap;
        font-family:sans-serif;">
      <button id="speak" style="
        background:#DCD6FF;
        color:#35345A;
        border:0;
        border-radius:14px;
        padding:13px 18px;
        font-size:16px;
        font-weight:bold;
        cursor:pointer;">
        🔊 음성 안내 시작
      </button>
      <button id="stop" style="
        background:#E2F2FF;
        color:#354C70;
        border:0;
        border-radius:14px;
        padding:13px 18px;
        font-size:16px;
        font-weight:bold;
        cursor:pointer;">
        ⏹️ 음성 중지
      </button>
    </div>
    <p id="status" style="font-size:13px;color:#536A9D;">
      버튼을 누르면 안내를 읽어 줘요.
    </p>
    <script>
      const textToRead = {json.dumps(speech_text, ensure_ascii=False)};
      const status = document.getElementById("status");

      document.getElementById("speak").addEventListener("click", () => {{
        if (!("speechSynthesis" in window)) {{
          status.textContent = "이 브라우저에서는 음성 안내를 지원하지 않아요.";
          return;
        }}

        window.speechSynthesis.cancel();

        const message = new SpeechSynthesisUtterance(textToRead);
        message.lang = "ko-KR";
        message.rate = 0.9;

        message.onstart = () => {{
          status.textContent = "🔊 음성 안내 중이에요.";
        }};

        message.onend = () => {{
          status.textContent = "안내가 끝났어요.";
        }};

        message.onerror = () => {{
          status.textContent = "음성을 재생하지 못했어요. 기기 음량과 브라우저 설정을 확인해 주세요.";
        }};

        window.speechSynthesis.speak(message);
      }});

      document.getElementById("stop").addEventListener("click", () => {{
        window.speechSynthesis.cancel();
        status.textContent = "음성 안내를 중지했어요.";
      }});
    </script>
    """,
    height=100
)

st.caption(
    "안내 음성은 브라우저의 음성 합성 기능을 사용합니다. "
    "이 앱은 시범용으로, 실시간 GPS 추적이나 횡단보도·계단 감지 기능은 제공하지 않습니다."
)

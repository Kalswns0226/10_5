
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
</style>
""", unsafe_allow_html=True)

st.title("🩵 소리로 안내하는 길잡이")
st.write("목적지를 입력하면 경로와 음성 안내를 확인할 수 있어요!")
st.info(
    "학교 프로젝트용 시제품입니다. 실시간 위치 추적이나 "
    "횡단보도·계단 감지 기능은 없으므로 실제 이동 안내로 사용하지 마세요."
)

start = st.text_input("📍 출발지", placeholder="예: 서울역")
destination = st.text_input("🏁 도착지", placeholder="예: 서울시청")

transport = st.radio(
    "🚦 이동 방법",
    ["🚶 도보", "🚗 자동차", "🚌 대중교통", "🚇 지하철"],
    horizontal=True
)

def find_place(place):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
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

def get_route(origin, target, walking):
    if walking:
        base = (
            "https://routing.openstreetmap.de/"
            "routed-foot/route/v1/driving/"
        )
    else:
        base = "https://router.project-osrm.org/route/v1/driving/"

    url = (
        base
        + f"{origin[1]},{origin[0]};{target[1]},{target[0]}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        },
        timeout=25
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("routes"):
        return None

    return data["routes"][0]

def format_distance(meters):
    if meters < 1000:
        return f"{round(meters)}미터"
    return f"{meters / 1000:.1f}킬로미터"

def describe_step(step, walking):
    distance = step.get("distance", 0)
    name = step.get("name") or "현재 길"
    maneuver = step.get("maneuver", {})
    action = maneuver.get("type", "")
    modifier = maneuver.get("modifier", "")

    if action == "depart":
        beginning = "출발하세요"
    elif action == "arrive":
        return "목적지에 도착했습니다."
    elif action == "turn":
        directions = {
            "left": "왼쪽으로",
            "right": "오른쪽으로",
            "slight left": "왼쪽 방향으로",
            "slight right": "오른쪽 방향으로",
            "sharp left": "왼쪽으로 크게",
            "sharp right": "오른쪽으로 크게",
            "uturn": "유턴하여"
        }
        beginning = directions.get(
            modifier, "방향을 확인하며"
        ) + " 이동하세요"
    elif action == "roundabout":
        beginning = "회전 구간에서 안내된 방향으로 이동하세요"
    elif action == "new name":
        beginning = "길이 이어집니다"
    else:
        beginning = "계속 이동하세요"

    if walking:
        mode = "걸어가세요"
    else:
        mode = "주행하세요"

    if action in ["turn", "roundabout"]:
        sentence = beginning
    elif action == "arrive":
        sentence = beginning
    elif action == "depart":
        sentence = beginning
    else:
        sentence = f"{name} 방향으로 {mode}"

    if distance >= 20 and action != "arrive":
        sentence += f". 약 {format_distance(distance)} 이동하세요"

    return sentence + "."

def make_instructions(route, walking):
    instructions = []

    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            distance = step.get("distance", 0)

            if distance < 10 and step.get("maneuver", {}).get("type") != "arrive":
                continue

            sentence = describe_step(step, walking)

            if sentence not in instructions:
                instructions.append(sentence)

    if not instructions:
        instructions = [
            "지도에 표시된 경로를 확인하며 이동하세요."
        ]

    if "목적지에 도착했습니다." not in instructions:
        instructions.append("목적지에 도착했습니다.")

    return instructions

if "guidance_text" not in st.session_state:
    st.session_state.guidance_text = (
        "안녕하세요! 소리로 안내하는 길잡이입니다. "
        "출발지와 도착지를 입력한 뒤 길 찾기를 눌러 주세요."
    )

if "instructions" not in st.session_state:
    st.session_state.instructions = []

if "route_map" not in st.session_state:
    st.session_state.route_map = None

if "route_url" not in st.session_state:
    st.session_state.route_url = None

if st.button("🔎 길 찾기", use_container_width=True):
    if not start.strip() or not destination.strip():
        st.warning("출발지와 도착지를 모두 입력해 주세요.")
    else:
        try:
            with st.spinner("경로를 찾고 있어요..."):
                origin = find_place(start.strip())
                target = find_place(destination.strip())

                if origin is None or target is None:
                    st.error(
                        "장소를 찾지 못했어요. 이름을 더 자세히 입력해 주세요."
                    )

                elif transport in ["🚌 대중교통", "🚇 지하철"]:
                    url = (
                        "https://www.google.com/maps/dir/?api=1"
                        f"&origin={requests.utils.quote(start.strip())}"
                        f"&destination={requests.utils.quote(destination.strip())}"
                        "&travelmode=transit"
                    )

                    if transport == "🚇 지하철":
                        url += "&transit_mode=subway"

                    instructions = [
                        f"출발지는 {start}입니다.",
                        f"도착지는 {destination}입니다.",
                        "아래 대중교통 경로 링크를 열어 "
                        "승차역, 환승역, 하차역을 확인해 주세요.",
                        "실제 운행 정보와 도착 정보를 확인하세요."
                    ]

                    st.session_state.instructions = instructions
                    st.session_state.guidance_text = " ".join(instructions)
                    st.session_state.route_url = url
                    st.session_state.route_map = None
                    st.session_state.route_summary = ""

                    st.success("대중교통 경로 안내를 준비했어요!")

                else:
                    walking = transport == "🚶 도보"
                    route = get_route(origin, target, walking)

                    if route is None:
                        st.error("경로를 찾지 못했어요. 다시 시도해 주세요.")
                    else:
                        instructions = make_instructions(route, walking)

                        st.session_state.instructions = instructions
                        st.session_state.guidance_text = (
                            f"{transport[2:]} 안내를 시작합니다. "
                            f"출발지는 {start}입니다. "
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
                            [p[1], p[0]]
                            for p in route["geometry"]["coordinates"]
                        ]

                        folium.PolyLine(
                            coordinates,
                            color="#8A83E8",
                            weight=6
                        ).add_to(route_map)

                        route_map.fit_bounds(coordinates)

                        st.session_state.route_map = route_map
                        st.session_state.route_summary = (
                            f"거리: {format_distance(route['distance'])} · "
                            f"예상 시간: {round(route['duration'] / 60)}분"
                        )

                        st.success("경로를 찾았어요!")

        except requests.RequestException:
            st.error(
                "지도 서비스에 연결하지 못했어요. "
                "인터넷 연결을 확인하고 다시 시도해 주세요."
            )
        except (KeyError, ValueError, TypeError):
            st.error("경로 정보를 처리하지 못했어요. 다시 시도해 주세요.")

if st.session_state.route_url:
    st.link_button(
        "🗺️ 대중교통 경로 자세히 보기",
        st.session_state.route_url,
        use_container_width=True
    )

if st.session_state.route_map is not None:
    st.subheader("🗺️ 경로 지도")
    st.write(st.session_state.route_summary)
    st_folium(
        st.session_state.route_map,
        height=400,
        use_container_width=True,
        key="route_map"
    )

if st.session_state.instructions:
    st.subheader("🧭 단계별 길 안내")

    for number, instruction in enumerate(
        st.session_state.instructions, 1
    ):
        st.markdown(f"**{number}.** {instruction}")

st.divider()
st.subheader("🔊 음성으로 경로 듣기")
st.write("버튼을 누르면 안내 문장을 순서대로 읽어 줘요.")

speech_text = st.session_state.guidance_text

components.html(
    f"""
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <button id="play" style="
        background:#DCD6FF;color:#35345A;border:0;
        border-radius:14px;padding:13px 18px;
        font-size:16px;font-weight:bold;cursor:pointer;">
        🔊 전체 경로 듣기
      </button>
      <button id="stop" style="
        background:#E2F2FF;color:#354C70;border:0;
        border-radius:14px;padding:13px 18px;
        font-size:16px;font-weight:bold;cursor:pointer;">
        ⏹️ 중지
      </button>
    </div>
    <p id="status" style="font-size:13px;color:#536A9D;">
      전체 경로 듣기를 눌러 주세요.
    </p>
    <script>
      const text = {json.dumps(speech_text, ensure_ascii=False)};
      const status = document.getElementById("status");

      document.getElementById("play").onclick = () => {{
        if (!("speechSynthesis" in window)) {{
          status.textContent = "현재 브라우저에서 음성 기능을 사용할 수 없어요.";
          return;
        }}

        window.speechSynthesis.cancel();

        const parts = text.split(/(?<=\\.)\\s+/).filter(x => x.trim());
        let index = 0;

        function readNext() {{
          if (index >= parts.length) {{
            status.textContent = "전체 안내가 끝났어요.";
            return;
          }}

          const message = new SpeechSynthesisUtterance(parts[index]);
          message.lang = "ko-KR";
          message.rate = 0.9;

          message.onstart = () => {{
            status.textContent =
              "🔊 안내 중 (" + (index + 1) + "/" + parts.length + ")";
          }};

          message.onend = () => {{
            index++;
            readNext();
          }};

          message.onerror = () => {{
            status.textContent = "음성을 재생하지 못했어요.";
          }};

          window.speechSynthesis.speak(message);
        }}

        readNext();
      }};

      document.getElementById("stop").onclick = () => {{
        window.speechSynthesis.cancel();
        status.textContent = "음성 안내를 중지했어요.";
      }};
    </script>
    """,
    height=100
)

st.caption(
    "이 시제품은 경로 안내 문장을 읽어 주지만, "
    "GPS로 현재 위치를 추적해 다음 회전 지점에서 자동 안내하지는 않습니다. "
    "대중교통의 상세 승하차 안내는 연결된 지도 서비스에서 확인해야 합니다."
)

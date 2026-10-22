
import json
import math
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

# -------------------------------
# 1. 기본 설정과 귀여운 디자인
# -------------------------------
st.set_page_config(
    page_title="소리로 안내하는 길잡이",
    page_icon="🩵",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #EFF7FF 0%, #FBF7FF 100%);
}
.block-container {
    max-width: 850px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
h1, h2, h3 {
    color: #536A9D;
}
div.stButton > button {
    border: 0;
    border-radius: 16px;
    background: #DCD6FF;
    color: #38365F;
    font-weight: 700;
    min-height: 48px;
}
div[data-testid="stForm"] {
    background: white;
    border-radius: 20px;
    padding: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("🩵 소리로 안내하는 길잡이")
st.markdown(
    "### 🐰 귀로 듣고, 길을 찾아요!"
)
st.write(
    "목적지까지의 경로를 음성으로 안내하고, "
    "지도에서 확인되는 주의 장소를 미리 알려 주는 앱이에요."
)

st.info(
    "학교 프로젝트용 시제품입니다. 실제 이동에 필요한 "
    "모든 위험 정보를 감지하거나 안전을 보장하지는 않습니다."
)

# -------------------------------
# 2. 장소 검색
# -------------------------------
def find_place(place):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "kr"
        },
        headers={
            "User-Agent": "SoriroGiljabiSchoolProject/1.0"
        },
        timeout=20
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    return [
        float(results[0]["lat"]),
        float(results[0]["lon"])
    ]

# -------------------------------
# 3. 경로 검색
# -------------------------------
def get_route(origin, target, walking=True):
    if walking:
        base = (
            "https://routing.openstreetmap.de/"
            "routed-foot/route/v1/driving/"
        )
    else:
        base = (
            "https://router.project-osrm.org/"
            "route/v1/driving/"
        )

    url = (
        base
        + f"{origin[1]},{origin[0]};"
        + f"{target[1]},{target[0]}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "true"
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("routes"):
        return []

    return data["routes"]

# -------------------------------
# 4. 거리와 길 안내 문장 만들기
# -------------------------------
def distance_text(meters):
    if meters < 1000:
        return f"{round(meters)}미터"
    return f"{meters / 1000:.1f}킬로미터"

def make_instructions(route, walking=True):
    instructions = []

    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            maneuver = step.get("maneuver", {})
            action = maneuver.get("type", "")
            direction = maneuver.get("modifier", "")
            road = step.get("name") or "이름이 확인되지 않은 길"
            distance = step.get("distance", 0)

            if action == "arrive":
                instructions.append("목적지에 도착했습니다.")
                continue

            if action == "depart":
                instructions.append(
                    f"출발합니다. {road} 방향으로 "
                    f"{distance_text(distance)} 이동하세요."
                )
                continue

            directions = {
                "left": "왼쪽으로",
                "right": "오른쪽으로",
                "slight left": "왼쪽 방향으로",
                "slight right": "오른쪽 방향으로",
                "sharp left": "왼쪽으로 크게",
                "sharp right": "오른쪽으로 크게",
                "uturn": "유턴하여"
            }

            if action == "turn":
                turn_text = directions.get(
                    direction, "방향을 확인한 뒤"
                )
                sentence = (
                    f"안내 지점에서 {turn_text} 이동하세요."
                )
            elif action == "roundabout":
                sentence = (
                    "회전 구간입니다. 경로를 확인하고 "
                    "안내된 방향으로 이동하세요."
                )
            elif action in ["continue", "new name"]:
                sentence = (
                    f"{road} 방향으로 계속 이동하세요."
                )
            else:
                sentence = (
                    f"{road} 방향으로 이동하세요."
                )

            if distance >= 20:
                sentence += (
                    f" 이 구간의 길이는 약 "
                    f"{distance_text(distance)}입니다."
                )

            instructions.append(sentence)

    # 안내 문장이 없을 때의 기본 문장
    if not instructions:
        instructions = [
            "경로 안내 정보를 충분히 가져오지 못했습니다. "
            "경로를 다시 검색해 주세요."
        ]

    if not any("도착했습니다" in x for x in instructions):
        instructions.append("경로의 마지막 지점에 도착했습니다.")

    return instructions

# -------------------------------
# 5. 경로 주변 주의 장소 확인
#    OpenStreetMap에 등록된 정보만 사용
# -------------------------------
def approximate_distance_m(lat1, lon1, lat2, lon2):
    """두 좌표 사이의 대략적인 직선거리(미터)."""
    mean_lat = math.radians((lat1 + lat2) / 2)
    north = (lat1 - lat2) * 111_000
    east = (lon1 - lon2) * 111_000 * math.cos(mean_lat)
    return math.sqrt(north * north + east * east)

def find_caution_places(route):
    coords = route.get("geometry", {}).get("coordinates", [])

    if not coords:
        return [], False

    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]

    south = min(lats) - 0.0015
    north = max(lats) + 0.0015
    west = min(lons) - 0.0015
    east = max(lons) + 0.0015

    query = f"""
    [out:json][timeout:20];
    (
      nwr["highway"="crossing"]({south},{west},{north},{east});
      nwr["footway"="crossing"]({south},{west},{north},{east});
      nwr["highway"="steps"]({south},{west},{north},{east});
      nwr["barrier"="kerb"]({south},{west},{north},{east});
    );
    out center tags;
    """

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            headers={
                "User-Agent": "SoriroGiljabiSchoolProject/1.0"
            },
            timeout=30
        )
        response.raise_for_status()
        elements = response.json().get("elements", [])
    except (requests.RequestException, ValueError):
        return [], False

    cautions = []
    seen = set()

    for element in elements:
        tags = element.get("tags", {})

        # 노드는 lat/lon, way/relation은 center 좌표를 이용
        if "lat" in element and "lon" in element:
            lat = element["lat"]
            lon = element["lon"]
        elif "center" in element:
            lat = element["center"]["lat"]
            lon = element["center"]["lon"]
        else:
            continue

        # 경로 좌표 중 가장 가까운 점까지의 거리
        nearest = min(
            approximate_distance_m(lat, lon, p[1], p[0])
            for p in coords[::max(1, len(coords) // 300)]
        )

        # 경로에 충분히 가까운 등록 정보만 사용
        if nearest > 30:
            continue

        if tags.get("highway") == "crossing" or tags.get("footway") == "crossing":
            name = "횡단보도 정보"
            message = (
                "주의하세요. 지도 데이터에 횡단보도 정보가 "
                "등록되어 있습니다. 주변 차량과 신호를 확인하세요."
            )
        elif tags.get("highway") == "steps":
            name = "계단 정보"
            message = (
                "주의하세요. 지도 데이터에 계단 정보가 "
                "등록되어 있습니다. 주변 지형을 확인하고 도움을 요청하세요."
            )
        elif tags.get("barrier") == "kerb":
            name = "연석 정보"
            message = (
                "주의하세요. 지도 데이터에 연석 정보가 "
                "등록되어 있습니다. 발밑과 주변을 확인하세요."
            )
        else:
            continue

        key = (name, round(lat, 4), round(lon, 4))
        if key not in seen:
            seen.add(key)
            cautions.append({
                "name": name,
                "message": message,
                "lat": lat,
                "lon": lon
            })

    return cautions, True

# -------------------------------
# 6. 사용자 입력
# -------------------------------
st.subheader("📍 어디로 갈까요?")

start = st.text_input(
    "출발지",
    placeholder="예: 서울역"
)
destination = st.text_input(
    "도착지",
    placeholder="예: 서울시청"
)

transport = st.radio(
    "이동 방법을 선택해 주세요",
    ["🚶 도보", "🚗 자동차", "🚌 대중교통", "🚇 지하철"],
    horizontal=True
)

# -------------------------------
# 7. 길 찾기 실행
# -------------------------------
if "instructions" not in st.session_state:
    st.session_state.instructions = []

if "cautions" not in st.session_state:
    st.session_state.cautions = []

if "speech_text" not in st.session_state:
    st.session_state.speech_text = (
        "안녕하세요. 소리로 안내하는 길잡이입니다. "
        "출발지와 도착지를 입력해 주세요."
    )

if "route_map" not in st.session_state:
    st.session_state.route_map = None

if st.button("🔎 경로 찾기", use_container_width=True):
    if not start.strip() or not destination.strip():
        st.warning("출발지와 도착지를 모두 입력해 주세요.")
    else:
        try:
            with st.spinner("길과 주의 장소 정보를 찾고 있어요..."):
                origin = find_place(start.strip())
                target = find_place(destination.strip())

                if origin is None or target is None:
                    st.error(
                        "장소를 찾지 못했어요. "
                        "지역 이름을 포함해 더 자세히 입력해 주세요."
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
                        f"목적지는 {destination}입니다.",
                        "대중교통 경로를 확인하려면 아래 경로 열기 링크를 이용하세요.",
                        "승차역, 환승역, 하차역과 도착 안내는 연결된 지도 서비스에서 확인하세요."
                    ]

                    st.session_state.instructions = instructions
                    st.session_state.cautions = []
                    st.session_state.speech_text = " ".join(instructions)
                    st.session_state.route_map = None
                    st.session_state.transit_url = url
                    st.success("대중교통 경로 안내를 준비했어요!")

                else:
                    walking = transport == "🚶 도보"
                    routes = get_route(origin, target, walking)

                    if not routes:
                        st.error("경로를 찾지 못했어요. 다시 시도해 주세요.")
                    else:
                        route = routes[0]
                        instructions = make_instructions(route, walking)
                        cautions, caution_data_available = find_caution_places(route)

                        caution_sentences = [
                            item["message"] for item in cautions
                        ]

                        if not caution_data_available:
                            caution_sentences = [
                                "주의 장소 정보를 가져오지 못했습니다. "
                                "횡단보도와 계단 등 주변 위험을 별도로 확인해야 합니다."
                            ]
                        elif not cautions:
                            caution_sentences = [
                                "경로 주변에서 등록된 주의 장소 정보를 찾지 못했습니다. "
                                "이는 위험 장소가 없다는 뜻이 아닙니다. "
                                "주변을 계속 주의해 주세요."
                            ]

                        full_text = (
                            f"{transport[2:]} 경로 안내를 시작합니다. "
                            f"출발지는 {start}입니다. "
                            + " ".join(instructions)
                            + " 경로 주변 주의 안내입니다. "
                            + " ".join(caution_sentences)
                        )

                        st.session_state.instructions = instructions
                        st.session_state.cautions = cautions
                        st.session_state.speech_text = full_text
                        st.session_state.route_map = None
                        st.session_state.transit_url = None

                        route_map = folium.Map(
                            location=origin,
                            zoom_start=14,
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

                        coords = [
                            [p[1], p[0]]
                            for p in route["geometry"]["coordinates"]
                        ]

                        folium.PolyLine(
                            coords,
                            color="#8A83E8",
                            weight=6,
                            opacity=0.85,
                            tooltip="추천 경로"
                        ).add_to(route_map)

                        for item in cautions:
                            folium.Marker(
                                [item["lat"], item["lon"]],
                                tooltip=item["name"],
                                popup=item["message"],
                                icon=folium.Icon(
                                    color="orange",
                                    icon="warning-sign"
                                )
                            ).add_to(route_map)

                        route_map.fit_bounds(coords)
                        st.session_state.route_map = route_map
                        st.session_state.route_summary = (
                            f"예상 거리 {distance_text(route['distance'])}, "
                            f"예상 시간 {round(route['duration'] / 60)}분"
                        )

                        st.success("경로 안내를 준비했어요!")

        except requests.RequestException:
            st.error(
                "지도 서비스에 연결하지 못했어요. "
                "잠시 후 다시 시도해 주세요."
            )
        except (KeyError, ValueError, TypeError):
            st.error("경로 정보를 처리하지 못했어요. 다시 시도해 주세요.")

# -------------------------------
# 8. 결과 표시
# -------------------------------
if st.session_state.get("transit_url"):
    st.link_button(
        "🗺️ 대중교통 경로 자세히 보기",
        st.session_state.transit_url,
        use_container_width=True
    )

if st.session_state.route_map is not None:
    st.subheader("🗺️ 경로 지도")
    st.write(st.session_state.get("route_summary", ""))
    st_folium(
        st.session_state.route_map,
        height=400,
        use_container_width=True,
        key="route_map_display"
    )

st.subheader("🧭 단계별 음성 안내")

if st.session_state.instructions:
    for number, instruction in enumerate(
        st.session_state.instructions, 1
    ):
        st.markdown(f"**{number}.** {instruction}")

st.subheader("⚠️ 경로 주변 주의 장소")

if st.session_state.cautions:
    for item in st.session_state.cautions:
        st.warning(item["message"])
else:
    st.write(
        "등록된 주의 장소가 표시되지 않더라도 "
        "실제로 위험 장소가 없다는 뜻은 아니에요."
    )

# -------------------------------
# 9. 한국어 음성 안내
# -------------------------------
st.divider()
st.subheader("🔊 음성으로 안내 듣기")
st.write(
    "아래 버튼을 누르면 경로 안내와 주의 장소 안내를 "
    "한국어 음성으로 차례대로 읽어 줘요."
)

components.html(
    f"""
    <div style="
        background:#FFFFFF;
        border-radius:20px;
        padding:16px;
        font-family:sans-serif;
        border:1px solid #E4E0FF;">
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <button id="play" style="
          background:#DCD6FF;color:#35345A;border:0;
          border-radius:14px;padding:14px 18px;
          font-size:16px;font-weight:bold;cursor:pointer;">
          🔊 경로 전체 듣기
        </button>
        <button id="stop" style="
          background:#E2F2FF;color:#354C70;border:0;
          border-radius:14px;padding:14px 18px;
          font-size:16px;font-weight:bold;cursor:pointer;">
          ⏹️ 음성 중지
        </button>
      </div>
      <p id="status" style="font-size:14px;color:#536A9D;">
        음성 안내 버튼을 눌러 주세요.
      </p>
    </div>

    <script>
      const fullText = {json.dumps(st.session_state.speech_text, ensure_ascii=False)};
      const status = document.getElementById("status");
      let chunks = [];
      let current = 0;

      function speakNext() {{
        if (current >= chunks.length) {{
          status.textContent = "안내가 끝났어요.";
          return;
        }}

        const utterance = new SpeechSynthesisUtterance(chunks[current]);
        utterance.lang = "ko-KR";
        utterance.rate = 0.88;

        utterance.onstart = () => {{
          status.textContent =
            "🔊 음성 안내 중 (" + (current + 1) + "/" + chunks.length + ")";
        }};

        utterance.onend = () => {{
          current += 1;
          speakNext();
        }};

        utterance.onerror = () => {{
          status.textContent =
            "음성 재생에 문제가 생겼어요. 브라우저와 기기 음량을 확인해 주세요.";
        }};

        window.speechSynthesis.speak(utterance);
      }}

      document.getElementById("play").onclick = () => {{
        if (!("speechSynthesis" in window)) {{
          status.textContent =
            "현재 브라우저에서 음성 합성을 지원하지 않아요.";
          return;
        }}

        window.speechSynthesis.cancel();

        // 문장을 나누어 차례대로 읽기
        chunks = fullText.match(/[^.!?。]+[.!?。]?/g) || [fullText];
        chunks = chunks.map(x => x.trim()).filter(Boolean);
        current = 0;

        speakNext();
      }};

      document.getElementById("stop").onclick = () => {{
        window.speechSynthesis.cancel();
        current = chunks.length;
        status.textContent = "음성 안내를 중지했어요.";
      }};
    </script>
    """,
    height=125
)

st.caption(
    "이 앱은 경로 정보를 바탕으로 안내 문장을 만들고 읽어 주는 시제품입니다. "
    "GPS 실시간 추적, 경로 이탈 감지, 실제 횡단보도 신호 확인, "
    "계단의 실시간 감지는 구현되어 있지 않습니다. "
    "지도 정보가 누락되거나 부정확할 수 있으므로 실제 이동의 안전을 보장하지 않습니다."
)

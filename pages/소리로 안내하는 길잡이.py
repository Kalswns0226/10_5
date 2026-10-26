
import os
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
import folium

st.set_page_config(
    page_title="소리로 안내하는 길잡이",
    page_icon="🔊",
    layout="centered",
)

# 음성 입력 및 음성 안내 컴포넌트
COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "voice_component")
voice_component = components.declare_component(
    "voice_navigation_component",
    path=COMPONENT_DIR,
)

# 귀엽고 세련된 파스텔 디자인
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Noto+Sans+KR:wght@400;500;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}
.stApp {
    background: linear-gradient(145deg, #f4f8ff, #fbf7ff, #fff8fb);
}
.main .block-container {
    max-width: 850px;
    padding-top: 1.6rem;
}
.hero {
    background: rgba(255,255,255,.9);
    border: 1px solid #e5e9ff;
    border-radius: 24px;
    padding: 24px;
    text-align: center;
    box-shadow: 0 8px 24px rgba(91,105,170,.08);
}
.hero h1 {
    font-family: 'Jua', sans-serif;
    color: #505b9c;
    font-size: 2.2rem;
    margin: 0;
}
.hero p {
    color: #5e6481;
    margin-top: 8px;
}
.stButton button, .stFormSubmitButton button {
    min-height: 3rem;
    border-radius: 16px;
    font-weight: 700;
    border: 1px solid #d8defd;
    background: #edf0ff;
    color: #343d78;
}
.stTextInput input {
    min-height: 3rem;
    border-radius: 14px;
}
.info-card {
    background: white;
    border: 1px solid #e4e7fb;
    border-radius: 18px;
    padding: 15px 18px;
    margin: 8px 0;
}
.small-note {
    font-size: .9rem;
    color: #5f6682;
}
</style>

<div class="hero" role="region" aria-label="앱 소개">
    <h1>🔊 소리로 안내하는 길잡이</h1>
    <p>목적지를 말하면 길 안내와 주의 사항을 음성으로 알려드려요.</p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.markdown("### 🎙️ 음성으로 앱 사용하기")
st.caption(
    "사용 방법을 음성으로 듣고 목적지를 말할 수 있어요. "
    "마이크 권한과 브라우저 지원이 필요합니다."
)

voice_value = voice_component(
    key="voice_component",
    prompt=(
        "안녕하세요. 소리로 안내하는 길잡이입니다. "
        "목적지를 말하려면 목적지 말하기 버튼을 누른 뒤 "
        "목적지를 말씀해 주세요. 음성 인식이 되지 않으면 "
        "아래 입력창에 직접 입력할 수 있습니다."
    ),
    directions=[],
    caution="",
    height=180,
)

# 음성으로 인식한 목적지를 입력창에 전달
if isinstance(voice_value, dict):
    spoken_destination = str(
        voice_value.get("destination", "")
    ).strip()
else:
    spoken_destination = ""

if spoken_destination:
    st.session_state["destination_text"] = spoken_destination

st.markdown("### 📍 목적지 입력")
st.caption(
    "음성 입력이 되지 않으면 목적지를 직접 입력해도 됩니다."
)

with st.form("destination_form"):
    destination = st.text_input(
        "목적지",
        key="destination_text",
        placeholder="예: 두정역",
        help=(
            "목적지 이름이나 주소를 입력하세요. "
            "화면 읽기 기능을 사용할 수 있습니다."
        ),
    )
    submitted = st.form_submit_button(
        "목적지로 경로 찾기",
        use_container_width=True,
    )


def geocode(place):
    """장소 이름을 위도와 경도로 변환합니다."""
    url = "https://nominatim.openstreetmap.org/search"

    response = requests.get(
        url,
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "kr",
        },
        headers={
            "User-Agent": "VoiceNavigationSchoolPrototype/1.0"
        },
        timeout=15,
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    return (
        float(results[0]["lat"]),
        float(results[0]["lon"]),
        results[0].get("display_name", place),
    )


def get_route(start, end):
    """보행 경로 서비스에 경로를 요청합니다."""
    url = (
        "https://routing.openstreetmap.de/"
        "routed-foot/route/v1/driving/"
        f"{start[1]},{start[0]};{end[1]},{end[0]}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
        },
        headers={
            "User-Agent": "VoiceNavigationSchoolPrototype/1.0"
        },
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    return data["routes"][0]


def format_distance(meters):
    """거리를 읽기 쉬운 한국어로 표시합니다."""
    if meters < 1000:
        return f"{round(meters / 10) * 10}미터"

    return f"{meters / 1000:.1f}킬로미터"


def step_instruction(step):
    """지도 경로 정보를 음성 안내 문장으로 바꿉니다."""
    name = step.get("name") or ""
    maneuver = step.get("maneuver", {}) or {}
    typ = maneuver.get("type", "")
    mod = maneuver.get("modifier", "")

    if typ == "depart":
        text = "출발합니다."

    elif typ == "arrive":
        text = "목적지에 도착했습니다."

    elif typ == "turn":
        directions = {
            "left": "왼쪽으로",
            "right": "오른쪽으로",
            "slight left": "왼쪽으로 조금",
            "slight right": "오른쪽으로 조금",
            "sharp left": "왼쪽으로 크게",
            "sharp right": "오른쪽으로 크게",
            "uturn": "유턴하여",
        }
        turn = directions.get(mod, "방향을 바꾸어")
        text = f"{turn} 이동하세요."

    elif typ in ("roundabout", "rotary", "roundabout turn"):
        text = (
            "회전 구간입니다. "
            "주변을 주의 깊게 확인하세요."
        )

    elif typ in ("continue", "new name"):
        text = "계속 직진하세요."

    elif typ == "fork":
        if mod == "left":
            text = "갈림길에서 왼쪽으로 이동하세요."
        elif mod == "right":
            text = "갈림길에서 오른쪽으로 이동하세요."
        else:
            text = "갈림길에서 경로를 확인하세요."

    else:
        text = "경로를 따라 계속 이동하세요."

    if name:
        text += f" 주변 길 이름은 {name}입니다."

    distance = step.get("distance", 0) or 0

    if distance >= 15 and typ != "arrive":
        text = (
            f"앞으로 약 {format_distance(distance)} 이동하세요. "
            + text
        )

    return text


# 목적지 경로 찾기
if submitted:
    place = destination.strip()

    if not place:
        st.warning("목적지를 말하거나 입력해 주세요.")

    else:
        with st.spinner("목적지와 경로를 확인하고 있어요..."):
            try:
                # 시연을 위해 출발지는 서울역으로 고정합니다.
                start_result = geocode("서울역")
                end_result = geocode(place)

                if not start_result or not end_result:
                    st.error(
                        "장소를 찾지 못했어요. "
                        "더 구체적인 장소 이름이나 주소를 입력해 주세요."
                    )

                else:
                    route = get_route(
                        start_result[:2],
                        end_result[:2],
                    )

                    if not route:
                        st.error(
                            "현재 보행 경로 서비스를 사용할 수 없어요. "
                            "잠시 후 다시 시도해 주세요."
                        )

                    else:
                        coordinates = route["geometry"]["coordinates"]
                        latlon = [
                            [lat, lon]
                            for lon, lat in coordinates
                        ]

                        steps = [
                            step_instruction(step)
                            for leg in route.get("legs", [])
                            for step in leg.get("steps", [])
                        ]

                        st.session_state["route_data"] = {
                            "destination": place,
                            "distance": route.get("distance", 0),
                            "duration": route.get("duration", 0),
                            "steps": steps,
                            "latlon": latlon,
                            "start": list(start_result[:2]),
                            "end": list(end_result[:2]),
                        }

            except requests.RequestException:
                st.error(
                    "인터넷 연결 또는 지도 서비스에 문제가 있어요. "
                    "잠시 후 다시 시도해 주세요."
                )

            except (ValueError, KeyError, TypeError):
                st.error(
                    "경로 정보를 읽는 중 문제가 생겼어요. "
                    "다른 목적지를 입력해 다시 시도해 주세요."
                )


# 경로 결과 표시
route_data = st.session_state.get("route_data")

if route_data:
    st.markdown("### 🧭 경로 안내")

    st.markdown(
        f"""
        <div class="info-card">
            <b>출발지:</b> 서울역<br>
            <b>도착지:</b> {route_data["destination"]}<br>
            <b>예상 거리:</b> 약 {format_distance(route_data["distance"])}<br>
            <b>예상 시간:</b> 약 {max(1, round(route_data["duration"] / 60))}분
            <p class="small-note">
                출발지는 시연을 위해 서울역으로 고정되어 있습니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    directions = route_data["steps"]

    caution_text = (
        "주의하세요. 지도에 표시되지 않은 횡단보도, 계단, "
        "공사 구간이나 장애물이 있을 수 있습니다. "
        "실제로 이동할 때는 주변 상황을 확인하고 "
        "필요하면 동행인이나 현장 안내를 이용하세요."
    )

    all_spoken = (
        "경로 안내를 시작합니다. "
        + " ".join(directions)
        + " "
        + caution_text
    )

    voice_component(
        key="route_voice_component",
        prompt=all_spoken,
        directions=directions,
        caution=caution_text,
        height=240,
    )

    with st.expander("음성 안내 내용을 글로 확인하기"):
        for number, instruction in enumerate(directions, 1):
            st.write(f"{number}. {instruction}")

        st.info(caution_text)

    # 경로 지도
    if route_data.get("latlon"):
        map_view = folium.Map(
            location=route_data["start"],
            zoom_start=13,
            control_scale=True,
        )

        folium.PolyLine(
            route_data["latlon"],
            color="#7585d8",
            weight=6,
            opacity=0.8,
        ).add_to(map_view)

        folium.Marker(
            route_data["start"],
            tooltip="출발지: 서울역",
            popup="출발지: 서울역",
        ).add_to(map_view)

        folium.Marker(
            route_data["end"],
            tooltip=f"도착지: {route_data['destination']}",
            popup=f"도착지: {route_data['destination']}",
        ).add_to(map_view)

        st_folium(
            map_view,
            width=None,
            height=300,
            returned_objects=[],
        )


st.markdown("---")
st.markdown("### ♿ 접근성과 안전 안내")

st.write(
    "- VoiceOver와 TalkBack 같은 화면 읽기 기능을 함께 사용할 수 있도록 구성했습니다."
)
st.write(
    "- 음성 인식은 브라우저 지원 여부와 마이크 권한에 따라 달라질 수 있습니다."
)
st.write(
    "- 현재 위치 실시간 추적이나 이동 중 자동 방향 재안내는 구현되어 있지 않습니다."
)
st.write(
    "- 지도 데이터에 모든 횡단보도, 계단, 공사 구간과 장애물이 포함된다는 보장은 없습니다."
)
st.warning(
    "이 앱은 학교 프로젝트용 시제품입니다. "
    "실제 보행 안전을 보장하지 않으므로 실제 길 안내에 의존하지 마세요."
)
st.caption(
    "OpenStreetMap 기반 · 인터넷 연결 필요 · 수행평가용 시제품"
)


import json
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="소리로 안내하는 길잡이",
    page_icon="🔊",
    layout="centered"
)

# 귀엽고 세련된 디자인
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Noto+Sans+KR&display=swap');

.stApp {
    background: linear-gradient(135deg, #f1f6ff, #fbf5ff, #fff8fb);
}
.block-container {
    max-width: 850px;
    padding-top: 2rem;
}
.title-card {
    background: white;
    border: 2px solid #e2e7ff;
    border-radius: 24px;
    padding: 25px;
    text-align: center;
}
.title-card h1 {
    font-family: 'Jua', sans-serif;
    color: #5968ad;
}
.stButton button, .stFormSubmitButton button {
    min-height: 48px;
    border-radius: 15px;
    background: #e9edff;
    color: #35427f;
    font-weight: bold;
    border: 1px solid #d4dcff;
}
</style>

<div class="title-card" role="region" aria-label="앱 소개">
    <h1>🔊 소리로 안내하는 길잡이</h1>
    <p>목적지까지 음성으로 안내해 드려요.</p>
    <p>💜 길 안내와 안전 주의 사항을 확인해 보세요.</p>
</div>
""", unsafe_allow_html=True)


# 브라우저 음성 안내
def speak_panel(message, label="음성 안내"):
    safe_message = json.dumps(message, ensure_ascii=False)

    html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: sans-serif;
            color: #35427f;
            margin: 0;
        }
        .panel {
            background: white;
            border: 1px solid #dfe5ff;
            border-radius: 18px;
            padding: 14px;
        }
        button {
            min-height: 48px;
            margin: 4px;
            padding: 10px 15px;
            border-radius: 14px;
            border: 1px solid #d4dcff;
            background: #e9edff;
            color: #35427f;
            font-size: 16px;
            font-weight: bold;
        }
        button:focus {
            outline: 3px solid #5268c8;
            outline-offset: 2px;
        }
        .status {
            margin: 10px 4px;
            line-height: 1.6;
        }
    </style>
    </head>
    <body>
    <div class="panel" role="region" aria-label="음성 안내">
        <button id="play" aria-label="안내 음성 듣기">
            🔊 안내 듣기
        </button>
        <button id="repeat" aria-label="안내 음성 다시 듣기">
            🔁 다시 듣기
        </button>
        <button id="stop" aria-label="안내 음성 멈추기">
            ⏹️ 멈추기
        </button>
        <div id="status" class="status" role="status" aria-live="polite">
            안내를 들으려면 버튼을 눌러 주세요.
        </div>
    </div>

    <script>
    const message = MESSAGE_PLACEHOLDER;
    const status = document.getElementById("status");

    function playSpeech() {
        if (!("speechSynthesis" in window)) {
            status.textContent =
                "이 브라우저는 음성 읽기를 지원하지 않습니다.";
            return;
        }

        window.speechSynthesis.cancel();

        const speech = new SpeechSynthesisUtterance(message);
        speech.lang = "ko-KR";
        speech.rate = 0.9;

        speech.onstart = () => {
            status.textContent = "음성 안내 중입니다.";
        };

        speech.onend = () => {
            status.textContent = "음성 안내가 끝났습니다.";
        };

        speech.onerror = () => {
            status.textContent =
                "음성 재생에 실패했습니다. 기기 설정을 확인해 주세요.";
        };

        window.speechSynthesis.speak(speech);
    }

    document.getElementById("play").onclick = playSpeech;
    document.getElementById("repeat").onclick = playSpeech;

    document.getElementById("stop").onclick = () => {
        window.speechSynthesis.cancel();
        status.textContent = "음성 안내를 멈췄습니다.";
    };
    </script>
    </body>
    </html>
    """

    html = html.replace("MESSAGE_PLACEHOLDER", safe_message)

    components.html(html, height=150, scrolling=False)


st.markdown("### 🎧 앱 사용 방법")

speak_panel(
    "안녕하세요. 소리로 안내하는 길잡이입니다. "
    "목적지를 입력하고 경로 찾기 버튼을 누르면 "
    "길 안내를 확인할 수 있습니다. "
    "안내 듣기 버튼을 눌러 음성으로 들을 수 있습니다."
)

st.markdown("### 📍 목적지 입력")

st.caption(
    "현재 위치를 자동으로 찾지 않으므로 "
    "이 시연에서는 출발지를 서울역으로 사용합니다."
)

with st.form("route_form"):
    destination = st.text_input(
        "도착할 장소",
        placeholder="예: 두정역",
        help="도착할 장소의 이름이나 주소를 입력하세요."
    )

    submitted = st.form_submit_button(
        "🧭 경로 찾기",
        use_container_width=True
    )


# 장소 검색
def geocode(place):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "kr"
        },
        headers={
            "User-Agent": "SchoolVoiceNavigationPrototype/1.0"
        },
        timeout=20
    )

    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    return (
        float(results[0]["lat"]),
        float(results[0]["lon"]),
        results[0].get("display_name", place)
    )


# 보행 경로 검색
def find_route(start, end):
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
            "steps": "true"
        },
        headers={
            "User-Agent": "SchoolVoiceNavigationPrototype/1.0"
        },
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    return data["routes"][0]


# 지도 안내 문장을 음성용 문장으로 변경
def make_instruction(step):
    maneuver = step.get("maneuver", {})
    kind = maneuver.get("type", "")
    modifier = maneuver.get("modifier", "")
    street = step.get("name", "")
    distance = step.get("distance", 0) or 0

    if kind == "depart":
        message = "출발합니다."
    elif kind == "arrive":
        message = "목적지에 도착했습니다."
    elif kind == "turn":
        turns = {
            "left": "왼쪽으로",
            "right": "오른쪽으로",
            "slight left": "왼쪽으로 조금",
            "slight right": "오른쪽으로 조금",
            "sharp left": "왼쪽으로 크게",
            "sharp right": "오른쪽으로 크게",
            "uturn": "유턴하여"
        }
        message = turns.get(modifier, "방향을 바꾸어")
        message += " 이동하세요."
    elif kind in ("roundabout", "rotary"):
        message = "회전 구간입니다. 주변을 주의 깊게 확인하세요."
    elif kind == "fork":
        if modifier == "left":
            message = "갈림길에서 왼쪽으로 이동하세요."
        elif modifier == "right":
            message = "갈림길에서 오른쪽으로 이동하세요."
        else:
            message = "갈림길에서 경로를 확인하세요."
    else:
        message = "경로를 따라 계속 이동하세요."

    if distance >= 15:
        if distance < 1000:
            distance_text = f"{round(distance / 10) * 10}미터"
        else:
            distance_text = f"{distance / 1000:.1f}킬로미터"

        message = f"앞으로 약 {distance_text} 이동하세요. " + message

    if street:
        message += f" 길 이름은 {street}입니다."

    return message


# 경로 계산
if submitted:
    if not destination.strip():
        st.warning("도착할 장소를 입력해 주세요.")
    else:
        try:
            with st.spinner("경로를 확인하고 있어요..."):
                start_place = geocode("서울역")
                end_place = geocode(destination.strip())

                if not start_place or not end_place:
                    st.error("장소를 찾지 못했어요. 이름이나 주소를 확인해 주세요.")
                else:
                    route = find_route(
                        start_place[:2],
                        end_place[:2]
                    )

                    if not route:
                        st.error("경로를 찾지 못했어요. 잠시 후 다시 시도해 주세요.")
                    else:
                        steps = [
                            make_instruction(step)
                            for leg in route.get("legs", [])
                            for step in leg.get("steps", [])
                        ]

                        st.session_state["route_result"] = {
                            "destination": destination.strip(),
                            "start": list(start_place[:2]),
                            "end": list(end_place[:2]),
                            "distance": route.get("distance", 0),
                            "duration": route.get("duration", 0),
                            "steps": steps,
                            "coordinates": [
                                [lat, lon]
                                for lon, lat in
                                route["geometry"]["coordinates"]
                            ]
                        }

        except requests.RequestException:
            st.error(
                "인터넷 또는 지도 서비스에 연결할 수 없어요. "
                "잠시 후 다시 시도해 주세요."
            )
        except (ValueError, KeyError, TypeError):
            st.error("경로 정보를 처리하는 중 오류가 발생했어요.")


# 결과 출력
result = st.session_state.get("route_result")

if result:
    st.markdown("### 💜 목적지까지의 안내")

    distance = result["distance"]
    if distance < 1000:
        distance_text = f"{round(distance)}미터"
    else:
        distance_text = f"{distance / 1000:.1f}킬로미터"

    duration_text = max(1, round(result["duration"] / 60))

    st.markdown(
        f"""
        <div class="title-card">
            <p><b>출발지:</b> 서울역</p>
            <p><b>도착지:</b> {result["destination"]}</p>
            <p><b>예상 거리:</b> 약 {distance_text}</p>
            <p><b>예상 시간:</b> 약 {duration_text}분</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    caution = (
        "주의하세요. 지도에 표시되지 않은 횡단보도, 계단, "
        "공사 구간이나 장애물이 있을 수 있습니다. "
        "실제 이동 시 주변 상황을 확인하세요. "
        "이 앱은 현재 위치를 추적하지 않으므로 "
        "안내가 실제 위치와 다를 수 있습니다."
    )

    speech_text = (
        "경로 안내를 시작합니다. "
        + " ".join(result["steps"])
        + " "
        + caution
    )

    speak_panel(speech_text, "경로 음성 안내")

    st.markdown("### 📝 경로 안내 내용")

    for number, instruction in enumerate(result["steps"], 1):
        st.write(f"{number}. {instruction}")

    st.warning(caution)

    map_view = folium.Map(
        location=result["start"],
        zoom_start=13
    )

    folium.PolyLine(
        result["coordinates"],
        color="#7585d8",
        weight=6
    ).add_to(map_view)

    folium.Marker(
        result["start"],
        tooltip="출발지: 서울역"
    ).add_to(map_view)

    folium.Marker(
        result["end"],
        tooltip=f"도착지: {result['destination']}"
    ).add_to(map_view)

    st_folium(
        map_view,
        width=None,
        height=350,
        returned_objects=[]
    )


st.markdown("---")
st.markdown("### ♿ 접근성과 안전")

st.write(
    "- 버튼과 입력창에 화면 읽기용 설명을 추가했습니다."
)
st.write(
    "- 아이폰 VoiceOver와 안드로이드 TalkBack을 켜서 조작할 수 있습니다."
)
st.write(
    "- 음성 안내는 브라우저의 한국어 음성 지원 여부에 따라 달라질 수 있습니다."
)
st.write(
    "- 이 시제품은 실시간 위치 추적, 자동 방향 재안내, "
    "횡단보도와 계단의 완전한 감지를 지원하지 않습니다."
)

st.warning(
    "학교 프로젝트용 시제품입니다. 실제 보행 시 이 안내만 믿고 이동하지 마세요."
)

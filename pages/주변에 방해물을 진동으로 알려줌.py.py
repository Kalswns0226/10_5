
import json
import math
import html
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="안심길 | 음성 안전 길안내",
    page_icon="🦯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp { background: #f4f7fa; color: #132536; }
.block-container { max-width: 1100px; padding-top: 1.5rem; }
h1, h2, h3 { color: #12344a; }
.stButton button, .stFormSubmitButton button {
    min-height: 52px; font-size: 18px; font-weight: 700;
    border-radius: 12px;
}
.stTextInput input, .stTextArea textarea {
    font-size: 17px; min-height: 48px;
}
.notice {
    background: #e5f1fa; padding: 16px;
    border-left: 6px solid #17658b; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🦯 안심길")
st.subheader("음성으로 듣는 보행 경로 안내")
st.markdown("""
<div class="notice">
<strong>안전 안내</strong><br>
이 앱은 등록된 장애물 위치를 기준으로 경고합니다.
주변의 모든 장애물을 자동으로 감지하지는 않습니다.
이 앱만 믿고 이동하지 말고 흰지팡이, 안내견 및
필요한 보행 지원을 함께 이용하세요.
</div>
""", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "AnsimgilAccessibleNavigation/1.0"
}
TIMEOUT = 12


def geocode(address):
    """주소를 위도·경도로 변환합니다."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": address,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "kr",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(
            f"주소를 찾을 수 없습니다: {address}"
        )

    return [
        float(results[0]["lon"]),
        float(results[0]["lat"]),
    ]


def get_route(start, end):
    """OSRM에서 도보 경로 정보를 요청합니다."""
    coordinates = (
        f"{start[0]},{start[1]};"
        f"{end[0]},{end[1]}"
    )
    response = requests.get(
        "https://router.project-osrm.org/route/v1/"
        f"driving/{coordinates}",
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "false",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("경로를 찾을 수 없습니다.")

    route = data["routes"][0]
    return route


def parse_obstacles(text):
    """
    한 줄에 하나씩 다음 형식으로 입력합니다.
    장애물 설명 | 위도 | 경도
    예: 공사 구간 | 37.5665 | 126.9780
    """
    obstacles = []

    for line_number, line in enumerate(
        text.splitlines(), start=1
    ):
        line = line.strip()
        if not line:
            continue

        parts = [part.strip() for part in line.split("|")]

        if len(parts) != 3:
            raise ValueError(
                f"{line_number}번째 줄 형식이 잘못되었습니다. "
                "설명 | 위도 | 경도로 입력하세요."
            )

        name = parts[0]
        try:
            lat = float(parts[1])
            lon = float(parts[2])
        except ValueError:
            raise ValueError(
                f"{line_number}번째 줄의 위도·경도를 확인하세요."
            )

        if not name or not (-90 <= lat <= 90) or not (
            -180 <= lon <= 180
        ):
            raise ValueError(
                f"{line_number}번째 줄의 장애물 정보를 확인하세요."
            )

        obstacles.append({
            "name": name,
            "lat": lat,
            "lon": lon,
        })

    return obstacles


def haversine_m(lat1, lon1, lat2, lon2):
    """두 GPS 좌표 사이의 직선거리를 미터로 계산합니다."""
    radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )
    return 2 * radius * math.asin(
        min(1.0, math.sqrt(a))
    )


with st.form("route_form"):
    st.markdown("### 1. 이동 경로 설정")

    start_address = st.text_input(
        "출발지",
        placeholder="예: 서울시청",
    )
    destination_address = st.text_input(
        "목적지",
        placeholder="예: 서울역",
    )

    obstacle_text = st.text_area(
        "2. 알고 있는 장애물 위치 (선택)",
        placeholder=(
            "공사 구간 | 37.5665 | 126.9780\n"
            "보도 위 장애물 | 37.5659 | 126.9772"
        ),
        help=(
            "각 줄에 장애물 설명 | 위도 | 경도를 입력하세요. "
            "실제 위치를 확인한 정보만 등록하세요."
        ),
        height=110,
    )

    submitted = st.form_submit_button(
        "경로 찾기",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not start_address.strip() or not destination_address.strip():
        st.error("출발지와 목적지를 모두 입력해 주세요.")
    else:
        try:
            with st.spinner("주소와 경로를 확인하고 있습니다..."):
                start = geocode(start_address.strip())
                end = geocode(destination_address.strip())
                route = get_route(start, end)
                obstacles = parse_obstacles(obstacle_text)

            st.session_state["route_data"] = {
                "start": start,
                "end": end,
                "route": route,
                "obstacles": obstacles,
                "start_name": start_address.strip(),
                "end_name": destination_address.strip(),
            }
            st.success("경로를 불러왔습니다.")

        except ValueError as exc:
            st.error(str(exc))
        except requests.exceptions.Timeout:
            st.error(
                "지도 서버 응답이 지연되고 있습니다. "
                "잠시 후 다시 시도해 주세요."
            )
        except requests.exceptions.RequestException:
            st.error(
                "주소 또는 경로 서버에 연결할 수 없습니다. "
                "인터넷 연결을 확인하고 다시 시도해 주세요."
            )
        except Exception:
            st.error(
                "처리 중 문제가 발생했습니다. "
                "입력 정보를 확인하고 다시 시도해 주세요."
            )

data = st.session_state.get("route_data")

if data:
    route = data["route"]
    distance_km = route["distance"] / 1000
    duration_min = route["duration"] / 60

    col1, col2, col3 = st.columns(3)
    col1.metric("경로 거리", f"{distance_km:.2f} km")
    col2.metric("예상 이동 시간", f"{duration_min:.0f}분")
    col3.metric("등록된 장애물", f"{len(data['obstacles'])}개")

    st.markdown("### 3. 지도 및 음성 안내")
    st.caption(
        "지도는 참고용입니다. 실제 보행 가능 여부와 "
        "보도 상태는 현장에서 확인해야 합니다."
    )

    route_geojson = route["geometry"]["coordinates"]

    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            name = step.get("name") or "이름 없는 도로"
            maneuver = step.get("maneuver", {})
            instruction = maneuver.get("instruction", "")
            modifier = maneuver.get("modifier", "")
            kind = maneuver.get("type", "")

            if instruction:
                text = instruction
            elif kind == "arrive":
                text = "목적지에 도착했습니다."
            elif kind == "depart":
                text = f"{name}에서 출발하세요."
            elif modifier:
                text = f"{name}에서 {modifier} 방향으로 이동하세요."
            else:
                text = f"{name} 방향으로 계속 이동하세요."

            steps.append({
                "text": text,
                "distance": step.get("distance", 0),
            })

    map_payload = {
        "route": route_geojson,
        "start": data["start"],
        "end": data["end"],
        "obstacles": data["obstacles"],
        "steps": steps,
    }

    payload_json = json.dumps(
        map_payload, ensure_ascii=False
    ).replace("</", "<\\/")

    map_html = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet"
 href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
body { margin:0; font-family:Arial,sans-serif; color:#102a3a; }
#map { height:390px; width:100%; border-radius:12px; }
.panel { padding:12px 4px; }
button {
  width:100%; min-height:54px; margin:5px 0;
  border:0; border-radius:10px; font-size:18px;
  font-weight:bold; background:#123e56; color:white;
}
button.secondary { background:#e1edf4; color:#12344a; }
#status { font-size:17px; line-height:1.7; }
#current { font-size:15px; }
</style>
</head>
<body>
<div class="panel">
  <button id="startVoice">음성 안내 및 GPS 시작</button>
  <button id="testVoice" class="secondary">음성 테스트</button>
  <button id="stopVoice" class="secondary">음성 안내 중지</button>
  <div id="status" role="status" aria-live="polite">
    GPS 시작 버튼을 누른 뒤 위치 권한을 허용하세요.
  </div>
  <div id="current"></div>
</div>
<div id="map" aria-label="이동 경로 지도"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const data = __PAYLOAD__;
const statusEl = document.getElementById("status");
const currentEl = document.getElementById("current");
let watchId = null;
let announced = new Set();
let lastNav = -1;
let lastNavTime = 0;
let map = null;

function speak(message) {
  if (!("speechSynthesis" in window)) {
    statusEl.textContent = "이 브라우저는 음성 안내를 지원하지 않습니다.";
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(message);
  utterance.lang = "ko-KR";
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}

function distanceM(lat1, lon1, lat2, lon2) {
  const rad = Math.PI / 180;
  const dLat = (lat2-lat1)*rad;
  const dLon = (lon2-lon1)*rad;
  const a = Math.sin(dLat/2)**2 +
    Math.cos(lat1*rad)*Math.cos(lat2*rad)*
    Math.sin(dLon/2)**2;
  return 6371000*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}

function nearestRouteIndex(lat, lon) {
  let best = 0, bestDist = Infinity;
  data.route.forEach((p,i) => {
    const d = distanceM(lat,lon,p[1],p[0]);
    if (d < bestDist) { bestDist=d; best=i; }
  });
  return {index:best, distance:bestDist};
}

function handlePosition(position) {
  const lat = position.coords.latitude;
  const lon = position.coords.longitude;
  const accuracy = position.coords.accuracy || 999;

  currentEl.textContent =
    "GPS 정확도 약 " + Math.round(accuracy) + "m";

  if (map) {
    L.circleMarker([lat,lon], {
      radius:8, color:"#005b96", fillOpacity:1
    }).addTo(map).bindPopup("현재 위치");
  }

  const nearest = nearestRouteIndex(lat,lon);
  if (nearest.distance > 50) {
    statusEl.textContent =
      "경로에서 벗어났을 수 있습니다. 주변을 확인하세요.";
  } else {
    statusEl.textContent = "GPS 위치를 확인하고 있습니다.";
  }

  // 장애물 위치는 사용자가 직접 등록한 정보입니다.
  // 초당 1.2m 보행을 가정해 약 5초 전 경고를 시도합니다.
  // GPS 오차 및 실제 이동 방향 때문에 정확한 5초를 보장하지 않습니다.
  const speed = 1.2;
  const warningDistance = speed * 5 + 2;

  data.obstacles.forEach((obstacle, i) => {
    const d = distanceM(
      lat,lon,obstacle.lat,obstacle.lon
    );
    if (d <= warningDistance && !announced.has(i)) {
      announced.add(i);
      const message =
        "주의. 약 " + Math.round(d) + "미터 앞에 등록된 장애물, " +
        obstacle.name + "이 있습니다. 주변을 확인하세요.";
      statusEl.textContent = message;
      speak(message);
    }
  });

  // 가장 가까운 경로 지점을 기준으로 다음 안내를 읽습니다.
  if (data.steps.length && nearest.index > lastNav &&
      Date.now()-lastNavTime > 7000) {
    const ratio = nearest.index / Math.max(1,data.route.length-1);
    const stepIndex = Math.min(
      data.steps.length-1,
      Math.floor(ratio*data.steps.length)
    );
    if (stepIndex > lastNav) {
      lastNav = stepIndex;
      lastNavTime = Date.now();
      speak(data.steps[stepIndex].text);
    }
  }
}

function startGPS() {
  if (!navigator.geolocation) {
    statusEl.textContent = "이 브라우저는 GPS 위치 기능을 지원하지 않습니다.";
    return;
  }
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
  }
  announced = new Set();
  statusEl.textContent = "GPS 권한을 확인하고 있습니다.";

  watchId = navigator.geolocation.watchPosition(
    handlePosition,
    function(error) {
      const messages = {
        1: "위치 권한이 거부되었습니다. 브라우저 설정을 확인하세요.",
        2: "현재 위치를 확인할 수 없습니다.",
        3: "GPS 응답 시간이 초과되었습니다."
      };
      statusEl.textContent =
        messages[error.code] || "GPS 오류가 발생했습니다.";
    },
    {enableHighAccuracy:true, maximumAge:1000, timeout:15000}
  );
}

document.getElementById("startVoice").addEventListener("click", function() {
  speak("안심길 음성 안내를 시작합니다. 주변을 확인하며 이동하세요.");
  startGPS();
});

document.getElementById("testVoice").addEventListener("click", function() {
  speak("음성 안내 테스트입니다. 앞에 장애물이 있을 수 있습니다. 주의하세요.");
});

document.getElementById("stopVoice").addEventListener("click", function() {
  if (watchId !== null) navigator.geolocation.clearWatch(watchId);
  watchId = null;
  window.speechSynthesis.cancel();
  statusEl.textContent = "음성 안내가 중지되었습니다.";
});

try {
  map = L.map("map").setView(
    [data.start[1],data.start[0]], 16
  );
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom:19,
    attribution:"&copy; OpenStreetMap contributors"
  }).addTo(map);

  const routeLatLngs = data.route.map(p => [p[1],p[0]]);
  const line = L.polyline(routeLatLngs, {
    color:"#075985", weight:6
  }).addTo(map);

  L.marker([data.start[1],data.start[0]])
    .addTo(map).bindPopup("출발지");
  L.marker([data.end[1],data.end[0]])
    .addTo(map).bindPopup("목적지");

  data.obstacles.forEach(o => {
    L.circleMarker([o.lat,o.lon], {
      radius:9, color:"#b91c1c", fillColor:"#ef4444",
      fillOpacity:0.9
    }).addTo(map).bindPopup("등록된 장애물: " + o.name);
  });

  map.fitBounds(line.getBounds(), {padding:[20,20]});
} catch (e) {
  statusEl.textContent =
    "지도를 표시할 수 없습니다. 인터넷 연결을 확인하세요.";
}
</script>
</body>
</html>
""".replace("__PAYLOAD__", payload_json)

    components.html(map_html, height=590, scrolling=False)

    st.markdown("### 4. 이동 안내 순서")
    if steps:
        for i, step in enumerate(steps, start=1):
            st.markdown(
                f"**{i}.** {html.escape(step['text'])} "
                f"({step['distance']:.0f}m)"
            )
    else:
        st.info("표시할 세부 경로 안내가 없습니다.")

    st.caption(
        "안내 순서는 전체 경로의 진행 상황을 단순화해 추정합니다. "
        "실제 교차로별 실시간 내비게이션과 같지 않을 수 있습니다."
    )

st.divider()
st.markdown("### 사용 전 확인")
st.markdown("""
- GPS와 음성 안내는 HTTPS 환경에서 브라우저 권한이 필요합니다.
- 장애물 위치는 자동 탐지되지 않습니다. 직접 등록한 정보만 사용합니다.
- GPS 오차, 보행 속도, 네트워크 지연으로 5초 전 경고가 보장되지 않습니다.
- 지도와 경로는 보행로, 계단, 공사, 신호등 및 접근성 상태를
  모두 반영하지 않을 수 있습니다.
- 실제 이동 중에는 이 앱만을 안전 수단으로 사용하지 마세요.
""")

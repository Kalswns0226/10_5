
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>소리로 안내하는 길잡이</title>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Arial, sans-serif;
  background: #f2f7ff;
  color: #243b65;
}

header {
  padding: 24px 20px;
  background: linear-gradient(135deg, #d9ecff, #eee6ff);
  text-align: center;
  border-radius: 0 0 28px 28px;
}

.logo {
  font-size: 38px;
}

h1 {
  font-size: 25px;
  margin: 8px 0;
}

header p {
  color: #657da6;
  margin: 0;
}

main {
  max-width: 480px;
  margin: 20px auto;
  padding: 0 16px;
}

.card {
  background: white;
  border-radius: 22px;
  padding: 22px;
  margin-bottom: 16px;
  box-shadow: 0 5px 20px #dce8f5;
}

h2 {
  font-size: 19px;
  margin-top: 0;
}

label {
  display: block;
  margin: 14px 0 7px;
  color: #7185a8;
  font-size: 14px;
}

input {
  width: 100%;
  padding: 14px;
  border: 1px solid #dce7f6;
  border-radius: 13px;
  font-size: 16px;
  color: #243b65;
  background: #fbfdff;
}

button {
  width: 100%;
  padding: 15px;
  border: none;
  border-radius: 15px;
  background: #4388f5;
  color: white;
  font-size: 16px;
  font-weight: bold;
  margin-top: 14px;
  cursor: pointer;
}

button:active {
  transform: scale(0.98);
}

.secondary {
  background: #e9f2ff;
  color: #3477df;
}

#map {
  width: 100%;
  height: 300px;
  border-radius: 16px;
  background: #e9f2ff;
  margin-top: 14px;
}

#result {
  white-space: pre-line;
  line-height: 1.8;
  font-size: 15px;
}

.notice {
  background: #f1edff;
  color: #7460b8;
  padding: 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
}

footer {
  text-align: center;
  color: #8294b1;
  font-size: 12px;
  padding: 15px;
}
</style>

<link rel="stylesheet"
 href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
</head>

<body>
<header>
  <div class="logo">🔊 ☁️</div>
  <h1>소리로 안내하는 길잡이</h1>
  <p>작은 소리로 더 안전한 이동을 도와요 💙</p>
</header>

<main>
  <section class="card">
    <h2>📍 경로 설정</h2>

    <label for="start">출발지</label>
    <input id="start" value="서울역">

    <label for="end">도착지</label>
    <input id="end" value="두정역">

    <button onclick="findRoute()">🧭 경로 검색하기</button>
    <div id="result" aria-live="polite">
      출발지와 도착지를 확인한 뒤 검색해 주세요.
    </div>
  </section>

  <section class="card">
    <h2>🗺️ 경로 지도</h2>
    <div id="map" aria-label="경로 지도"></div>
  </section>

  <section class="card">
    <h2>🎧 음성 안내</h2>
    <p>화면에 표시된 안내를 음성으로 읽어 줘요.</p>
    <button onclick="speakGuide()">▶ 음성 안내 시작</button>
    <button class="secondary" onclick="stopGuide()">
      ■ 음성 안내 정지
    </button>
    <p id="voiceStatus" aria-live="polite"></p>
  </section>

  <section class="card">
    <h2>🛡️ 안전 안내</h2>
    <p class="notice">
      🚦 횡단보도에서는 보행 신호를 확인해 주세요.<br>
      🪜 계단이나 높이 차이가 있는 곳에서는 주의해 주세요.<br>
      💜 이 안내는 위험 요소를 실시간으로 감지하지는 않아요.
    </p>
  </section>
</main>

<footer>
  소리로 안내하는 길잡이 · 학교 프로젝트용 체험판
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
const map = L.map("map").setView([36.5, 127.5], 7);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

let routeLayer;
let markers = [];
let guideText = "";

async function findRoute() {
  const start = document.getElementById("start").value.trim();
  const end = document.getElementById("end").value.trim();
  const result = document.getElementById("result");

  if (!start || !end) {
    result.textContent = "출발지와 도착지를 모두 입력해 주세요.";
    return;
  }

  result.textContent = "🔎 장소와 경로를 검색하고 있어요...";

  try {
    async function locate(place) {
      const url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
        + encodeURIComponent(place + ", South Korea");

      const response = await fetch(url);
      if (!response.ok) throw new Error("장소 검색 실패");

      const data = await response.json();
      if (!data.length) throw new Error(place + "을(를) 찾지 못했어요.");

      return [
        Number(data[0].lat),
        Number(data[0].lon)
      ];
    }

    const a = await locate(start);
    await new Promise(resolve => setTimeout(resolve, 1100));
    const b = await locate(end);

    const url =
      `https://routing.openstreetmap.de/routed-foot/route/v1/driving/${a[1]},${a[0]};${b[1]},${b[0]}?overview=full&geometries=geojson&steps=true`;

    const response = await fetch(url);
    if (!response.ok) throw new Error("경로 서버에 연결하지 못했어요.");

    const data = await response.json();
    if (!data.routes || !data.routes.length) {
      throw new Error("경로를 찾지 못했어요.");
    }

    const route = data.routes[0];

    if (routeLayer) map.removeLayer(routeLayer);
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    routeLayer = L.geoJSON(route.geometry, {
      style: { color: "#4388f5", weight: 6 }
    }).addTo(map);

    markers.push(
      L.marker(a).addTo(map).bindPopup("출발: " + start),
      L.marker(b).addTo(map).bindPopup("도착: " + end)
    );

    map.fitBounds(routeLayer.getBounds(), { padding: [20, 20] });

    const km = (route.distance / 1000).toFixed(1);
    const mins = Math.round(route.duration / 60);

    guideText = start + "에서 출발합니다. "
      + end + "까지 경로 안내를 시작합니다. "
      + "검색된 경로는 약 " + km + "킬로미터입니다. "
      + "예상 시간은 약 " + mins + "분입니다. "
      + "이동 중에는 주변 상황과 보행 신호를 꼭 확인해 주세요.";

    result.textContent =
      "📍 " + start + " → " + end +
      "\n📏 경로 거리: 약 " + km + "km" +
      "\n⏱️ 예상 시간: 약 " + mins + "분" +
      "\n\n" + guideText;

  } catch (error) {
    result.textContent =
      "경로를 불러오지 못했어요.\n" +
      error.message +
      "\n잠시 후 다시 시도해 주세요.";
  }
}

function speakGuide() {
  if (!("speechSynthesis" in window)) {
    document.getElementById("voiceStatus").textContent =
      "이 브라우저에서는 음성 읽기를 지원하지 않아요.";
    return;
  }

  if (!guideText) {
    guideText =
      "출발지와 도착지를 입력하고 경로 검색하기를 눌러 주세요.";
  }

  speechSynthesis.cancel();

  const speech = new SpeechSynthesisUtterance(guideText);
  speech.lang = "ko-KR";
  speech.rate = 0.9;

  speechSynthesis.speak(speech);

  document.getElementById("voiceStatus").textContent =
    "🔊 음성 안내를 재생하고 있어요.";
}

function stopGuide() {
  if ("speechSynthesis" in window) {
    speechSynthesis.cancel();
  }
  document.getElementById("voiceStatus").textContent =
    "음성 안내를 정지했어요.";
}
</script>
</body>
</html>

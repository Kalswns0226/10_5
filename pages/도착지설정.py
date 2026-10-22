import streamlit as st

st.set_page_config(
    page_title="소리길 | 음성 목적지 도우미",
    page_icon="🔔",
    layout="centered",
    initial_sidebar_state="collapsed",
)

APP_HTML = r"""
<div id="sound-road-app">
<style>
#sound-road-app {
  font-family: Arial, "Malgun Gothic", sans-serif;
  color: #102a43;
  max-width: 760px;
  margin: 0 auto;
}
#sound-road-app * { box-sizing: border-box; }
#sound-road-app .hero {
  background: #102a43;
  color: white;
  border-radius: 20px;
  padding: 24px 20px;
  margin-bottom: 18px;
}
#sound-road-app h1 { font-size: 30px; margin: 0 0 8px; }
#sound-road-app h2 { font-size: 22px; margin: 0 0 14px; }
#sound-road-app p { line-height: 1.65; }
#sound-road-app .card {
  border: 2px solid #cbd5e1;
  border-radius: 18px;
  padding: 20px;
  margin: 14px 0;
  background: #fff;
}
#sound-road-app .big {
  display: block;
  width: 100%;
  min-height: 66px;
  border: 0;
  border-radius: 14px;
  padding: 16px;
  margin: 10px 0;
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  color: #102a43;
  background: #e2e8f0;
}
#sound-road-app .primary {
  color: #fff;
  background: #075985;
}
#sound-road-app .danger {
  color: #fff;
  background: #9f1239;
}
#sound-road-app button:focus,
#sound-road-app input:focus {
  outline: 4px solid #f59e0b;
  outline-offset: 3px;
}
#sound-road-app .status {
  background: #f1f5f9;
  border-left: 6px solid #075985;
  border-radius: 8px;
  padding: 14px;
  margin: 12px 0;
  font-size: 17px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
#sound-road-app .metric {
  font-size: 32px;
  font-weight: 800;
  line-height: 1.3;
}
#sound-road-app .muted {
  color: #334155;
  font-size: 14px;
  line-height: 1.65;
}
#sound-road-app input {
  width: 100%;
  min-height: 54px;
  border: 2px solid #64748b;
  border-radius: 10px;
  padding: 12px;
  font-size: 18px;
}
#sound-road-app .result {
  display: block;
  width: 100%;
  text-align: left;
  border: 2px solid #64748b;
  border-radius: 12px;
  background: #fff;
  padding: 14px;
  margin: 8px 0;
  font-size: 17px;
  cursor: pointer;
  color: #102a43;
}
#sound-road-app .small-title {
  font-weight: 800;
  font-size: 18px;
  margin-bottom: 8px;
}
#sound-road-app .notice {
  border: 2px solid #b45309;
  background: #fffbeb;
  padding: 14px;
  border-radius: 12px;
  color: #78350f;
  line-height: 1.6;
}
</style>

<section class="hero" aria-labelledby="app-title">
  <h1 id="app-title">소리길</h1>
  <p>목적지를 말하고, 거리를 확인하고, 도착 알림을 받아요.</p>
  <p>화면 읽기 프로그램과 키보드로도 버튼을 사용할 수 있도록 구성했어요.</p>
</section>

<section class="card" aria-labelledby="destination-heading">
  <h2 id="destination-heading">1. 목적지 설정</h2>
  <button id="voice-btn" class="big primary">
    🎙️ 목적지를 음성으로 말하기
  </button>
  <label for="destination-text" class="small-title">
    음성 인식이 안 되면 목적지를 직접 입력할 수 있어요.
  </label>
  <input id="destination-text" type="text"
         placeholder="예: 천안역, 서울역"
         autocomplete="street-address">
  <button id="search-btn" class="big">입력한 목적지 검색</button>
  <div id="search-status" class="status" role="status" aria-live="polite">
    먼저 목적지를 말하거나 입력해 주세요.
  </div>
  <div id="results" aria-label="목적지 검색 결과"></div>
</section>

<section class="card" aria-labelledby="location-heading">
  <h2 id="location-heading">2. 위치 확인 및 이동 시작</h2>
  <button id="start-btn" class="big primary">
    📍 현재 위치 확인 및 도착 알림 시작
  </button>
  <button id="stop-btn" class="big danger">
    ■ 위치 확인 및 알림 중지
  </button>
  <div id="location-status" class="status" role="status" aria-live="polite">
    시작 버튼을 누르고 브라우저의 위치 권한을 허용해 주세요.
  </div>
</section>

<section class="card" aria-labelledby="distance-heading">
  <h2 id="distance-heading">3. 거리와 도착 상태</h2>
  <div class="muted">선택한 목적지</div>
  <div id="chosen-place" class="metric" style="font-size:24px">
    아직 선택하지 않았어요.
  </div>
  <hr>
  <div class="muted">도보 경로 거리(마지막으로 계산한 값)</div>
  <div id="route-distance" class="metric" aria-live="polite">계산 전</div>
  <p id="route-time">예상 도보 시간: 계산 전</p>
  <div class="muted">현재 위치에서 목적지까지의 직선거리</div>
  <div id="direct-distance" class="metric" style="font-size:24px">측정 전</div>
  <div id="arrival-status" class="status" role="status" aria-live="polite">
    목적지를 선택하고 위치 확인을 시작하면 상태가 표시돼요.
  </div>
</section>

<section class="card">
  <h2>안전 및 개인정보 안내</h2>
  <div class="notice">
    이 서비스는 정밀 내비게이션이 아닙니다. GPS와 지도 정보에는 오차가 있을 수
    있으므로, 음성 안내만 믿고 도로를 건너거나 이동하지 마세요.
    필요하면 보호자 또는 주변 사람의 도움을 요청하세요.
  </div>
  <p class="muted">
    현재 위치와 목적지 검색어는 거리·장소를 조회하기 위해 외부 지도 서비스에
    전달될 수 있습니다. 브라우저의 위치 권한을 허용할지 신중하게 결정하세요.
  </p>
  <p class="muted">
    장소 데이터: OpenStreetMap / Photon · 경로 데이터: OpenStreetMap 기반 FOSSGIS
    경로 서비스
  </p>
</section>
</div>

<script>
(function () {
  const root = document.getElementById("sound-road-app");
  if (!root || root.dataset.initialized === "yes") return;
  root.dataset.initialized = "yes";

  const $ = (id) => document.getElementById(id);
  const voiceBtn = $("voice-btn");
  const searchBtn = $("search-btn");
  const startBtn = $("start-btn");
  const stopBtn = $("stop-btn");
  const destinationInput = $("destination-text");

  let currentPosition = null;
  let destination = null;
  let watchId = null;
  let arrivalAnnounced = false;
  let recognition = null;
  let routeInFlight = false;
  let lastRouteAt = 0;
  let audioContext = null;
  let lastAccuracy = null;

  function setText(id, text) {
    $(id).textContent = text;
  }

  function speak(message) {
    try {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.lang = "ko-KR";
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    } catch (error) {
      console.warn("음성 안내 오류:", error);
    }
  }

  function playAlert() {
    try {
      const AudioContextClass =
        window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) {
        speak("목적지 근처에 도착했습니다. 주변을 확인해 주세요.");
        return;
      }
      audioContext = audioContext || new AudioContextClass();
      if (audioContext.state === "suspended") {
        audioContext.resume();
      }

      const playTone = (when, frequency) => {
        const oscillator = audioContext.createOscillator();
        const gain = audioContext.createGain();
        oscillator.type = "sine";
        oscillator.frequency.value = frequency;
        gain.gain.setValueAtTime(0.001, when);
        gain.gain.exponentialRampToValueAtTime(0.3, when + 0.03);
        gain.gain.exponentialRampToValueAtTime(0.001, when + 0.35);
        oscillator.connect(gain);
        gain.connect(audioContext.destination);
        oscillator.start(when);
        oscillator.stop(when + 0.38);
      };

      const now = audioContext.currentTime;
      playTone(now, 880);
      playTone(now + 0.42, 660);
      playTone(now + 0.84, 880);
      setTimeout(() => {
        speak("목적지 근처에 도착했습니다. 주변을 확인해 주세요.");
      }, 1300);
    } catch (error) {
      console.warn("알림음 재생 오류:", error);
      speak("목적지 근처에 도착했습니다. 주변을 확인해 주세요.");
    }
  }

  function formatDistance(meters) {
    if (!Number.isFinite(meters)) return "계산할 수 없어요.";
    if (meters < 1000) return Math.round(meters) + "미터";
    return (meters / 1000).toFixed(2) + "킬로미터";
  }

  function formatDuration(seconds) {
    if (!Number.isFinite(seconds)) return "계산할 수 없어요.";
    const minutes = Math.max(1, Math.round(seconds / 60));
    if (minutes < 60) return "약 " + minutes + "분";
    const hours = Math.floor(minutes / 60);
    const remainder = minutes % 60;
    return remainder ? "약 " + hours + "시간 " + remainder + "분"
                     : "약 " + hours + "시간";
  }

  function straightDistance(lat1, lon1, lat2, lon2) {
    const toRad = (degrees) => degrees * Math.PI / 180;
    const earthRadius = 6371000;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) ** 2;
    return earthRadius * 2 *
      Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function updateDirectDistance() {
    if (!currentPosition || !destination) return;
    const meters = straightDistance(
      currentPosition.lat, currentPosition.lon,
      destination.lat, destination.lon
    );
    setText("direct-distance", formatDistance(meters));
    return meters;
  }

  async function searchDestination() {
    const query = destinationInput.value.trim();
    if (!query) {
      setText("search-status", "목적지를 먼저 말하거나 입력해 주세요.");
      speak("목적지를 먼저 입력해 주세요.");
      return;
    }

    setText("search-status", "장소를 검색하고 있어요. 잠시 기다려 주세요.");
    $("results").replaceChildren();
    searchBtn.disabled = true;
    voiceBtn.disabled = true;

    try {
      const params = new URLSearchParams({
        q: query + ", 대한민국",
        limit: "5",
        lang: "ko"
      });

      if (currentPosition) {
        params.set("lat", String(currentPosition.lat));
        params.set("lon", String(currentPosition.lon));
      }

      const response = await fetch(
        "https://photon.komoot.io/api/?" + params.toString(),
        { method: "GET" }
      );
      if (!response.ok) {
        throw new Error("장소 검색 서버가 응답하지 않습니다.");
      }

      const data = await response.json();
      const features = Array.isArray(data.features) ? data.features : [];

      if (features.length === 0) {
        setText(
          "search-status",
          "장소를 찾지 못했어요. 동네 이름이나 도로명 주소를 포함해 다시 검색해 주세요."
        );
        speak("장소를 찾지 못했습니다. 조금 더 자세히 말해 주세요.");
        return;
      }

      setText("search-status", "검색 결과가 " + features.length +
        "개 있어요. 원하는 장소를 선택해 주세요.");

      features.forEach((feature) => {
        const coords = feature && feature.geometry &&
          feature.geometry.coordinates;
        if (!coords || coords.length < 2) return;

        const props = feature.properties || {};
        const name = props.name || props.street || "이름 없는 장소";
        const details = [
          props.district, props.city, props.state, props.country
        ].filter(Boolean);
        const label = [name, ...details].join(", ");

        const button = document

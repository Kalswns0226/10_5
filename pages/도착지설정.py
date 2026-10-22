
import streamlit as st

st.set_page_config(
    page_title="소리길 - 음성 도착 알림",
    page_icon="🔔",
    layout="centered",
)

APP_HTML = r'''
<div id="soundroad">
<style>
#soundroad {font-family:Arial,sans-serif;color:#102a43;max-width:700px;margin:auto}
#soundroad * {box-sizing:border-box}
#soundroad .hero {background:#102a43;color:white;padding:22px;border-radius:18px}
#soundroad .card {border:2px solid #cbd5e1;border-radius:16px;padding:18px;margin:14px 0}
#soundroad button {width:100%;min-height:58px;padding:13px;margin:7px 0;border:2px solid #64748b;border-radius:12px;font-size:18px;font-weight:bold;cursor:pointer;background:#f1f5f9;color:#102a43}
#soundroad button:focus,#soundroad input:focus {outline:4px solid #f59e0b}
#soundroad .primary {background:#075985;color:white;border-color:#075985}
#soundroad .stop {background:#9f1239;color:white;border-color:#9f1239}
#soundroad input {width:100%;min-height:54px;font-size:18px;padding:12px;border:2px solid #64748b;border-radius:10px}
#soundroad .status {padding:13px;margin:10px 0;background:#f1f5f9;border-left:5px solid #075985;border-radius:8px;line-height:1.6;overflow-wrap:anywhere}
#soundroad .metric {font-size:27px;font-weight:bold;overflow-wrap:anywhere}
#soundroad .muted {font-size:14px;line-height:1.6;color:#334155}
#soundroad .result {text-align:left;background:white}
</style>

<section class="hero">
<h1>소리길 🔔</h1>
<p>음성으로 목적지를 찾고, 거리를 확인하고, 도착 알림을 받아요.</p>
</section>

<section class="card">
<h2>1. 목적지 입력</h2>
<button id="voice" class="primary">🎙️ 목적지를 음성으로 말하기</button>
<label for="place">음성 인식이 안 되면 직접 입력하세요.</label>
<input id="place" placeholder="예: 천안역">
<button id="search">목적지 검색</button>
<div id="searchStatus" class="status" role="status" aria-live="polite">목적지를 말하거나 입력해 주세요.</div>
<div id="results"></div>
</section>

<section class="card">
<h2>2. 현재 위치 및 도착 알림</h2>
<button id="start" class="primary">📍 위치 확인 및 알림 시작</button>
<button id="stop" class="stop">■ 알림 중지</button>
<div id="locationStatus" class="status" role="status" aria-live="polite">시작 버튼을 눌러 위치 권한을 허용해 주세요.</div>
</section>

<section class="card">
<h2>3. 목적지까지 거리</h2>
<p class="muted">선택한 목적지</p>
<div id="selected" class="metric">선택 전</div>
<hr>
<p class="muted">도보 경로 거리</p>
<div id="routeDistance" class="metric">계산 전</div>
<p id="routeTime">예상 도보 시간: 계산 전</p>
<p class="muted">현재 위치와 목적지의 직선거리</p>
<div id="directDistance" class="metric">측정 전</div>
<div id="arrivalStatus" class="status" role="status" aria-live="polite">목적지를 선택해 주세요.</div>
</section>

<section class="card">
<h2>안전 안내</h2>
<p>GPS와 지도에는 오차가 있을 수 있습니다. 이 앱은 전문 내비게이션이 아니며, 도착 알림만으로 실제 목적지에 도착했다고 확신할 수 없습니다. 주변 교통과 장애물을 반드시 확인하세요.</p>
<p class="muted">장소 검색과 도보 경로 계산을 위해 외부 지도 서비스에 요청을 보냅니다. 인터넷 연결이 필요합니다.</p>
</section>
</div>

<script>
(function () {
  const root = document.getElementById("soundroad");
  if (!root || root.dataset.ready === "1") return;
  root.dataset.ready = "1";

  const el = id => document.getElementById(id);
  let current = null;
  let destination = null;
  let watchId = null;
  let arrived = false;
  let recognition = null;
  let routeBusy = false;
  let lastRouteTime = 0;
  let audio = null;

  function say(message) {
    try {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.lang = "ko-KR";
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn(e);
    }
  }

  function text(id, value) {
    el(id).textContent = value;
  }

  function distanceText(m) {
    if (!Number.isFinite(m)) return "계산할 수 없음";
    return m < 1000 ? Math.round(m) + "m" : (m / 1000).toFixed(2) + "km";
  }

  function durationText(seconds) {
    if (!Number.isFinite(seconds)) return "계산할 수 없음";
    const minutes = Math.max(1, Math.round(seconds / 60));
    if (minutes < 60) return "약 " + minutes + "분";
    const hours = Math.floor(minutes / 60);
    const rest = minutes % 60;
    return "약 " + hours + "시간 " + rest + "분";
  }

  function straightDistance(a, b) {
    const rad = n => n * Math.PI / 180;
    const dLat = rad(b.lat - a.lat);
    const dLon = rad(b.lon - a.lon);
    const h = Math.sin(dLat / 2) ** 2 +
      Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) *
      Math.sin(dLon / 2) ** 2;
    return 6371000 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  }

  function alertArrival() {
    try {
      const AudioClass = window.AudioContext || window.webkitAudioContext;
      if (AudioClass) {
        audio = audio || new AudioClass();
        if (audio.state === "suspended") audio.resume();
        [0, 0.45, 0.9].forEach((offset, index) => {
          const oscillator = audio.createOscillator();
          const gain = audio.createGain();
          const start = audio.currentTime + offset;
          oscillator.frequency.value = index === 1 ? 660 : 880;
          gain.gain.setValueAtTime(0.001, start);
          gain.gain.exponentialRampToValueAtTime(0.25, start + 0.03);
          gain.gain.exponentialRampToValueAtTime(0.001, start + 0.3);
          oscillator.connect(gain);
          gain.connect(audio.destination);
          oscillator.start(start);
          oscillator.stop(start + 0.32);
        });
      }
    } catch (e) {
      console.warn("알림음 오류", e);
    }
    say("목적지 근처에 도착한 것으로 보여요. 주변을 확인해 주세요.");
  }

  async function searchPlace() {
    const query = el("place").value.trim();
    if (!query) {
      text("searchStatus", "목적지를 먼저 입력해 주세요.");
      say("목적지를 먼저 입력해 주세요.");
      return;
    }

    text("searchStatus", "장소를 검색하고 있어요.");
    el("results").replaceChildren();
    el("search").disabled = true;
    el("voice").disabled = true;

    try {
      const params = new URLSearchParams({
        q: query + ", 대한민국",
        limit: "5",
        lang: "ko"
      });
      if (current) {
        params.set("lat", String(current.lat));
        params.set("lon", String(current.lon));
      }

      const response = await fetch(
        "https://photon.komoot.io/api/?" + params.toString()
      );
      if (!response.ok) throw new Error("검색 서버 오류");

      const data = await response.json();
      const features = Array.isArray(data.features) ? data.features : [];

      if (!features.length) {
        text("searchStatus", "장소를 찾지 못했어요. 지역명이나 주소를 더해 다시 검색해 주세요.");
        say("장소를 찾지 못했습니다.");
        return;
      }

      text("searchStatus", "검색 결과를 선택해 주세요.");

      features.forEach(feature => {
        const coords = feature.geometry && feature.geometry.coordinates;
        if (!coords || coords.length < 2) return;

        const p = feature.properties || {};
        const name = p.name || p.street || "이름 없는 장소";
        const label = [name, p.district, p.city, p.state]
          .filter(Boolean).join(", ");

        const button = document.createElement("button");
        button.className = "result";
        button.textContent = label + " - 선택";
        button.addEventListener("click", () => {
          destination = {
            name: name,
            label: label,
            lon: Number(coords[0]),
            lat: Number(coords[1])
          };
          arrived = false;
          text("selected", label);
          text("searchStatus", "목적지를 선택했어요.");
          text("arrivalStatus", "현재 위치 확인을 시작해 주세요.");
          say("목적지를 " + name + "으로 선택했습니다.");
          updateDistance();
          if (current) calculateRoute(true);
        });
        el("results").appendChild(button);
      });
    } catch (e) {
      console.error(e);
      text("searchStatus", "검색에 실패했어요. 인터넷 연결을 확인하고 다시 시도해 주세요.");
      say("장소 검색에 실패했습니다.");
    } finally {
      el("search").disabled = false;
      el("voice").disabled = false;
    }
  }

  function updateDistance() {
    if (!current || !destination) return null;
    const meters = straightDistance(current, destination);
    text("directDistance", distanceText(meters));
    return meters;
  }

  async function calculateRoute(force) {
    if (!current || !destination || routeBusy) return;
    const now = Date.now();
    if (!force && now - lastRouteTime < 60000) return;

    routeBusy = true;
    lastRouteTime = now;
    text("routeDistance", "계산 중");
    text("routeTime", "예상 도보 시간: 계산 중");

    try {
      const coords = current.lon + "," + current.lat + ";" +
        destination.lon + "," + destination.lat;
      const url =
        "https://routing.openstreetmap.de/routed-foot/route/v1/driving/" +
        coords + "?overview=false&steps=false";

      const response = await fetch(url);
      if (!response.ok) throw new Error("경로 서버 오류");

      const data = await response.json();
      if (data.code !== "Ok" || !data.routes || !data.routes.length) {
        throw new Error("경로 없음");
      }

      const route = data.routes[0];
      text("routeDistance", distanceText(route.distance));
      text("routeTime", "예상 도보 시간: " + durationText(route.duration));
      text("arrivalStatus", "경로를 조회했어요. 실제 보행 거리와 시간은 다를 수 있어요.");
    } catch (e) {
      console.warn(e);
      text("routeDistance", "경로 조회 실패");
      text("routeTime", "경로 서비스에 연결할 수 없어요.");
      text("arrivalStatus", "직선거리만 확인할 수 있어요. 잠시 후 다시 시도해 주세요.");
    } finally {
      routeBusy = false;
    }
  }

  function positionSuccess(position) {
    current = {
      lat: position.coords.latitude,
      lon: position.coords.longitude
    };
    const accuracy = position.coords.accuracy;
    text("locationStatus",
      "현재 위치 확인 완료. GPS 오차 범위 약 " +
      Math.round(accuracy) + "m");

    const meters = updateDistance();
    if (destination && meters !== null) {
      if (meters <= 35 && accuracy <= 60 && !arrived) {
        arrived = true;
        text("arrivalStatus", "목적지 근처로 판단했어요. 주변을 확인해 주세요.");
        alertArrival();
      } else if (!arrived) {
        text("arrivalStatus",
          "이동 중이에요. 직선거리 " + distanceText(meters) +
          ". GPS 오차에 따라 달라질 수 있어요.");
      }
      calculateRoute(false);
    }
  }

  function positionError(error) {
    let message = "위치를 확인할 수 없어요. 기기 설정을 확인해 주세요.";
    if (error.code === 1) {
      message = "위치 권한이 거부됐어요. 브라우저에서 위치 권한을 허용해 주세요.";
    } else if (error.code === 2) {
      message = "현재 위치를 사용할 수 없어요. 기기의 위치 설정을 확인해 주세요.";
    } else if (error.code === 3) {
      message = "위치 확인 시간이 초과됐어요. 다시 시작해 주세요.";
    }
    text("locationStatus", message);
    say(message);
  }

  function startTracking() {
    if (!navigator.geolocation) {
      text("locationStatus", "이 브라우저는 위치 확인을 지원하지 않아요.");
      say("위치 확인을 지원하지 않는 브라우저입니다.");
      return;
    }

    try {
      const AudioClass = window.AudioContext || window.webkitAudioContext;
      if (AudioClass) {
        audio = audio || new AudioClass();
        if (audio.state === "suspended") audio.resume();
      }
    } catch (e) {
      console.warn(e);
    }

    if (watchId !== null) navigator.geolocation.clearWatch(watchId);

    text("locationStatus", "위치를 확인하고 있어요.");
    say("위치 확인을 시작합니다.");

    watchId = navigator.geolocation.watchPosition(
      positionSuccess,
      positionError,
      { enableHighAccuracy: true, maximumAge: 3000, timeout: 20000 }
    );
    if (destination) calculateRoute(true);
  }

  function stopTracking() {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
    text("locationStatus", "위치 확인을 중지했어요.");
    text("arrivalStatus", "알림이 중지됐어요.");
    say("위치 확인을 중지했습니다.");
  }

  el("voice").addEventListener("click", () => {
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Speech) {
      text("searchStatus", "음성 인식을 지원하지 않는 브라우저예요. 아래 칸에 직접 입력해 주세요.");
      say("음성 인식을 지원하지 않습니다. 직접 입력해 주세요.");
      return;
    }

    try {
      if (recognition) {
        try { recognition.abort(); } catch (e) {}
      }
      recognition = new Speech();
      recognition.lang = "ko-KR";
      recognition.continuous = false;
      recognition.interimResults = false;
      el("voice").disabled = true;
      text("searchStatus", "목적지를 듣고 있어요. 장소 이름을 말해 주세요.");

      recognition.onresult = event => {
        const phrase = event.results[0][0].transcript.trim();
        el("place").value = phrase;
        text("searchStatus", "인식한 목적지: " + phrase);
        searchPlace();
      };
      recognition.onerror = event => {
        let message = "음성 인식에 실패했어요. 다시 시도해 주세요.";
        if (event.error === "not-allowed") {
          message = "마이크 권한을 허용해 주세요.";
        } else if (event.error === "no-speech") {
          message = "음성이 들리지 않았어요. 다시 말해 주세요.";
        }
        text("searchStatus", message);
        say(message);
      };
      recognition.onend = () => {
        el("voice").disabled = false;
      };
      recognition.start();
    } catch (e) {
      console.error(e);
      el("voice").disabled = false;
      text("searchStatus", "음성 인식을 시작하지 못했어요. 직접 입력해 주세요.");
    }
  });

  el("search").addEventListener("click", searchPlace);
  el("place").addEventListener("keydown", event => {
    if (event.key === "Enter") searchPlace();
  });
  el("start").addEventListener("click", startTracking);
  el("stop").addEventListener("click", stopTracking);

  window.addEventListener("beforeunload", () => {
    if (watchId !== null) navigator.geolocation.clearWatch(watchId);
  });
})();
</script>
'''

st.html(APP_HTML, unsafe_allow_javascript=True)

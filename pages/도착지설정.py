
import json
import math
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(
    page_title="안심도착",
    page_icon="🧭",
    layout="centered",
)

st.markdown("""
<style>
html, body, [class*="css"] { font-size: 20px !important; }
.stApp { background: #f7f9fc; }
.stButton button {
    min-height: 3.5rem;
    font-size: 1.2rem !important;
    font-weight: bold;
    border-radius: 12px;
}
input { font-size: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("안심도착")
st.header("음성으로 목적지 설정하기")

st.info(
    "이 앱은 도착 알림 보조 도구입니다. "
    "실제 보행 경로 안내나 장애물 감지는 제공하지 않습니다."
)


def distance_m(lat1, lon1, lat2, lon2):
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )
    return 2 * r * math.atan2(
        math.sqrt(a), math.sqrt(1 - a)
    )


if "destination_name" not in st.session_state:
    st.session_state.destination_name = ""

if "destination_coords" not in st.session_state:
    st.session_state.destination_coords = None

if "confirmed" not in st.session_state:
    st.session_state.confirmed = False

if "current_location" not in st.session_state:
    st.session_state.current_location = None

if "arrived" not in st.session_state:
    st.session_state.arrived = False


# 브라우저 음성 인식
st.write(
    "목적지 말하기 버튼을 누른 뒤 "
    "가고 싶은 장소를 말해 주세요. "
    "예: 서울역, 시청역, 학교 정문."
)

components.html("""
<div style="font-family:sans-serif">
  <button id="help" style="width:100%;padding:18px;font-size:22px">
    안내 음성 듣기
  </button>
  <br><br>
  <button id="speak" style="width:100%;padding:22px;
    font-size:24px;font-weight:bold;background:#174ea6;color:white">
    목적지 말하기
  </button>
  <p id="status" aria-live="polite" style="font-size:20px">
    버튼을 눌러 음성 입력을 시작하세요.
  </p>
  <script>
    function say(text) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "ko-KR";
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    }

    document.getElementById("help").onclick = () => {
      say("목적지 말하기 버튼을 누르고 가고 싶은 장소의 이름을 말해 주세요.");
    };

    document.getElementById("speak").onclick = () => {
      const SR = window.SpeechRecognition ||
                 window.webkitSpeechRecognition;

      if (!SR) {
        document.getElementById("status").textContent =
          "음성 인식을 지원하지 않습니다. 아래 입력 칸을 사용하세요.";
        say("음성 인식을 지원하지 않습니다. 아래 입력 칸을 사용하세요.");
        return;
      }

      const rec = new SR();
      rec.lang = "ko-KR";
      rec.interimResults = false;
      rec.maxAlternatives = 1;

      document.getElementById("status").textContent =
        "듣고 있습니다. 목적지를 말해 주세요.";
      say("목적지를 말해 주세요.");

      rec.onresult = (event) => {
        const result = event.results[0][0].transcript.trim();
        document.getElementById("status").textContent =
          "인식한 내용: " + result;

        const url = new URL(window.parent.location.href);
        url.searchParams.set("voice_destination", result);
        window.parent.location.href = url.toString();
      };

      rec.onerror = (event) => {
        let msg = "음성을 인식하지 못했습니다. 다시 시도해 주세요.";
        if (event.error === "not-allowed") {
          msg = "마이크 권한을 허용해 주세요.";
        }
        document.getElementById("status").textContent = msg;
        say(msg);
      };

      rec.start();
    };
  </script>
</div>
""", height=220)


# 음성 인식 결과 받기
try:
    voice_text = st.query_params.get("voice_destination", "")
except Exception:
    voice_text = ""

if voice_text:
    st.session_state.destination_name = voice_text.strip()
    st.session_state.confirmed = False
    st.session_state.destination_coords = None
    st.session_state.arrived = False

    try:
        del st.query_params["voice_destination"]
    except Exception:
        pass


st.subheader("목적지 확인")

typed_name = st.text_input(
    "목적지 이름",
    value=st.session_state.destination_name,
    placeholder="예: 서울역",
)

if typed_name != st.session_state.destination_name:
    st.session_state.destination_name = typed_name.strip()
    st.session_state.confirmed = False
    st.session_state.destination_coords = None

if st.button("목적지 이름 읽기", use_container_width=True):
    if st.session_state.destination_name.strip():
        name_json = json.dumps(
            st.session_state.destination_name,
            ensure_ascii=False,
        )
        components.html(f"""
        <script>
        const u = new SpeechSynthesisUtterance(
            {name_json} + " 입니다. 맞는 목적지인지 확인해 주세요."
        );
        u.lang = "ko-KR";
        speechSynthesis.cancel();
        speechSynthesis.speak(u);
        </script>
        """, height=10)
    else:
        st.warning("먼저 목적지를 말하거나 입력해 주세요.")


if st.button("이 목적지로 설정", type="primary",
             use_container_width=True):
    name = st.session_state.destination_name.strip()

    if not name:
        st.warning("목적지를 먼저 입력해 주세요.")
    else:
        with st.spinner("목적지를 검색하고 있어요."):
            try:
                response = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": name + ", South Korea",
                        "format": "jsonv2",
                        "limit": 1,
                    },
                    headers={
                        "User-Agent": "AnsimDochagAccessibilityApp/1.0"
                    },
                    timeout=15,
                )
                response.raise_for_status()
                results = response.json()

                if results:
                    result = results[0]
                    st.session_state.destination_coords = {
                        "lat": float(result["lat"]),
                        "lon": float(result["lon"]),
                        "address": result.get("display_name", ""),
                    }
                    st.session_state.confirmed = True
                    st.session_state.arrived = False
                    st.success("목적지를 찾았어요.")
                    st.write("검색 결과:", result.get("display_name", name))
                else:
                    st.session_state.confirmed = False
                    st.error(
                        "장소를 찾지 못했어요. "
                        "동네 이름을 포함해 다시 말해 주세요."
                    )

            except requests.RequestException:
                st.session_state.confirmed = False
                st.error(
                    "장소 검색에 실패했어요. "
                    "인터넷 연결을 확인한 뒤 다시 시도해 주세요."
                )


# 현재 위치 확인
st.header("현재 위치 확인")

if st.button("현재 위치 확인 또는 새로고침",
             type="primary", use_container_width=True):
    st.session_state.request_location = True

if st.session_state.get("request_location", False):
    location = streamlit_geolocation()

    if (
        location
        and location.get("latitude") is not None
        and location.get("longitude") is not None
    ):
        st.session_state.current_location = {
            "lat": float(location["latitude"]),
            "lon": float(location["longitude"]),
        }
        st.session_state.request_location = False
        st.rerun()
    else:
        st.info(
            "브라우저의 위치 권한을 허용해 주세요. "
            "위치를 받지 못하면 다시 버튼을 눌러 주세요."
        )


# 거리와 도착 알림
st.header("도착 알림")

radius = st.select_slider(
    "도착으로 판단할 거리",
    options=[20, 30, 50, 75, 100, 150, 200],
    value=50,
    format_func=lambda x: f"{x}미터",
)

if (
    st.session_state.confirmed
    and st.session_state.destination_coords
    and st.session_state.current_location
):
    d = st.session_state.destination_coords
    p = st.session_state.current_location

    distance = distance_m(
        p["lat"], p["lon"], d["lat"], d["lon"]
    )

    st.metric("목적지까지 직선거리", f"{distance:.0f}m")

    if distance <= radius:
        st.success("도착 반경 안에 들어왔어요!")

        if not st.session_state.arrived:
            st.session_state.arrived = True

            name_json = json.dumps(
                st.session_state.destination_name,
                ensure_ascii=False,
            )

            components.html(f"""
            <button id="repeat" style="padding:16px;font-size:22px">
              도착 알림 다시 듣기
            </button>
            <p aria-live="polite" id="alertStatus"></p>
            <script>
              function notify() {{
                try {{
                  if (navigator.vibrate) {{
                    navigator.vibrate([300,150,300,150,600]);
                  }}
                }} catch(e) {{}}

                try {{
                  const u = new SpeechSynthesisUtterance(
                    {name_json} +
                    " 근처에 도착한 것으로 보여요. 주변을 확인해 주세요."
                  );
                  u.lang = "ko-KR";
                  speechSynthesis.cancel();
                  speechSynthesis.speak(u);
                }} catch(e) {{}}

                try {{
                  const AC = window.AudioContext ||
                             window.webkitAudioContext;
                  if (AC) {{
                    const ctx = new AC();
                    [880,660,880].forEach((freq,i) => {{
                      const osc = ctx.createOscillator();
                      const gain = ctx.createGain();
                      osc.frequency.value = freq;
                      gain.gain.value = 0.12;
                      osc.connect(gain);
                      gain.connect(ctx.destination);
                      osc.start(ctx.currentTime + i * 0.3);
                      osc.stop(ctx.currentTime + i * 0.3 + 0.18);
                    }});
                  }}
                }} catch(e) {{}}

                document.getElementById("alertStatus").textContent =
                  "도착 알림을 실행했어요.";
              }}

              document.getElementById("repeat").onclick = notify;
              notify();
            </script>
            """, height=130)

    else:
        st.info(
            f"아직 도착 반경 밖이에요. "
            f"약 {max(0, distance - radius):.0f}m 더 가까워지면 "
            "알림 조건에 들어옵니다."
        )

    st.caption(
        "현재 위치는 마지막으로 확인한 위치입니다. "
        "이동 중에는 위치 새로고침 버튼을 눌러 주세요."
    )

elif st.session_state.confirmed:
    st.info("현재 위치를 확인하면 거리를 계산할 수 있어요.")

st.divider()
st.caption(
    "GPS 오차가 있을 수 있으며, 진동과 음성 기능은 "
    "기기와 브라우저에 따라 다르게 작동할 수 있습니다. "
    "이 앱은 자동 백그라운드 추적이나 실제 길 안내를 제공하지 않습니다."
)

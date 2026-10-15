import streamlit as st
st. title(' 나는 짱이다')
st.write('바이브코딩 재밌다!!') 

<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>소리로 안내하는 길잡이</title>
  <style>
    body {
      text-align: center;
      font-family: sans-serif;
      background: #eaf5ff;
      padding: 30px;
    }
    h1 { color: #2865a8; }
    button, input {
      padding: 12px;
      margin: 8px;
      font-size: 17px;
      border-radius: 10px;
    }
    button {
      background: #4285e8;
      color: white;
      border: none;
    }
  </style>
</head>
<body>
  <h1>🔊 소리로 안내하는 길잡이</h1>
  <p>목적지를 입력하면 음성으로 안내해요!</p>

  <input id="place" placeholder="목적지를 입력하세요">
  <button onclick="guide()">길 안내</button>

  <h3>⚠️ 안전 안내</h3>
  <button onclick="speak('앞에 횡단보도가 있습니다. 조심하세요.')">
    횡단보도 안내
  </button>
  <button onclick="speak('앞에 계단이 있습니다. 조심하세요.')">
    계단 안내
  </button>

  <script>
    function speak(message) {
      const voice = new SpeechSynthesisUtterance(message);
      voice.lang = "ko-KR";
      speechSynthesis.speak(voice);
    }

    function guide() {
      const place = document.getElementById("place").value;
      if (place.trim() === "") {
        speak("목적지를 입력해 주세요.");
      } else {
        speak(place + "까지 안전하게 이동하세요. 주변을 조심하세요.");
      }
    }
  </script>
</body>
</html>

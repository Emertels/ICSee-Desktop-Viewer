"""
Internationalization (i18n) Module — 10 Languages Edition
==========================================================
Full multilingual support for the ICSee Desktop Viewer.
Supported Languages:
  1. pt  — Português (Brasil)
  2. en  — English
  3. es  — Español
  4. fr  — Français
  5. de  — Deutsch
  6. it  — Italiano
  7. ja  — 日本語 (Japanese)
  8. zh  — 简体中文 (Simplified Chinese)
  9. ru  — Русский (Russian)
 10. ko  — 한국어 (Korean)

Author: Emerson Teles (@Emertels)
License: MIT
"""

from __future__ import annotations
from typing import Callable, List, Tuple

_current_lang = "pt"
_listeners: List[Callable[[], None]] = []

LANGUAGES: List[Tuple[str, str]] = [
    ("pt", "🇧🇷 Português"),
    ("en", "🇺🇸 English"),
    ("es", "🇪🇸 Español"),
    ("fr", "🇫🇷 Français"),
    ("de", "🇩🇪 Deutsch"),
    ("it", "🇮🇹 Italiano"),
    ("ja", "🇯🇵 日本語"),
    ("zh", "🇨🇳 简体中文"),
    ("ru", "🇷🇺 Русский"),
    ("ko", "🇰🇷 한국어"),
]

STRINGS: dict[str, dict[str, str]] = {
    # App Title & Headers
    "app_title": {
        "pt": "ICSee Desktop Viewer v1.0.0",
        "en": "ICSee Desktop Viewer v1.0.0",
        "es": "ICSee Desktop Viewer v1.0.0",
        "fr": "ICSee Desktop Viewer v1.0.0",
        "de": "ICSee Desktop Viewer v1.0.0",
        "it": "ICSee Desktop Viewer v1.0.0",
        "ja": "ICSee デスクトップビューアー v1.0.0",
        "zh": "ICSee 桌面监控器 v1.0.0",
        "ru": "ICSee Desktop Viewer v1.0.0",
        "ko": "ICSee 데스크톱 뷰어 v1.0.0",
    },
    
    # Top Bar Buttons
    "btn_photo": {
        "pt": "📸 Foto",
        "en": "📸 Photo",
        "es": "📸 Foto",
        "fr": "📸 Photo",
        "de": "📸 Foto",
        "it": "📸 Foto",
        "ja": "📸 写真",
        "zh": "📸 截图",
        "ru": "📸 Фото",
        "ko": "📸 사진",
    },
    "tip_photo": {
        "pt": "Captura instantânea (salva em Imagens)",
        "en": "Instant snapshot (saved to Pictures)",
        "es": "Captura instantánea (guardada en Imágenes)",
        "fr": "Capture instantanée (enregistrée dans Images)",
        "de": "Sofortiges Bildschirmfoto (in Bilder gespeichert)",
        "it": "Istantanea rapida (salvata in Immagini)",
        "ja": "即時スナップショット（ピクチャに保存）",
        "zh": "快速截图（保存至图片文件夹）",
        "ru": "Быстрый снимок (сохраняется в Изображения)",
        "ko": "즉시 스냅샷(사진 폴더에 저장)",
    },
    "btn_sd": {
        "pt": "⚡ SD",
        "en": "⚡ SD",
        "es": "⚡ SD",
        "fr": "⚡ SD",
        "de": "⚡ SD",
        "it": "⚡ SD",
        "ja": "⚡ SD",
        "zh": "⚡ 标清",
        "ru": "⚡ SD",
        "ko": "⚡ SD",
    },
    "tip_sd": {
        "pt": "SD Fluido: Resolução 640x720 (~15 FPS). Baixo uso de rede.",
        "en": "Fluid SD: 640x720 resolution (~15 FPS). Low network usage.",
        "es": "SD Fluido: Resolución 640x720 (~15 FPS). Bajo uso de red.",
        "fr": "SD Fluide : Résolution 640x720 (~15 FPS). Faible bande passante.",
        "de": "Flüssiges SD: 640x720 Auflösung (~15 FPS). Geringe Netzwerkauslastung.",
        "it": "SD Fluido: Risoluzione 640x720 (~15 FPS). Basso utilizzo di rete.",
        "ja": "スムーズSD：解像度 640x720 (~15 FPS)。低帯域幅。",
        "zh": "流畅标清：分辨率 640x720 (~15 FPS)，超低网络占用。",
        "ru": "SD поток: 640x720 (~15 кадров/с). Низкая нагрузка на сеть.",
        "ko": "원활한 SD: 해상도 640x720 (~15 FPS). 낮은 네트워크 사용량.",
    },
    "btn_hd": {
        "pt": "🌟 HD",
        "en": "🌟 HD",
        "es": "🌟 HD",
        "fr": "🌟 HD",
        "de": "🌟 HD",
        "it": "🌟 HD",
        "ja": "🌟 HD",
        "zh": "🌟 高清",
        "ru": "🌟 HD",
        "ko": "🌟 HD",
    },
    "tip_hd": {
        "pt": "HD Ultra: Resolução 2304x2592 (8MP Ultra). Máxima nitidez.",
        "en": "Ultra HD: 2304x2592 resolution (8MP Ultra). Maximum clarity.",
        "es": "HD Ultra: Resolución 2304x2592 (8MP Ultra). Máxima nitidez.",
        "fr": "Ultra HD : Résolution 2304x2592 (8MP Ultra). Netteté maximale.",
        "de": "Ultra HD: 2304x2592 Auflösung (8MP Ultra). Maximale Schärfe.",
        "it": "HD Ultra: Risoluzione 2304x2592 (8MP Ultra). Massima nitidezza.",
        "ja": "ウルトラHD：解像度 2304x2592 (8MP Ultra)。最高画質。",
        "zh": "超清高清：分辨率 2304x2592 (800万像素)，极高清晰度。",
        "ru": "Ultra HD: 2304x2592 (8МП). Максимальная четкость.",
        "ko": "울트라 HD: 해상도 2304x2592 (8MP). 최고 선명도.",
    },
    "btn_normal": {
        "pt": "⯀ Normal",
        "en": "⯀ Normal",
        "es": "⯀ Normal",
        "fr": "⯀ Normal",
        "de": "⯀ Normal",
        "it": "⯀ Normale",
        "ja": "⯀ 標準",
        "zh": "⯀ 默认",
        "ru": "⯀ Обычный",
        "ko": "⯀ 기본",
    },
    "tip_normal": {
        "pt": "Visão Vertical: Exibe as duas lentes sobrepostas verticalmente",
        "en": "Vertical View: Displays both lenses stacked vertically",
        "es": "Vista Vertical: Muestra ambas lentes superpuestas verticalmente",
        "fr": "Vue Verticale : Affiche les deux objectifs superposés",
        "de": "Vertikale Ansicht: Beide Objektive übereinander anzeigen",
        "it": "Vista Verticale: Mostra entrambi gli obiettivi impilati",
        "ja": "垂直ビュー：両方のレンズを上下に重ねて表示",
        "zh": "垂直布局：上下并排显示双镜头",
        "ru": "Вертикальный вид: Двойной объектив друг над другом",
        "ko": "세로 보기: 두 렌즈를 상하로 나란히 표시",
    },
    "btn_side": {
        "pt": "⚏ Lado a Lado",
        "en": "⚏ Side-by-Side",
        "es": "⚏ Lado a Lado",
        "fr": "⚏ Côte à côte",
        "de": "⚏ Nebeneinander",
        "it": "⚏ Affiancato",
        "ja": "⚏ 並列表示",
        "zh": "⚏ 左右并排",
        "ru": "⚏ Рядом",
        "ko": "⚏ 나란히 보기",
    },
    "tip_side": {
        "pt": "Lado a Lado: Exibe ambas as lentes horizontalmente",
        "en": "Side-by-Side: Displays both lenses side by side horizontally",
        "es": "Lado a Lado: Muestra ambas lentes horizontalmente",
        "fr": "Côte à côte : Affiche les deux objectifs horizontalement",
        "de": "Nebeneinander: Zeigt beide Objektive nebeneinander",
        "it": "Affiancato: Mostra entrambi gli obiettivi orizzontalmente",
        "ja": "並列表示：両方のレンズを水平に並べて表示",
        "zh": "左右并排：横向显示双镜头全景",
        "ru": "Рядом: Горизонтальное отображение двух камер",
        "ko": "나란히 보기: 양쪽 렌즈를 가로로 배치",
    },
    "btn_pin": {
        "pt": "📌 Fixar",
        "en": "📌 Pin",
        "es": "📌 Fijar",
        "fr": "📌 Épingler",
        "de": "📌 Anheften",
        "it": "📌 Fissa",
        "ja": "📌 最前面",
        "zh": "📌 置顶",
        "ru": "📌 Закрепить",
        "ko": "📌 고정",
    },
    "tip_pin": {
        "pt": "Manter a janela sempre visível sobre outros programas",
        "en": "Keep window always on top of other applications",
        "es": "Mantener la ventana siempre sobre otros programas",
        "fr": "Garder la fenêtre toujours au premier plan",
        "de": "Fenster immer im Vordergrund halten",
        "it": "Mantieni la finestra sempre in primo piano",
        "ja": "ウィンドウを常に最前面に維持",
        "zh": "始终保持窗口置顶在最前",
        "ru": "Поверх всех окон",
        "ko": "항상 다른 창 위에 유지",
    },
    "btn_tips": {
        "pt": "🎮 Dicas",
        "en": "🎮 Tips",
        "es": "🎮 Atajos",
        "fr": "🎮 Astuces",
        "de": "🎮 Tipps",
        "it": "🎮 Suggerimenti",
        "ja": "🎮 ヒント",
        "zh": "🎮 帮助",
        "ru": "🎮 Советы",
        "ko": "🎮 단축키",
    },
    "tip_tips": {
        "pt": "Exibir guia de atalhos e controles de videogame",
        "en": "Show shortcuts guide and gamepad controls",
        "es": "Mostrar guía de atajos y controles de gamepad",
        "fr": "Afficher le guide des raccourcis et manette",
        "de": "Tastenkombinationen und Gamepad-Steuerung anzeigen",
        "it": "Mostra guida scorciatoie e comandi gamepad",
        "ja": "ショートカットとコントローラー操作ガイドを表示",
        "zh": "显示快捷键及手柄控制说明",
        "ru": "Показать горячие клавиши и управление геймпадом",
        "ko": "단축키 및 게임패드 컨트롤 안내 표시",
    },
    "btn_discover": {
        "pt": "🔍 Buscar",
        "en": "🔍 Scan",
        "es": "🔍 Buscar",
        "fr": "🔍 Scanner",
        "de": "🔍 Suchen",
        "it": "🔍 Cerca",
        "ja": "🔍 検索",
        "zh": "🔍 扫描",
        "ru": "🔍 Поиск",
        "ko": "🔍 검색",
    },
    "tip_discover": {
        "pt": "Escanear a rede local em busca de câmeras ONVIF/ICSee",
        "en": "Scan local network for ONVIF/ICSee cameras",
        "es": "Escanear la red local en busca de cámaras ONVIF/ICSee",
        "fr": "Scanner le réseau local pour caméras ONVIF/ICSee",
        "de": "Lokales Netzwerk nach ONVIF/ICSee-Kameras durchsuchen",
        "it": "Scansiona la rete locale per telecamere ONVIF/ICSee",
        "ja": "ローカルネットワーク内のONVIF/ICSeeカメラを検索",
        "zh": "扫描局域网中的ONVIF/ICSee摄像头",
        "ru": "Сканировать локальную сеть на наличие камер ONVIF/ICSee",
        "ko": "로컬 네트워크에서 ONVIF/ICSee 카메라 검색",
    },

    # Audio Intercom
    "btn_listen": {
        "pt": "🔊 Ouvir Áudio",
        "en": "🔊 Listen Audio",
        "es": "🔊 Escuchar Audio",
        "fr": "🔊 Écouter l'audio",
        "de": "🔊 Audio anhören",
        "it": "🔊 Ascolta Audio",
        "ja": "🔊 音声を聞く",
        "zh": "🔊 监听声音",
        "ru": "🔊 Прослушать звук",
        "ko": "🔊 오디오 듣기",
    },
    "btn_listening": {
        "pt": "🔊 Ouvindo Áudio",
        "en": "🔊 Listening Audio",
        "es": "🔊 Escuchando Audio",
        "fr": "🔊 Écoute en cours",
        "de": "🔊 Audio wird wiedergegeben",
        "it": "🔊 Ascolto in corso",
        "ja": "🔊 音声再生中",
        "zh": "🔊 正在监听",
        "ru": "🔊 Звук воспроизводится",
        "ko": "🔊 오디오 재생 중",
    },
    "btn_talk": {
        "pt": "🎙️ Falar na Câmera",
        "en": "🎙️ Talk to Camera",
        "es": "🎙️ Hablar a la Cámara",
        "fr": "🎙️ Parler à la caméra",
        "de": "🎙️ Zur Kamera sprechen",
        "it": "🎙️ Parla alla Fotocamera",
        "ja": "🎙️ カメラに話す",
        "zh": "🎙️ 对讲喊话",
        "ru": "🎙️ Говорить в камеру",
        "ko": "🎙️ 카메라로 말하기",
    },
    "btn_talking": {
        "pt": "🔴 Falando na Câmera...",
        "en": "🔴 Talking to Camera...",
        "es": "🔴 Hablando a la Cámara...",
        "fr": "🔴 En train de parler...",
        "de": "🔴 Sprechen aktiv...",
        "it": "🔴 Parlando alla Fotocamera...",
        "ja": "🔴 通話中...",
        "zh": "🔴 正在喊话对讲...",
        "ru": "🔴 Передача голоса...",
        "ko": "🔴 대화 중...",
    },
    "tip_talk": {
        "pt": "Clique para falar continuamente no alto-falante da câmera. Clique novamente para desligar.",
        "en": "Click to speak continuously through the camera speaker. Click again to stop.",
        "es": "Haga clic para hablar de forma continua por el altavoz de la cámara. Haga clic de nuevo para detener.",
        "fr": "Cliquez pour parler en continu via le haut-parleur. Cliquez à nouveau pour arrêter.",
        "de": "Klicken, um kontinuierlich durch den Kameralautsprecher zu sprechen. Erneut klicken zum Beenden.",
        "it": "Fai clic per parlare continuamente dall'altoparlante della telecamera. Fai clic di nuovo per interrompere.",
        "ja": "クリックでカメラのスピーカーから連続通話を開始。もう一度クリックで停止します。",
        "zh": "点击开启持续语音喊话，再次点击关闭喊话。",
        "ru": "Нажмите для голосовой передачи в динамик камеры. Нажмите снова для остановки.",
        "ko": "카메라 스피커로 음성을 전달하려면 클릭하세요. 멈추려면 다시 클릭하세요.",
    },

    # PTZ & Hardware Controls
    "ptz_title": {
        "pt": "🕹️ Controle PTZ",
        "en": "🕹️ PTZ Control",
        "es": "🕹️ Control PTZ",
        "fr": "🕹️ Contrôle PTZ",
        "de": "🕹️ PTZ-Steuerung",
        "it": "🕹️ Controllo PTZ",
        "ja": "🕹️ PTZ制御",
        "zh": "🕹️ 云台控制",
        "ru": "🕹️ Управление PTZ",
        "ko": "🕹️ PTZ 제어",
    },
    "btn_turn_left": {
        "pt": "↶ Esquerda",
        "en": "↶ Left",
        "es": "↶ Izquierda",
        "fr": "↶ Gauche",
        "de": "↶ Links",
        "it": "↶ Sinistra",
        "ja": "↶ 左旋回",
        "zh": "↶ 向左转",
        "ru": "↶ Влево",
        "ko": "↶ 왼쪽",
    },
    "btn_turn_right": {
        "pt": "Direita ↷",
        "en": "Right ↷",
        "es": "Derecha ↷",
        "fr": "Droite ↷",
        "de": "Rechts ↷",
        "it": "Destra ↷",
        "ja": "右旋回 ↷",
        "zh": "向右转 ↷",
        "ru": "Вправо ↷",
        "ko": "오른쪽 ↷",
    },
    "btn_tracking": {
        "pt": "🤖 Rastreamento Humano",
        "en": "🤖 Human Tracking",
        "es": "🤖 Rastreo Humano",
        "fr": "🤖 Suivi Humain",
        "de": "🤖 Personenverfolgung",
        "it": "🤖 Tracciamento Umano",
        "ja": "🤖 人物自動追尾",
        "zh": "🤖 人形追踪",
        "ru": "🤖 Слежение за людьми",
        "ko": "🤖 인간 추적",
    },
    "btn_night_mode": {
        "pt": "🌙 Modo Noturno",
        "en": "🌙 Night Mode",
        "es": "🌙 Modo Nocturno",
        "fr": "🌙 Mode Nuit",
        "de": "🌙 Nachtmodus",
        "it": "🌙 Modalità Notte",
        "ja": "🌙 夜間モード",
        "zh": "🌙 夜视模式",
        "ru": "🌙 Ночной режим",
        "ko": "🌙 야간 모드",
    },
    "btn_light_mode": {
        "pt": "💡 Modo Iluminado",
        "en": "💡 Floodlight Mode",
        "es": "💡 Modo Iluminado",
        "fr": "💡 Mode Éclairé",
        "de": "💡 Flutlicht-Modus",
        "it": "💡 Modalità Luce",
        "ja": "💡 照明モード",
        "zh": "💡 补光全彩",
        "ru": "💡 Режим прожектора",
        "ko": "💡 조명 모드",
    },
    "btn_reboot": {
        "pt": "🔄 Reiniciar Câmera",
        "en": "🔄 Reboot Camera",
        "es": "🔄 Reiniciar Cámara",
        "fr": "🔄 Redémarrer la caméra",
        "de": "🔄 Kamera neustarten",
        "it": "🔄 Riavvia Telecamera",
        "ja": "🔄 カメラ再起動",
        "zh": "🔄 重启摄像头",
        "ru": "🔄 Перезагрузить камеру",
        "ko": "🔄 카메라 재부팅",
    },

    # Video Recording
    "rec_title": {
        "pt": "🎥 Gravação de Vídeo (MP4)",
        "en": "🎥 Video Recording (MP4)",
        "es": "🎥 Grabación de Video (MP4)",
        "fr": "🎥 Enregistrement Vidéo (MP4)",
        "de": "🎥 Videoaufnahme (MP4)",
        "it": "🎥 Registrazione Video (MP4)",
        "ja": "🎥 動画録画 (MP4)",
        "zh": "🎥 录像保存 (MP4)",
        "ru": "🎥 Запись видео (MP4)",
        "ko": "🎥 비디오 녹화 (MP4)",
    },
    "btn_start_rec": {
        "pt": "🔴 Iniciar Gravação",
        "en": "🔴 Start Recording",
        "es": "🔴 Iniciar Grabación",
        "fr": "🔴 Démarrer l'enregistrement",
        "de": "🔴 Aufnahme starten",
        "it": "🔴 Avvia Registrazione",
        "ja": "🔴 録画開始",
        "zh": "🔴 开始录像",
        "ru": "🔴 Начать запись",
        "ko": "🔴 녹화 시작",
    },
    "btn_stop_rec": {
        "pt": "⏹️ Interromper Gravação",
        "en": "⏹️ Stop Recording",
        "es": "⏹️ Detener Grabación",
        "fr": "⏹️ Arrêter l'enregistrement",
        "de": "⏹️ Aufnahme stoppen",
        "it": "⏹️ Interrompi Registrazione",
        "ja": "⏹️ 録画停止",
        "zh": "⏹️ 停止录像",
        "ru": "⏹️ Остановить запись",
        "ko": "⏹️ 녹화 중지",
    },
    "chk_shutdown": {
        "pt": "Desligar o PC ao finalizar",
        "en": "Shut down PC when finished",
        "es": "Apagar el PC al finalizar",
        "fr": "Éteindre le PC à la fin",
        "de": "PC nach Abschluss herunterfahren",
        "it": "Spegni il PC al termine",
        "ja": "録画終了後にPCをシャットダウン",
        "zh": "录制完成后自动关机",
        "ru": "Выключить ПК после завершения",
        "ko": "완료 후 PC 종료",
    },
    "rec_duration_label": {
        "pt": "Duração da gravação:",
        "en": "Recording duration:",
        "es": "Duración de grabación:",
        "fr": "Durée d'enregistrement :",
        "de": "Aufnahmedauer:",
        "it": "Durata registrazione:",
        "ja": "録画時間：",
        "zh": "录像时长：",
        "ru": "Длительность записи:",
        "ko": "녹화 시간:",
    },
    "duration_unlimited": {
        "pt": "Ininterrupto (Sem limite)",
        "en": "Continuous (No limit)",
        "es": "Ininterrumpido (Sin límite)",
        "fr": "Continu (Sans limite)",
        "de": "Endlos (Kein Limit)",
        "it": "Continuo (Senza limiti)",
        "ja": "無制限（手動停止）",
        "zh": "不限时长（持续录制）",
        "ru": "Непрерывно (Без ограничений)",
        "ko": "제한 없음 (연속 녹화)",
    },

    # Settings Panel
    "sett_conn": {
        "pt": "🌐 Conexão:",
        "en": "🌐 Connection:",
        "es": "🌐 Conexión:",
        "fr": "🌐 Connexion :",
        "de": "🌐 Verbindung:",
        "it": "🌐 Connessione:",
        "ja": "🌐 接続設定：",
        "zh": "🌐 连接设置：",
        "ru": "🌐 Подключение:",
        "ko": "🌐 연결 설정:",
    },
    "lbl_ip": {
        "pt": "IP:",
        "en": "IP:",
        "es": "IP:",
        "fr": "IP :",
        "de": "IP:",
        "it": "IP:",
        "ja": "IP：",
        "zh": "IP：",
        "ru": "IP:",
        "ko": "IP:",
    },
    "lbl_port": {
        "pt": "Porta:",
        "en": "Port:",
        "es": "Puerto:",
        "fr": "Port :",
        "de": "Port:",
        "it": "Porta:",
        "ja": "ポート：",
        "zh": "端口：",
        "ru": "Порт:",
        "ko": "포트:",
    },
    "lbl_user": {
        "pt": "Usuário:",
        "en": "User:",
        "es": "Usuario:",
        "fr": "Utilisateur :",
        "de": "Benutzer:",
        "it": "Utente:",
        "ja": "ユーザー：",
        "zh": "用户名：",
        "ru": "Пользователь:",
        "ko": "사용자:",
    },
    "lbl_pass": {
        "pt": "Senha:",
        "en": "Password:",
        "es": "Contraseña:",
        "fr": "Mot de passe :",
        "de": "Passwort:",
        "it": "Password:",
        "ja": "パスワード：",
        "zh": "密码：",
        "ru": "Пароль:",
        "ko": "비밀번호:",
    },
    "lbl_options": {
        "pt": "⚙️ Opções:",
        "en": "⚙️ Options:",
        "es": "⚙️ Opciones:",
        "fr": "⚙️ Options :",
        "de": "⚙️ Optionen:",
        "it": "⚙️ Opzioni:",
        "ja": "⚙️ オプション：",
        "zh": "⚙️ 选项：",
        "ru": "⚙️ Параметры:",
        "ko": "⚙️ 옵션:",
    },
    "chk_invert_x": {
        "pt": "Inverter Horizontal (PTZ)",
        "en": "Invert Horizontal (PTZ)",
        "es": "Invertir Horizontal (PTZ)",
        "fr": "Inverser l'axe horizontal (PTZ)",
        "de": "Horizontal umkehren (PTZ)",
        "it": "Inverti Orizzontale (PTZ)",
        "ja": "水平反転 (PTZ)",
        "zh": "水平反转 (云台)",
        "ru": "Инвертировать по горизонтали (PTZ)",
        "ko": "수평 반전 (PTZ)",
    },
    "chk_autostart": {
        "pt": "Iniciar com o Windows",
        "en": "Start with Windows",
        "es": "Iniciar con Windows",
        "fr": "Démarrer avec Windows",
        "de": "Mit Windows starten",
        "it": "Avvia con Windows",
        "ja": "Windows起動時に実行",
        "zh": "随Windows开机启动",
        "ru": "Запуск вместе с Windows",
        "ko": "Windows 시작 시 실행",
    },
    "chk_start_minimized": {
        "pt": "Iniciar Minimizado",
        "en": "Start Minimized",
        "es": "Iniciar Minimizado",
        "fr": "Démarrer minimisé",
        "de": "Minimiert starten",
        "it": "Avvia ridotto a icona",
        "ja": "最小化で起動",
        "zh": "最小化启动",
        "ru": "Запускать свернутым",
        "ko": "최소화 상태로 시작",
    },
    "btn_reset_cache": {
        "pt": "🧹 Limpar Dados / Cache",
        "en": "🧹 Clear Cache / Data",
        "es": "🧹 Limpiar Datos / Caché",
        "fr": "🧹 Effacer Cache / Données",
        "de": "🧹 Cache / Daten löschen",
        "it": "🧹 Cancella Dati / Cache",
        "ja": "🧹 データ/キャッシュ消去",
        "zh": "🧹 清除缓存与个人数据",
        "ru": "🧹 Очистить данные / кэш",
        "ko": "🧹 캐시 및 데이터 정리",
    },
    "btn_save_connect": {
        "pt": "💾 Salvar e Conectar",
        "en": "💾 Save and Connect",
        "es": "💾 Guardar y Conectar",
        "fr": "💾 Enregistrer et Connecter",
        "de": "💾 Speichern & Verbinden",
        "it": "💾 Salva e Connetti",
        "ja": "💾 保存して接続",
        "zh": "💾 保存并连接",
        "ru": "💾 Сохранить и подключить",
        "ko": "💾 저장 및 연결",
    },
    "lbl_language": {
        "pt": "🌐 Idioma:",
        "en": "🌐 Language:",
        "es": "🌐 Idioma:",
        "fr": "🌐 Langue :",
        "de": "🌐 Sprache:",
        "it": "🌐 Lingua:",
        "ja": "🌐 言語：",
        "zh": "🌐 语言：",
        "ru": "🌐 Язык:",
        "ko": "🌐 언어:",
    },

    # Dialogs & Prompts
    "msg_reset_title": {
        "pt": "Limpar Dados e Cache",
        "en": "Clear Cache and Data",
        "es": "Limpiar Datos y Caché",
        "fr": "Effacer le Cache et les Données",
        "de": "Cache und Daten löschen",
        "it": "Cancella Dati e Cache",
        "ja": "キャッシュとデータの消去",
        "zh": "清除缓存与配置数据",
        "ru": "Очистка данных и кэша",
        "ko": "캐시 및 데이터 정리",
    },
    "msg_reset_body": {
        "pt": (
            "Deseja realmente apagar todos os dados e credenciais salvas?\n\n"
            "• As configurações locais serão redefinidas para o padrão.\n"
            "• Endereço IP, usuário e senha salvos serão apagados deste computador.\n"
            "• Inicialização automática com o Windows será desativada.\n\n"
            "Esta ação limpa completamente seus dados locais."
        ),
        "en": (
            "Do you really want to delete all saved data and credentials?\n\n"
            "• Local settings will be restored to factory defaults.\n"
            "• Saved IP address, username, and password will be wiped.\n"
            "• Windows autostart will be disabled.\n\n"
            "This action completely clears your local private data."
        ),
        "es": (
            "¿Realmente desea eliminar todos los datos y credenciales guardadas?\n\n"
            "• La configuración se restaurará a los valores predeterminados.\n"
            "• Se borrarán la IP, usuario y contraseña guardados.\n"
            "• El inicio automático con Windows se desactivará."
        ),
        "fr": (
            "Voulez-vous vraiment effacer toutes les données et identifiants enregistrés ?\n\n"
            "• Les paramètres locaux seront réinitialisés.\n"
            "• L'adresse IP, le nom d'utilisateur et le mot de passe seront supprimés.\n"
            "• Le démarrage automatique avec Windows sera désactivé."
        ),
        "de": (
            "Möchten Sie wirklich alle gespeicherten Daten und Anmeldeinformationen löschen?\n\n"
            "• Lokale Einstellungen werden auf Werkseinstellungen zurückgesetzt.\n"
            "• Gespeicherte IP, Benutzername und Passwort werden gelöscht.\n"
            "• Windows-Autostart wird deaktiviert."
        ),
        "it": (
            "Vuoi davvero eliminare tutti i dati e le credenziali salvate?\n\n"
            "• Le impostazioni locali verranno ripristinate ai valori predefiniti.\n"
            "• Indirizzo IP, nome utente e password salvati verranno cancellati.\n"
            "• L'avvio automatico con Windows verrà disattivato."
        ),
        "ja": (
            "保存されているすべてのデータと認証情報を削除してもよろしいですか？\n\n"
            "• 設定が初期状態にリセットされます。\n"
            "• 保存されたIPアドレス、ユーザー名、パスワードが消去されます。\n"
            "• Windows自動起動が無効化されます。"
        ),
        "zh": (
            "确定要清除所有保存的本地配置与密码凭证吗？\n\n"
            "• 本地配置将恢复为出厂默认设置。\n"
            "• 保存的IP地址、用户名和密码将被彻底清除。\n"
            "• 开机自启将被关闭。"
        ),
        "ru": (
            "Вы действительно хотите удалить все сохраненные данные и пароли?\n\n"
            "• Настройки будут сброшены к значениям по умолчанию.\n"
            "• Сохраненные IP-адрес, логин и пароль будут удалены.\n"
            "• Автозагрузка с Windows будет отключена."
        ),
        "ko": (
            "저장된 모든 데이터와 자격 증명을 삭제하시겠습니까?\n\n"
            "• 로컬 설정이 기본값으로 초기화됩니다.\n"
            "• 저장된 IP 주소, 사용자 이름 및 비밀번호가 삭제됩니다.\n"
            "• Windows 시작 시 실행이 해제됩니다."
        ),
    },
    "msg_reset_success": {
        "pt": "Todas as informações locais e senhas foram apagadas com sucesso!\nO aplicativo foi restaurado para o estado limpo original.",
        "en": "All local data and passwords have been successfully deleted!\nThe application was restored to its clean initial state.",
        "es": "¡Todos los datos locales y contraseñas han sido eliminados con éxito!\nLa aplicación fue restaurada a su estado limpio original.",
        "fr": "Toutes les données locales et mots de passe ont été supprimés avec succès !\nL'application a été réinitialisée.",
        "de": "Alle lokalen Daten und Passwörter wurden erfolgreich gelöscht!\nDie Anwendung wurde zurückgesetzt.",
        "it": "Tutti i dati locali e le password sono stati eliminati con successo!\nL'applicazione è stata ripristinata.",
        "ja": "ローカルデータとパスワードが正常に消去されました！\nアプリケーションが初期状態に復元されました。",
        "zh": "所有本地数据及密码已成功清除！\n应用已恢复至纯净初始状态。",
        "ru": "Все локальные данные и пароли успешно удалены!\nПриложение сброшено к исходному состоянию.",
        "ko": "모든 로컬 데이터와 비밀번호가 삭제되었습니다!\n응용 프로그램이 초기 상태로 복원되었습니다.",
    },
    "msg_reboot_title": {
        "pt": "Reiniciar Câmera",
        "en": "Reboot Camera",
        "es": "Reiniciar Cámara",
        "fr": "Redémarrer la caméra",
        "de": "Kamera neustarten",
        "it": "Riavvia Telecamera",
        "ja": "カメラ再起動",
        "zh": "重启摄像头",
        "ru": "Перезагрузка камеры",
        "ko": "카메라 재부팅",
    },
    "msg_reboot_body": {
        "pt": "Deseja realmente reiniciar o hardware da câmera agora?\nA transmissão será interrompida temporariamente durante o reinício.",
        "en": "Do you really want to reboot the camera hardware now?\nThe video stream will temporarily stop during reboot.",
        "es": "¿Desea realmente reiniciar la cámara ahora?\nLa transmisión se detendrá temporalmente durante el reinicio.",
        "fr": "Voulez-vous vraiment redémarrer la caméra maintenant ?\nLe flux sera temporairement interrompu.",
        "de": "Möchten Sie die Kamera jetzt wirklich neu starten?\nDer Videostream wird vorübergehend unterbrochen.",
        "it": "Vuoi davvero riavviare la telecamera adesso?\nLo streaming verrà interrotto temporaneamente.",
        "ja": "今すぐカメラのハードウェアを再起動しますか？\n再起動中は映像が一時的に停止します。",
        "zh": "确定要立即重启摄像头硬件吗？\n重启过程中视频画面将暂时中断。",
        "ru": "Перезагрузить камеру прямо сейчас?\nТрансляция временно прервется.",
        "ko": "지금 카메라를 재부팅하시겠습니까?\n재부팅하는 동안 영상이 일시 중지됩니다.",
    },
}

def set_language(lang_code: str) -> None:
    """Sets the active language code and triggers all registered UI listeners."""
    global _current_lang
    if any(code == lang_code for code, _ in LANGUAGES):
        _current_lang = lang_code
        for listener in _listeners:
            try:
                listener()
            except Exception as e:
                print(f"[i18n] Listener error: {e}")

def get_language() -> str:
    """Returns the current active language code."""
    return _current_lang

def tr(key: str, default: str = "") -> str:
    """Translates a given translation key into the active language."""
    entry = STRINGS.get(key)
    if entry:
        return entry.get(_current_lang) or entry.get("en") or entry.get("pt") or default or key
    return default or key

def register_listener(fn: Callable[[], None]) -> None:
    """Registers a callback function to be invoked whenever language changes."""
    if fn not in _listeners:
        _listeners.append(fn)

def unregister_listener(fn: Callable[[], None]) -> None:
    """Unregisters a previously registered callback function."""
    if fn in _listeners:
        _listeners.remove(fn)

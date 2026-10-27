# 🤖 Arquitetura Técnica e Guia para Agentes de IA (AGENTS.md)

<p align="center">
  <b>🇧🇷 Português</b> | <a href="AGENTS.en.md">🇺🇸 English</a>
</p>

Este documento é o guia canônico para engenheiros de software, LLMs e agentes autônomos de IA responsáveis pela manutenção, depuração, teste ou expansão do projeto **ICSee Desktop Viewer**.

---

## 1. Visão Geral do Sistema

O aplicativo é um cliente desktop Windows assíncrono e orientada a eventos, desenvolvido em **Python 3.12**, **PyQt6**, **OpenCV (cv2)**, **onvif-zeep**, **pygame-ce** e **PyAudio**. Comunica-se diretamente com câmeras IP de segurança baseadas em chipsets Xiongmai / Sofia (especificamente a linha de lente dupla `XM535_X6E-WEQ_8M`), além de câmeras genéricas compatíveis com o padrão ONVIF.

```
+------------------------------------------------------------------------------------+
|                               Thread Principal GUI PyQt6                           |
|                                  (main_window.py)                                  |
|   +--------------------+  +----------------------+  +--------------------------+   |
|   | Top Bar Dinâmica   |  | Painel Configurações |  |   Canvas VideoWidget     |   |
|   | - Botões dinâmicos |  | - IP / Porta / User  |  | - Slicer de Lente Dupla  |   |
|   | - Alternar SD / HD |  | - Ocultar/Exibir Senh|  | - Zoom Digital (Ctrl+Wh) |   |
|   | - Layout ⯀ / ⚏     |  | - Limpar Cache/Dados |  | - Toasts Failsafe (3s/5s)|   |
|   | - 📸 Fotos         |  | - 10 Idiomas Nativos |  | - Flash de Obturador     |   |
|   +--------------------+  +----------------------+  +--------------------------+   |
|                              |                      | Painel Lateral ScrollArea|   |
|                              |                      |  - D-Pad + Botão Pausar  |   |
|                              |                      |  - 🤖 Auto-Rastreamento  |   |
|                              |                      |  - 💡 Controle de Luz/LED|   |
|                              |                      |  - 🔊 Ouvir / 🎙️ Falar   |   |
|                              |                      |  - 🎥 Gravador MP4       |   |
+------------------------------------------------------------------------------------+
           |                             |                             ^
           | (PTZ rápido & Tracking)     | (Troca a quente de URL)     | (Quadros QImage)
           v                             v                             |
+---------------------+        +--------------------+        +---------------------+
|    CameraManager    |        |    VideoWorker     |        |    GamepadWorker    |
| (camera_manager.py) |        |  (video_worker.py) |        |  (gamepad_worker.py)|
| - Sofia TCP :34567  |        | - RTSP Porta 554   |        | - pygame-ce @ 25Hz  |
| - ONVIF Porta 8899  |        | - cv2.VideoCapture |        | - DualSense / Xbox  |
| - Detect.DetectTrack|        | - Hot-swap URL     |        | - Controle analógico|
| - OPPTZControl ~60ms|        | - Transporte TCP   |        | - Parada PTZ & Ação |
+---------------------+        +--------------------+        +---------------------+
           |
           +---------------------------+---------------------------+
           v                           v                           v
+---------------------+     +---------------------+     +---------------------+
|    VideoRecorder    |     | CameraAudioReceiver |     |  CameraAudioTalker  |
| (cv2.VideoWriter)   |     | (audio_manager.py)  |     | (audio_manager.py)  |
| - Codec mp4v        |     | - Sofia Porta 34567 |     | - Sofia Porta 34567 |
| - Fila de quadros   |     | - Saída PyAudio     |     | - Microfone PC + AGC|
| - Worker secundário |     | - G.711A / PCM16    |     | - TALK_CU_PU_DATA   |
+---------------------+     +---------------------+     +---------------------+
```

---

## 2. Perfil de Hardware e Protocolos Xiongmai

- **SoC:** Xiongmai XM535 (`XM535_X6E-WEQ_8M` ou compatíveis da linha Xiongmai/Sofia).
- **Arquitetura de Lentes:** Sensor Duplo.
  - Sensor 1 (Superior): Lente motorizada PTZ móvel.
  - Sensor 2 (Inferior): Lente fixa grande-angular panorâmica.
- **Composição de Vídeo:** O codificador de hardware multiplexa ambos os sensores em um único quadro empilhado verticalmente:
  - **Sub-stream (SD):** `640 x 720` (cada lente tem `640 x 360`).
  - **Main-stream (HD):** `2304 x 2592` (cada lente tem `2304 x 1296`).

### 2.1 Autenticação RTSP Xiongmai
Clientes ONVIF comuns solicitam a URL pelo método `GetStreamUri`. Contudo, ao definir senha na câmera pelo app móvel ICSee em **Configurações Avançadas > NVR/IPC**:
1. O serviço ONVIF na porta 8899 retorna uma URL desprotegida sem token:
   `rtsp://<ip>:554/channel=0_stream=0&onvif=0.sdp?real_stream`
2. Conexões RTSP padrão com cabeçalhos HTTP Digest ou Basic resultam em `401 Unauthorized` ou reset de socket pelo firmware.
3. **Solução implementada:** O firmware Xiongmai requer as credenciais inseridas diretamente como parâmetros na URL RTSP:
   ```text
   rtsp://<ip>:554/user=<user>_password=<pass>_channel=0_stream=<0|1>.sdp?real_stream
   ```
   - `stream=0`: Main-stream (HD Ultra).
   - `stream=1`: Sub-stream (SD Fluido).

### 2.2 Protocolo Sofia NetSDK (Porta TCP 34567)
Enquanto o vídeo trafega via RTSP na porta 554, todos os comandos de controle PTZ, inteligência de rastreamento de pessoas, controle dos refletores de LED e intercomunicação de áudio operam via protocolo binário Sofia NetSDK na porta TCP 34567:
- **Cabeçalho:** 20 bytes iniciados por `\xff\x00\x00\x00`.
- **Campos estruturais:**
  - `0x00`: Byte Mágico (`0xFF`)
  - `0x04`: Session ID (atribuído no login `LOGIN_REQ 1000`)
  - `0x08`: Número de Sequência
  - `0x0c`: ID da Mensagem (`1436` para PTZ, `1040` para Configurações)
  - `0x10`: Tamanho do Payload (uint32 little-endian)
  - `0x14`: Conteúdo JSON formatado

### 2.3 Protocolo de Áudio Bidirecional (Talkback)
1. **Sessão:** Autentica conexão socket na porta 34567.
2. **Reivindicação de Canal:** `TALK_CLAIM` (`msg_id=1434`) reserva o canal de áudio da câmera.
3. **Início da Transmissão:** `TALK_REQ` (`msg_id=1430`) inicia o streaming.
4. **Envio de Quadros de Voz:** `TALK_CU_PU_DATA` (`msg_id=1432`):
   - Subcabeçalho de 8 bytes: `\x00\x00\x01\xfa\x0e\x02@\x01`
   - Quadros codificados em G.711A (PCMA) (8000 Hz, 16 bits mono, 320 bytes por quadro de 40ms).
   - Ganho digital via software (3.5x com soft limiter) para assegurar clareza e audibilidade mesmo em ambientes abertos e ruidosos.

---

## 3. Divisão de Módulos

### 3.1 `camera_manager.py`
- `SofiaClient`: Cliente socket TCP de alta velocidade (~60ms de latência de comando).
- `CameraManager`: Descoberta ONVIF, enumeração de perfis, controle PTZ, rastreamento humano e alternância de modos de iluminação noturna/holofote.

### 3.2 `video_worker.py`
- Thread dedicada `QThread` encapsulando `cv2.VideoCapture`.
- Decodificação eficiente para `QImage` (RGB888).
- Troca de fluxo sem vazamento de memória ou travamento de interface.

### 3.3 `audio_manager.py`
- `CameraAudioReceiver`: Escuta o microfone da câmera e reproduz nas caixas de som do PC.
- `CameraTalkWorker`: Captura o microfone do computador, aplica ganho digital e transmite continuamente ao alto-falante externo da câmera.

### 3.4 `i18n.py`
- Motor de internacionalização com 10 idiomas nativos: `pt`, `en`, `es`, `fr`, `de`, `it`, `ja`, `zh`, `ru`, `ko`.
- Padrão de ouvintes reativos que atualiza a interface dinamicamente sem necessidade de reiniciar.

### 3.5 `gamepad_worker.py`
- Coleta de eventos assíncrona em 25Hz via `pygame-ce`.
- Suporte a DualSense (PS5), DualShock 4 (PS4), Xbox e genéricos DirectInput/XInput.

### 3.6 `main_window.py`
- Interface principal PyQt6.
- Renderização canvas com divisão inteligente de lente dupla, zoom digital de até 5.0x e navegação suave.
- Botão "Limpar Dados / Cache" para remoção total de dados locais.

---

## 4. Esquema de Configuração (`config.json`)

```json
{
  "ip": "192.168.1.10",
  "port": 8899,
  "user": "admin",
  "password": "",
  "quality": "sub",
  "layout_mode": "vertical",
  "speed": 0.5,
  "invert_x": true,
  "invert_y": false,
  "always_on_top": false,
  "start_with_windows": false,
  "start_minimized": false,
  "window_width": 960,
  "window_height": 560,
  "lang": "pt"
}
```

---

## 5. Diretrizes de Segurança e Privacidade

- **Nunca comitar `config.json`**: O arquivo contém IPs e senhas pessoais e deve permanecer no `.gitignore`.
- **Use `config.example.json`**: Fornece o modelo limpo para novos usuários.
- **Limpeza de Cache**: O botão na interface restaura instantaneamente os padrões seguros e remove credenciais salvas.

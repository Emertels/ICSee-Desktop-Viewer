# 📷 ICSee Desktop Viewer

<p align="center">
  <b>🇧🇷 Português</b> | <a href="README.en.md">🇺🇸 English</a>
</p>

[![Release](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](https://github.com/Emertels/ICSee-Desktop-Viewer/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Streaming](https://img.shields.io/badge/Streaming-OpenCV%20%2F%20RTSP-orange.svg)](https://opencv.org/)
[![Recording](https://img.shields.io/badge/Recording-Universal%20MP4-red.svg)](https://en.wikipedia.org/wiki/MP4_file_format)
[![Gamepad Support](https://img.shields.io/badge/Gamepad-DualSense%20%7C%20Xbox-purple.svg)](https://github.com/pygame-community/pygame-ce)
[![i18n](https://img.shields.io/badge/i18n-10%20Idiomas-success.svg)](#-suporte-a-10-idiomas-nativos)
[![Portable Build](https://img.shields.io/badge/Build-Portable%20EXE-blueviolet.svg)](https://github.com/Emertels/ICSee-Desktop-Viewer/releases)
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)
[![OS](https://img.shields.io/badge/OS-Windows%2010%20%2F%2011-0078D6.svg)](https://www.microsoft.com/windows)

Um aplicativo desktop moderno, ultraleve, portátil e de alto desempenho para Windows, projetado para visualizar, gravar e controlar câmeras de segurança **ICSee / Xiongmai (XM535 / dual lens / lentes duplas)** e câmeras **ONVIF** em tempo real, **sem precisar de navegador** e sem depender de plugins obsoletos.

---

## ✨ Principais Funcionalidades

- **🔍 Auto-Descoberta Inteligente (WS-Discovery):** Varredura automática via protocolo **ONVIF WS-Discovery** e varredura de sub-rede local para detecção instantânea das câmeras na rede local com nome completo sem cortes.
- **⚡ Transmissão de Baixíssima Latência:** Decodificação direta via **RTSP/FFmpeg** com alternância a quente (*hot-swap*) instantânea entre os fluxos **SD Fluido (640x720)** e **HD Ultra (2304x2592)**.
- **🔊 Áudio Bidirecional Completo (Intercomunicador 2-Way):**
  - **🔊 Ouvir Áudio:** Clique para escutar o áudio captado pelo microfone da câmera em tempo real através dos alto-falantes/fones do seu computador.
  - **🎙️ Falar na Câmera (Comunicação Contínua com 1 Clique):** Clique uma vez para ativar a transmissão contínua do seu microfone do PC diretamente para o alto-falante externo da câmera (com ganho digital 3.5x e soft limiting para alta clareza ao ar livre), e clique novamente para desativar. Não requer ficar segurando o botão.
- **🔎 Zoom Digital com `Ctrl` + Roda do Mouse:**
  - Aumente o zoom até **5.0x** suavemente em qualquer área do vídeo usando `Ctrl` + Scroll do mouse.
  - Navegue e arraste livremente com o botão esquerdo do mouse para inspecionar detalhes.
  - Dois cliques restauram a visão panorâmica total (1.0x).
- **📐 Visualização Inteligente de Lente Dupla (Dual-Lens):**
  - **Modo Normal (Vertical):** Lente superior (PTZ móvel) sobre a lente inferior (fixa/panorâmica).
  - **Modo Lado a Lado (Horizontal):** Ambas as lentes dispostas lado a lado em proporção panorâmica uniforme.
  - **2 Cliques no Mouse / Gatilhos L2 e R2:** Expanda individualmente a lente superior ou inferior para tela inteira com 2 cliques rápidos ou pelos gatilhos do controle.
- **⏸️ Pausar e Retomar Vídeo Instantaneamente:** Botão central no D-Pad (`⏸` / `▶`) ou tecla `Espaço` com overlay visual elegante.
- **🎥 Gravação de Vídeo Universal MP4 com Desligamento Automático do PC:**
  - Grava diretamente na pasta **Vídeos (`Videos`)** do usuário com zero sobrecarga de CPU.
  - Seletor de duração: **Ininterrupto (Sem limite)**, **15 min**, **30 min**, **1h**, **2h**, **4h**, **6h**, **8h**, **10h**, **12h** e **24h**.
  - **Opção Desligar PC ao finalizar:** Desliga automaticamente o computador com aviso de segurança de 60s ao término de gravações programadas.
- **🤖 Modo Automático (Rastreamento Humano Inteligente - Human Tracking):**
  - Acionamento assíncrono via protocolo de alta velocidade Sofia NetSDK para rastrear pessoas detectadas automaticamente no campo visual.
- **💡 Iluminação & Holofotes Noturnos:**
  - **🌙 Modo Noturno:** Visão noturna padrão por infravermelho (preto e branco) com holofotes desligados.
  - **💡 Modo Iluminado:** Acende os LEDs de luz branca da câmera para iluminar o ambiente e filmar em cores plenas no escuro.
- **🔄 Reiniciar Hardware Remotamente:** Botão para reiniciar o hardware da câmera remotamente via rede com reconexão automática após o reboot.
- **🎮 Suporte Nativo a Controles de Videogame:**
  - Suporte completo a **Sony PlayStation DualSense (PS5) / DualShock 4 (PS4)** e controles **Microsoft Xbox (Series, One, 360)**.
  - Giro analógico suave e proporcional via stick esquerdo.
- **🧹 Limpar Dados / Cache (Privacidade & Reset de Fábrica):**
  - Botão integrado no painel de configurações para apagar senhas, IPs salvos e preferências locais em 1 clique, ideal antes de compartilhar ou migrar de computador.
- **🌐 10 Idiomas Nativos Integrados:**
  - Interface com tradução nativa completa para **Português (Brasil)**, **English**, **Español**, **Français**, **Deutsch**, **Italiano**, **日本語**, **简体中文**, **Русский** e **한국어**, selecionáveis a qualquer momento.
- **🪟 Iniciar com o Windows & Iniciar Minimizado:** Opção integrada no registro do Windows para inicialização automática silenciosa na bandeja/barra de tarefas.
- **📦 100% Portátil:** Pode ser empacotado em um executável autônomo `.exe` que roda direto de um pendrive ou partição sem necessidade de ter Python instalado.

---

## 📹 Compatibilidade de Câmeras

| Tipo de Câmera | Detecção / Descoberta | Transmissão de Vídeo | Controles PTZ | Recursos Avançados (Áudio, Luz, Rastreamento) |
| :--- | :---: | :---: | :---: | :---: |
| **Câmeras ICSee / Xiongmai / XMeye (XM535 / Sofia)** | ✅ Automática (WS-Discovery + Sofia) | ✅ RTSP SD & HD Ultra | ✅ Sofia Ultra-rápido (~60ms) | ✅ 100% Suportado (Áudio 2-Way, LEDs, Human Tracking) |
| **Câmeras ONVIF Genéricas (Intelbras, Hikvision, Dahua, Tapo, etc.)** | ✅ Automática (WS-Discovery) | ✅ RTSP ONVIF Padrão | ✅ ONVIF ContinuousMove | ⚠️ Depende dos perfis ONVIF do fabricante |

> **Nota:** O sistema faz a busca de câmeras na rede utilizando o padrão aberto **ONVIF WS-Discovery** (multicast `239.255.255.250:3702`). Qualquer câmera compatível com o padrão ONVIF será detectada e poderá ter seu vídeo transmitido. Os recursos proprietários (como acendimento de holofote LED, comando de áudio bidirecional e inteligência de rastreamento humano Sofia) são projetados especificamente para placas e SoCs Xiongmai/ICSee.

---

## 🎮 Tabela de Controles e Atalhos

| Ação | Teclado | Mouse / Interface | Sony DualSense (PS5) | Microsoft Xbox |
| :--- | :---: | :---: | :---: | :---: |
| **Girar Câmera (Pan / Tilt)** | `↑` `↓` `←` `→` | Botões D-Pad (`▲` `▼` `◀` `▶`) | Analógico Esquerdo / D-Pad | Analógico Esquerdo / D-Pad |
| **Pausar / Retomar Câmera** | `Espaço` | Botão Central D-Pad (`⏸` / `▶`) | Botão Círculo (`○`) | Botão `B` |
| **Ampliar Câmera Superior / Esquerda** | — | Dois cliques na câmera superior/esquerda | Gatilho `L2` | Gatilho `LT` |
| **Ampliar Câmera Inferior / Direita** | — | Dois cliques na câmera inferior/direita | Gatilho `R2` | Gatilho `RT` |
| **Zoom Digital no Ponto do Cursor** | `Ctrl` + Scroll | `Ctrl` + Roda do Mouse (até 5.0x) | — | — |
| **Mover / Navegar no Zoom (Pan)** | — | Clique e arraste com o botão esquerdo | — | — |
| **Redefinir Zoom para 1.0x** | — | Dois cliques no vídeo com zoom | — | — |
| **Restaurar Ambas as Lentes** | — | Dois cliques no vídeo sem zoom | `L2` ou `R2` | `LT` ou `RT` |
| **Giro Rápido (Toque Curto)** | — | Botões `↶ Esquerda` / `Direita ↷` | — | — |
| **Gravar Vídeo (MP4)** | `R` | Botão `🔴 Iniciar` / `⏹️ Interromper` | — | — |
| **Captura de Tela (Foto)** | `S` | Botão `📸 Foto` | Botão Triângulo (`△`) | Botão `Y` |
| **Alternar Visão (Normal / Lado a Lado)** | — | Botões `⯀ Normal` / `⚏ Lado a Lado` | Botão Quadrado (`□`) | Botão `X` |
| **Qualidade SD Fluido (640x720)** | — | Botão `⚡ SD` | Botão `L1` | Botão `LB` |
| **Qualidade HD Ultra (2304x2592)** | — | Botão `🌟 HD` | Botão `R1` | Botão `RB` |
| **Abrir Painel de Dicas** | — | Botão `🎮 Dicas` | — | — |
| **Fixar Janela no Topo** | `T` | Botão `📌 Fixar` | — | — |
| **Tela Cheia (Full Screen)** | `F11` | Oculta barra de tarefas do Windows | — | — |

---

## 🚀 Instalação e Execução

### Opção 1: Usando a Versão Portátil (Recomendado para Usuários)
1. Baixe ou acesse a pasta da versão portátil (`dist/ICSee_Viewer/` ou `ICSee_Viewer_Portatil`).
2. Dê um duplo clique em `ICSee_Viewer.exe`.
3. Pronto! Não requer instalação de Python, bibliotecas ou dependências.

### Opção 2: A Partir do Código Fonte (Desenvolvedores)

#### Pré-requisitos
- **Windows 10 ou 11 (64 bits)**
- **Python 3.10 ou superior**

#### Passos
```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/icsee-desktop-viewer.git
cd icsee-desktop-viewer

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Executar o aplicativo
python app.py
```

### Compilar a Versão Portátil (.exe)
Para gerar sua própria pasta portátil independente:
```bash
python build_exe.py
```
O executável compilado com todos os componentes necessários será gerado na pasta `dist/ICSee_Viewer/`.

---

## ⚙️ Configuração e Privacidade

1. Clique no ícone **⚙️** no canto superior direito para abrir as configurações.
2. Defina os campos de conexão:
   - **IP:** Endereço IP da câmera (ex: `192.168.1.100`).
   - **Porta:** Padrão `8899`.
   - **Usuário:** Nome do usuário (padrão de fábrica: `admin`).
   - **Senha:** Digite a senha cadastrada na câmera (use o botão `👁️` para verificar).
3. Clique em **💾 Salvar e Conectar**.
4. **Para Limpar Dados:** Utilize o botão **🧹 Limpar Dados / Cache** para restaurar instantaneamente as configurações para o padrão limpo de fábrica e apagar senhas e histórico salvos.

---

## 📁 Estrutura do Projeto

```text
icsee-desktop-viewer/
├── app.py                  # Ponto de entrada da aplicação
├── main_window.py          # Janela principal PyQt6, gravação MP4, layouts e canvas
├── camera_manager.py       # Gerenciador de conexão ONVIF/Sofia e construtor RTSP
├── audio_manager.py        # Módulos de recepção e intercomunicação bidirecional (PyAudio/Sofia)
├── video_worker.py         # Thread de decodificação de vídeo em tempo real (OpenCV)
├── gamepad_worker.py       # Driver de entrada para controles DualSense e Xbox (pygame-ce)
├── build_exe.py            # Script automatizado para geração da versão portátil
├── config.example.json     # Modelo limpo de configuração para novos usuários
├── Iniciar_Camera.bat      # Inicializador silencioso para Windows
├── Iniciar_Com_Console.bat # Inicializador com console de depuração
├── requirements.txt        # Dependências do projeto
├── LICENSE                 # Licença de código aberto MIT
├── README.md               # Apresentação do projeto e visão geral
├── MANUAL.md               # Manual de instruções detalhado
└── AGENTS.md               # Especificação técnica para desenvolvedores e agentes IA
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais informações.

---

## 👨‍💻 Sobre o Autor

Desenvolvido e mantido por **Emerson Teles** (conhecido na comunidade como **Emertels**).

Entusiasta de tecnologia, informática, jogos, manutenção de sistemas e tradução/localização de softwares para Português do Brasil (PT-BR). Desenvolvedor focado em utilitários práticos, ferramentas de produtividade, automação inteligente em PowerShell e soluções completas de localização técnica que aproximam ferramentas modernas do público brasileiro.

### 🛠️ Projetos & Contribuições

- [AI-Chat-Vault](https://github.com/Emertels/AI-Chat-Vault) — Backup portátil e recuperação de conversas locais de 20+ ferramentas e assistentes de IA.
- [Antigravity — Tradução PT-BR](https://github.com/Emertels/Antigravity-Traducao-PTBR) — Localização completa do Google Antigravity Desktop para Português do Brasil.
- [Codex Router — Tradução PT-BR](https://github.com/Emertels/CodexRouter-Traducao-PTBR) — Pacote de tradução e localização do Codex Router Control Center em PT-BR.
- [Cursor AI — Tradução PT-BR](https://github.com/Emertels/Cursor-Traducao-PTBR) — Localização completa e profunda do Cursor AI para Português do Brasil.
- [Devin AI — Tradução PT-BR](https://github.com/Emertels/Devin-Traducao-PTBR) — Tradução e localização completa do Devin Desktop para Português do Brasil.
- [GPU Tweak III — Tradução PT-BR](https://github.com/Emertels/GPU-Tweak-III-Traducao-PTBR) — Tradução em português brasileiro e instalador automatizado para ASUS GPU Tweak III.
- [ICSee Desktop Viewer](https://github.com/Emertels/ICSee-Desktop-Viewer) — Aplicativo desktop moderno e portátil para visualização e controle de câmeras ICSee e ONVIF no Windows.
- [Microsoft Photos Fix](https://github.com/Emertels/Microsoft-Photos-Fix) — Solução definitiva em PowerShell e C# para rota de inicialização rápida e visualização no app Fotos do Windows.
- [PSBBN-Translator](https://github.com/Emertels/PSBBN-Translator) — Suíte corporativa de tradução e localização para o PSBBN Definitive Project (PlayStation 2) em 40 idiomas.
- [Silent Hill: Homecoming — Tradução PT-BR](https://github.com/Emertels/Silent-Hill-Homecoming-Traducao-PTBR) — Tradução e revisão completa do jogo para PC em português brasileiro.
- [Suite-Emuladores](https://github.com/Emertels/Suite-Emuladores) — Suíte inteligente em PowerShell para download e atualização autônoma de 56 emuladores e frontends no Windows.
- [Xbox 360 Controller Calibration Tool](https://github.com/Emertels/Xbox-360-Controller-Calibration-Tool) — Ferramenta profissional para calibração avançada de controles Xbox 360 no Windows.
- [ZCode — Tradução PT-BR](https://github.com/Emertels/ZCode-Traducao-PTBR) — Tradução e localização completa do ZCode Desktop para Português do Brasil.

### 🌐 Conecte-se comigo & Comunidades Oficiais

<div align="left">

[![GitHub](https://img.shields.io/badge/GitHub-Emertels-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/emertels)
[![Website](https://img.shields.io/badge/Website-Emerson_Teles-0070F3?style=for-the-badge&logo=googlechrome&logoColor=white)](https://emertels.github.io)
[![Discord](https://img.shields.io/badge/Discord-Emertels%20Server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://emertels.github.io/discord)
[![X / Twitter](https://img.shields.io/badge/X_Twitter-@emertels-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/emertels)
[![YouTube](https://img.shields.io/badge/YouTube-Emerson_Teles-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@emersonteles2379)
[![Telegram](https://img.shields.io/badge/Telegram-Aplicativos%20Mods-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/apksmodsandroid)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Apoiar%20Projeto-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/emertels)

</div>


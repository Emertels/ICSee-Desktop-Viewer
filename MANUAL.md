# 📖 Manual do Usuário - ICSee Desktop Viewer

Guia de instruções e referência de uso do **ICSee Desktop Viewer** para câmeras de segurança Xiongmai / ICSee com lente dupla (*Dual-Lens*).

---

## 📑 Índice
1. [Visão Geral](#1-visão-geral)
2. [Pré-requisitos e Instalação](#2-pré-requisitos-e-instalação)
3. [Como Iniciar o Aplicativo](#3-como-iniciar-o-aplicativo)
4. [Configuração de Rede, Usuário e Senha](#4-configuração-de-rede-usuário-e-senha)
5. [Modos de Visão das Duas Lentes](#5-modos-de-visão-das-duas-lentes)
6. [Resolução e Qualidade de Imagem (SD vs HD)](#6-resolução-e-qualidade-de-imagem-sd-vs-hd)
7. [Pausar e Retomar a Câmera](#7-pausar-e-retomar-a-câmera)
8. [Controle de Giro da Câmera (PTZ)](#8-controle-de-giro-da-câmera-ptz)
9. [Uso de Controles de Videogame (DualSense e Xbox)](#9-uso-de-controles-de-videogame-dualsense-e-xbox)
10. [Gravação de Vídeo em Formato Universal MP4](#10-gravação-de-vídeo-em-formato-universal-mp4)
11. [Modo Automático (Rastreamento Humano)](#11-modo-automático-rastreamento-humano)
12. [Captura de Tela Instantânea (Snapshot)](#12-captura-de-tela-instantânea-snapshot)
13. [Painel de Dicas e Atalhos](#13-painel-de-dicas-e-atalhos)
14. [Barra Lateral com Rolagem Suave (Sem Sobreposição)](#14-barra-lateral-com-rolagem-suave-sem-sobreposição)
15. [Iniciar com o Windows](#15-iniciar-com-o-windows)
16. [Perguntas Frequentes e Solução de Problemas](#16-perguntas-frequentes-e-solução-de-problemas)

---

## 1. Visão Geral

O **ICSee Desktop Viewer** é uma solução completa para visualização, gravação e controle de câmeras IP baseadas na tecnologia Xiongmai / ICSee. Ao contrário dos programas pesados ou plugins ActiveX antigos, o aplicativo se comunica diretamente pelos protocolos de rede:
- **ONVIF (porta 8899):** Para descoberta e comandos de giro motorizado (PTZ).
- **RTSP (porta 554):** Para transmissão do vídeo em tempo real com baixa latência.
- **Gravação MP4:** Gravação em segundo plano diretamente para a pasta Vídeos.

O aplicativo é calibrado para modelos de **lente dupla** (como a `XM535_X6E-WEQ_8M`), multiplexando os dois sensores em um quadro de alta definição.

---

## 2. Pré-requisitos e Instalação

### Requisitos do Computador
- **Sistema:** Windows 10 ou Windows 11 (64 bits).
- **Rede:** O computador deve estar conectado na **mesma rede local (Wi-Fi ou cabo Ethernet)** da câmera.
- **Python:** Versão 3.10 ou superior.

### Instalação Passo a Passo
1. Baixe e instale o Python marcando a caixa **"Add Python to PATH"**.
2. Abra o terminal (PowerShell ou Prompt de Comando) na pasta do projeto.
3. Instale os módulos necessários executando:
   ```cmd
   pip install -r requirements.txt
   ```

---

## 3. Como Iniciar o Aplicativo

Você pode abrir o aplicativo de três formas simples:

1. **Atalho da Área de Trabalho:**
   - Dê um duplo clique no ícone **Câmera ICSee** criado na sua Área de Trabalho.
2. **Arquivo de Inicialização Silenciosa:**
   - Dê um duplo clique no arquivo `Iniciar_Camera.bat` dentro da pasta do programa. Ele executa silenciosamente em segundo plano, sem abrir janelas pretas do terminal.
3. **Pelo Executável Portátil:**
   - Dê um duplo clique em `ICSee_Viewer.exe` (na pasta portátil ou compilada `dist\ICSee_Viewer`), rodando de forma 100% autônoma sem requerer Python instalado.
4. **Pelo Terminal (Modo Diagnóstico):**
   - Execute `python app.py` ou abra o arquivo `Iniciar_Com_Console.bat` caso queira visualizar os logs de depuração.

---

## 4. Configuração de Rede, Usuário e Senha

### Usuário Padrão de Fábrica
Na primeira execução, o aplicativo vem configurado com:
- **Usuário:** `admin`
- **Senha:** *(em branco / vazia)*

### Como Configurar Câmeras com Senha (Opção NVR/IPC no App ICSee)
Se você configurou uma senha na câmera pelo app móvel ICSee (no menu **Configurações Avançadas > NVR/IPC > Conexão com senha**):

1. Clique no botão **⚙️** (Configurações) no topo superior direito da janela.
2. O painel se expandirá com os campos organizados:
   - **IP:** Endereço IP da câmera (ex: `192.168.1.100`).
   - **Porta:** Mantenha `8899`.
   - **Usuário:** Digite o usuário cadastrado (ex: `admin`).
   - **Senha:** Digite a senha cadastrada na câmera.
     > *Dica: Clique no botão `👁️` ao lado da senha para visualizá-la e conferir.*
3. Clique no botão **💾 Salvar e Conectar**.
4. Suas credenciais são salvas **imediatamente** no arquivo `config.json` e a conexão é iniciada.

### Como Limpar Todos os Dados e Histórico (Botão Limpar Dados / Cache)
Se você deseja apagar sua senha, endereço IP salvo, histórico de câmeras e preferências locais:
1. Abra o painel **⚙️** (Configurações).
2. Clique no botão **🧹 Limpar Dados / Cache**.
3. Confirme a caixa de diálogo: o aplicativo apagará o arquivo de configuração e restaurará os padrões de fábrica imediatamente, garantindo que nenhum dado pessoal permaneça armazenado no computador.

---

## 5. Modos de Visão das Duas Lentes

As câmeras dual-lens transmitem os dois sensores em um único quadro de vídeo empilhado. O aplicativo oferece dois modos de visualização instantâneos:

### ⯀ Modo Normal (Vertical)
- Exibe o quadro original: a **lente superior (móvel/PTZ)** fica posicionada sobre a **lente inferior (fixa/grande-angular)**.
- Ideal para monitores verticais ou janelas estreitas.

### ⚏ Modo Lado a Lado (Horizontal)
- O aplicativo divide matematicamente o quadro ao meio e posiciona as duas lentes **uma ao lado da outra**.
- Cria uma visão ampla e panorâmica perfeita para telas widescreen e monitores padrão de computador.
- Atalho rápido no controle: Botão **Quadrado (`□`)** no DualSense ou **`X`** no Xbox.

---

## 6. Resolução e Qualidade de Imagem (SD vs HD)

- **⚡ SD (Sub-stream - 640x720):**
  - Consumo mínimo de memória e CPU.
  - Latência praticamente nula (resposta instantânea).
  - Recomendado para redes Wi-Fi ou janelas minimizadas.
- **🌟 HD (Main-stream - 2304x2592):**
  - Resolução máxima ultra-nítida dos sensores de 8 MP.
  - Perfeito para identificar rostos, placas e detalhes finos.

---

## 7. Pausar e Retomar a Câmera

No centro do controle direcional D-Pad existe o botão central de pausa:
- **Ao clicar quando o vídeo está passando:**
  - O fluxo é congelado imediatamente.
  - Qualquer movimento de giro PTZ é interrompido.
  - O botão muda para o ícone de Play `▶` com fundo amarelo dourado.
  - Na tela surge o selo dourado `⏸️ CÂMERA PAUSADA`.
  - Um pop-up verde de **3 segundos** avisa: `⏸️ Câmera Pausada! Clique no botão central para retomar.`
- **Ao clicar quando o vídeo está pausado:**
  - O fluxo é reconectado ao vivo.
  - O botão retorna para o ícone de pausa `⏸` em tom ardósia azulado.
  - Um pop-up verde de **3 segundos** avisa: `▶️ Câmera Iniciada! Transmissão ao vivo retomada.`
- **Atalhos rápidos:** Pressione a **Barra de Espaço** no teclado ou o botão **Círculo (`○`)** / **`B`** no controle.

---

## 8. Zoom de Lente e Zoom Digital Focado no Cursor

Para focar em uma das duas lentes e aproximar detalhes:
- **2 Cliques com o Mouse no Vídeo:**
  - Dê dois cliques na lente superior (ou esquerda no modo lado a lado): ela se expandirá para ocupar toda a área de vídeo do programa.
  - Dê dois cliques na lente inferior (ou direita no modo lado a lado): ela se expandirá na área de vídeo.
  - Dê dois cliques novamente em qualquer ponto do vídeo ampliado para **restaurar a visão das duas lentes juntas**.
- **Gatilhos do Controle DualSense / Xbox:**
  - **Gatilho L2 / LT:** Expande / restaura a lente superior (ou esquerda).
  - **Gatilho R2 / RT:** Expande / restaura a lente inferior (ou direita).
- **🔍 Zoom Digital Contínuo (Ctrl + Scroll do Mouse):**
  - Com a câmera expandida (ou em qualquer modo), **aponte o cursor do mouse exatamente no ponto** que deseja ampliar.
  - **Segure a tecla `Ctrl` e gire a rodinha (scroll) do mouse**:
    - **Girar para cima:** Aproxima o zoom (até 5.0x) exatamente no ponto onde o cursor está apontando.
    - **Girar para baixo:** Afasta o zoom de volta até 1.0x.
  - **Arrastar para Navegar (Pan):** Quando a imagem estiver com zoom (> 1.0x), clique e segure o **botão esquerdo do mouse** para arrastar e navegar livremente pelo quadro ampliado.
  - **Resetar o Zoom com 2 Cliques:** Se a imagem estiver com zoom digital, basta dar dois cliques com o mouse para retornar instantaneamente a 1.0x.
- **🖥️ Tela Cheia Completa (F11):**
  - Pressione **`F11`** a qualquer momento: o programa entra em tela cheia cobrindo 100% do monitor, inclusive a barra de tarefas do Windows, mantendo todos os botões e atalhos perfeitamente acessíveis. Pressione `F11` novamente para restaurar a janela.

---

## 8. Controle de Giro da Câmera (PTZ)

### 1. Pelo Painel D-Pad na Interface
- Clique e segure as setas `▲`, `▼`, `◀`, `▶` para girar a câmera. Ao soltar o mouse, o giro para imediatamente.
- Botão **● / ▶ (Central):** Pausa/Retoma a câmera e freia o movimento.
- Botões **↶ Esquerda** e **Direita ↷:** Dão um pequeno toque rápido de giro (0.35s).
- **Controle de Velocidade:** Deslize a barra para calibrar a velocidade entre Lento (🐢) e Rápido (🐇).

### 2. Pelo Teclado
- **Setas direcionais (`↑`, `↓`, `←`, `→`):** Segure para girar; solte a tecla para parar na hora.
- **Barra de Espaço:** Pausa/Retoma a câmera.

### Inversão Horizontal
Para que o giro para a esquerda na tela corresponda ao ambiente físico, abra o painel **⚙️** e marque a opção **"Inverter Horizontal (PTZ)"**.

---

## 9. Uso de Controles de Videogame (DualSense e Xbox)

O aplicativo detecta e conecta automaticamente qualquer controle USB ou Bluetooth plugado no computador, exibindo o selo `🎮 [Nome do Controle]` na barra inferior.

### Mapeamento dos Controles:
- **Analógico Esquerdo / Analógico Direito:** Giro livre com sensibilidade proporcional (quanto mais inclina, mais rápido vira).
- **D-Pad (Cruzeta direcional):** Giro em passos direcionais.
- **Botão Círculo (`○` no DualSense) / Botão `B` (Xbox):** Pausar / Retomar Câmera (Freio).
- **Gatilho L2 / LT:** Ampliar / Restaurar Câmera Superior ou Esquerda.
- **Gatilho R2 / RT:** Ampliar / Restaurar Câmera Inferior ou Direita.
- **Botão Triângulo (`△` no DualSense) / Botão `Y` (Xbox):** Tira foto instantânea (Snapshot).
- **Botão Quadrado (`□` no DualSense) / Botão `X` (Xbox):** Alterna o modo de visão (Normal ↔ Lado a Lado).
- **Gatilho Superior Esquerdo (`L1` / `LB`):** Ativa qualidade **⚡ SD Fluido**.
- **Gatilho Superior Direito (`R1` / `RB`):** Ativa qualidade **🌟 HD Ultra**.

---

## 10. Gravação de Vídeo em Formato Universal MP4

Grave a transmissão da câmera diretamente no seu computador no padrão universal `.mp4`, sem precisar converter:

1. No painel lateral direito, localize a seção **🎥 Gravação de Vídeo (Universal MP4)**.
2. Selecione a programação desejada no seletor **Tempo**:
   - `Gravar sem limite (Interromper manualmente)`: grava continuamente até você interromper.
   - `Interromper após 15 minutos`, `30 minutos`, `1 hora`, `2 horas`, `4 horas`, `6 horas`, `8 horas`, **`10 horas`**, `12 horas` e `24 horas`.
3. **Opção Desligar PC ao finalizar:**
   - Se você marcar a caixa **"Desligar computador ao finalizar"**, assim que o tempo programado (ex: 10 horas) terminar, o aplicativo salva o arquivo de vídeo e desliga o computador automaticamente (com janela de 60 segundos com opção para cancelar).
4. Clique em **🔴 Iniciar Gravação** (ou aperte a tecla **`R`** no teclado).
5. O botão se transforma em **⏹️ Interromper Gravação** (vermelho vivo). Ao clicar para parar, o botão muda imediatamente para **`⏳ Interrompendo gravação...`** enquanto fecha e salva o arquivo com segurança.
6. Os vídeos são salvos na sua pasta de usuário **Vídeos** (`C:\Usuários\SeuNome\Videos`) com o nome padronizado `Gravacao_ICSee_[Modo]_[Data_Hora].mp4`.
7. Ao interromper ou atingir o tempo limite, um pop-up de **3 segundos** confirma o salvamento.

---

## 11. Iluminação & Visão Noturna (Modo Noturno vs Modo Iluminado)

Logo abaixo da seção de gravação, você encontra o painel de controle das lâmpadas da câmera:
- **🌙 Modo Noturno:**
  - Desliga os holofotes de LED branco e ativa a visão noturna padrão por infravermelho (preto e branco). Ideal para discrição total no escuro.
- **💡 Modo Iluminado:**
  - Acende os holofotes de LED branco da câmera, iluminando todo o ambiente físico e transmitindo a imagem em cores plenas mesmo na escuridão.
- Ambos os modos são acionados instantaneamente no hardware da câmera sem travar a transmissão.

---

## 12. Reiniciar Hardware da Câmera (Reboot Remoto)

Caso a câmera precise de reinicialização sem você ter que ir até ela desligar da tomada:
- Clique no botão **`🔄 Reiniciar Câmera`**.
- Uma janela de confirmação perguntará se deseja reiniciar.
- Ao confirmar, o comando de reinicialização é enviado ao hardware e o aplicativo inicia a contagem de reconexão automática (cerca de 25 a 45 segundos).

---

## 13. Modo Automático (Rastreamento Humano)

No painel lateral, marque a caixa **"🤖 Modo Automático (Pessoas)"**:
- Ativa o modo de detecção e rastreamento de pessoas na câmera.
- Um selo roxo `🤖 Rastreamento Ativo` surge no canto do vídeo.
- Um pop-up verde de **5 segundos** confirma a ativação.
- Para voltar ao controle manual, basta desmarcar a caixa.

---

## 12. Captura de Tela Instantânea (Snapshot)

- **Como acionar:**
  - Clique no botão **📸 Foto** no topo;
  - Pressione a tecla **`S`** no teclado;
  - Ou pressione **Triângulo (`△`)** / **`Y`** no controle.
- **O que acontece ao capturar:**
  - Flash de obturador na tela;
  - Imagem gravada na pasta **Imagens** (`Pictures`);
  - Nome gerado: `Captura_ICSee_[Modo]_[Data_Hora].png`;
  - Pop-up verde na tela exibindo o nome salvo que **some automaticamente após 3 segundos**.

---

## 13. Painel de Dicas e Atalhos

Esqueceu qual botão faz o quê no controle ou no teclado?
- Clique no botão **`🎮 Dicas`** no topo da janela.
- Uma gaveta visual se abrirá exibindo dois cartões completos:
  - **Cartão do Controle:** Lista cada botão do PlayStation DualSense e Xbox.
  - **Cartão do Teclado:** Lista todos os atalhos de navegação, foto (`S`), gravação (`R`), tela cheia (`F11`), pausa (`Espaço`) e fixação (`T`).
- Clique em **✕ Fechar** para recolher a gaveta quando não precisar mais.

---

## 14. Barra Lateral com Rolagem Suave (Sem Sobreposição)

Quando você comprime a tela verticalmente ou reduz a janela:
- O painel lateral direito possui uma barra de rolagem vertical integrada (`QScrollArea`).
- Os botões de giro, o controle de velocidade, os botões rápidos, a caixa de modo automático e a seção de gravação de vídeo **nunca se sobrepõem**.
- Basta rolar a barra lateral para acessar todos os controles confortavelmente.

---

## 15. Iniciar com o Windows & Iniciar Minimizado

Para que a câmera abra automaticamente ao ligar o computador:
1. Abra o menu **⚙️** (Configurações).
2. Marque a opção **"Iniciar com o Windows"**.
3. Se desejar que o programa inicie discretamente sem abrir a janela na tela inteira, marque também **"Iniciar Minimizado"**.
4. Clique em **💾 Salvar e Conectar**.
5. O aplicativo é registrado no Registro do Windows (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`), iniciando de forma silenciosa e minimizada.

---

## 16. Perguntas Frequentes e Solução de Problemas

### 1. O vídeo está preto ou exibe "Falha na autenticação"?
- **Solução:** Abra o menu **⚙️**, use o botão `👁️` para verificar a senha e certifique-se de digitar exatamente as letras minúsculas/maiúsculas cadastradas no app do celular. Clique em **💾 Salvar e Conectar**.

### 2. O nome da câmera na lista aparecia cortado com reticências ("...")?
- **Solução:** O seletor de câmeras foi expandido para exibir a linha inteira sem cortes (ex: `ICSee XM535_X6E-WEQ_8M (192.168.1.100)`).

### 3. Os pop-ups ficavam presos na tela ou duravam muito tempo?
- **Solução:** Todos os pop-ups e avisos somem estritamente em **3 segundos**, desimpedindo a tela rapidamente.

### 4. Onde encontro minhas fotos e gravações?
- **Fotos:** Pasta **Imagens** (`C:\Usuários\SeuNome\Pictures`).
- **Vídeos MP4:** Pasta **Vídeos** (`C:\Usuários\SeuNome\Videos`).

# 🎬 QuickClip

<div align="center">

![Language](https://img.shields.io/badge/Language-Python%203.12-3776AB?style=for-the-badge&logo=python)
![GUI](https://img.shields.io/badge/GUI-Win32%20%7C%20Tkinter-0078D6?style=for-the-badge&logo=windows)
![Encoder](https://img.shields.io/badge/Encoder-Windows%20GameDVR%20(GPU)-107C41?style=for-the-badge&logo=xbox)
![Processing](https://img.shields.io/badge/Processing-FFmpeg%20v7.1-007808?style=for-the-badge&logo=ffmpeg)
![Output](https://img.shields.io/badge/Output-Shorts%209%3A16-FF0000?style=for-the-badge&logo=youtube)
![Platform](https://img.shields.io/badge/OS-Windows%2010%2F11-0078D6?style=for-the-badge&logo=windows)
![Anti-Cheat Safe](https://img.shields.io/badge/Anti--Cheat-100%25%20Safe-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Mini-overlay gamer flutuante de gravação instantânea e conversor automático de jogadas para YouTube Shorts (9:16) no Windows.**

</div>

---

## 🌟 O que é o QuickClip?

O **QuickClip** foi criado para resolver um problema comum de quem joga MMORPGs e outros jogos de PC (como *Aion*): você está enfrentando um Boss ou completando uma missão épica e quer gravar na hora, mas abrir menus pesados ou configurar programas complexos atrapalha a gameplay.

Com o QuickClip, você tem uma mini barra flutuante translúcida no canto da tela. Você clica em **REC**, mata o boss, clica em **STOP**, e o aplicativo cuida de tudo:
1. Grava a 60 FPS com áudio do jogo usando o encoder nativo da sua GPU.
2. Não rouba o foco do jogo (`WS_EX_NOACTIVATE`) — você continua clicando e usando habilidades sem travar a mira.
3. Converte a gravação widescreen (16:9) em um **Shorts vertical (9:16)** estilizado com fundo desfocado em Full HD (1080x1920).
4. Disponibiliza o vídeo pronto e um botão direto para envio no **YouTube Studio**.

---

## ⚡ Recursos Principais

### 🎯 Gravação com 1 Clique (Zero Lag no Jogo)
- Dispara silenciosamente o acelerador de vídeo por hardware do Windows GameDVR (`Win + Alt + R`).
- Usa os chips dedicados da placa de vídeo (NVENC / AMF / QuickSync) com 60 FPS e captura de áudio límpida, sem roubar processamento do jogo.

### 🎬 Pipeline Automático para YouTube Shorts (9:16)
- Assim que você encerra a gravação, o **FFmpeg** embutido formata o clipe para o padrão das redes verticais:
  - **Centro:** Gameplay original nítida sem distorção.
  - **Fundo:** Preenchimento vertical inteligente com desfoque dinâmico (`boxblur=20:5`) e escurecimento suave para dar destaque à ação.
  - **Compatibilidade Mobile:** Codificação H.264 (`-pix_fmt yuv420p`) com `-movflags +faststart` para carregamento imediato em smartphones.

### 🧲 Ergonomia e Foco Gamer (`WS_EX_NOACTIVATE`)
- O HUD utiliza atributos avançados da Win32 API (`WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE`).
- Clicar no botão **NÃO transfere o foco do Windows para o aplicativo**. O cursor do jogo, rotação de câmera e atalhos continuam respondendo no jogo no mesmo milissegundo.
- Arraste suave com o mouse para posicionar o HUD em qualquer canto do monitor.

### 🛡️ Trava de Cliques Acidentais
- Gravações com menos de 2 segundos são descartadas automaticamente (status *"Muito curto"*), evitando poluir o disco com cliques por engano.

### 🚀 Acesso Imediato & YouTube Studio
- Botão dedicado de pasta `[ 📁 ]` para abrir a pasta de clipes finalizados no Windows Explorer.
- Botão dedicado do YouTube `[ ▶ ]` que abre diretamente a página de upload do YouTube Studio no navegador.

---

## 🕹️ Interface do HUD

```
┌──────────────────────────────────────────────────┐
│  [ ⚪ REC ]    00:00        [ 📁 ]    [ ▶ ]      │
└──────────────────────────────────────────────────┘
```

| Elemento | Ação ao Clicar | Descrição |
| :--- | :--- | :--- |
| **`[ ⚪ REC ]`** | Clique esquerdo | Inicia a gravação na hora. Vira `⏹ STOP` com tempo ativo. |
| **`[ ⏹ STOP ]`** | Clique esquerdo | Para a gravação e inicia o processamento do Shorts (`⏳ Criando...`). |
| **`[ 📁 ]`** | Clique esquerdo | Abre o diretório `output/shorts/` com o vídeo selecionado. |
| **`[ ▶ ]`** | Clique esquerdo | Abre a aba de upload do YouTube Studio no seu navegador. |
| **Barra do HUD** | Arrastar | Move o HUD suavemente para qualquer canto da tela. |

---

## 🛠️ Como Executar

### Pré-requisitos
- **Windows 10 ou 11**
- **Python 3.12+**

### 1. Clonar o repositório
```powershell
git clone https://github.com/IuryAlmeidaDev/quickclip.git
cd quickclip
```

### 2. Instalar dependências
```powershell
pip install -r requirements.txt
```

### 3. Iniciar o aplicativo
Basta dar dois cliques no executável de lote:
```powershell
.\run.bat
```
*Ou via linha de comando:*
```powershell
python -m quickclip.app
```

---

## 🧪 Testes Automatizados

O projeto possui **37 testes automatizados** cobrindo todos os módulos (configuração, motor de captura, processador de vídeo, interface gráfica e threads do pipeline):

```powershell
python -m pytest tests/ -v
```

---

## 🛡️ Segurança Anti-Cheat

O QuickClip **não injeta DLLs**, **não intercepta chamadas do DirectX/Vulkan/OpenGL** e não lê nem modifica a memória de nenhum jogo. Ele opera exclusivamente através das APIs oficiais do Windows Desktop (`WS_EX_LAYERED`, `keybd_event`), sendo **100% seguro** contra qualquer sistema anti-cheat (Easy Anti-Cheat, BattlEye, Vanguard, etc.).

---

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE). Desenvolvido por [Iury Almeida](https://github.com/IuryAlmeidaDev).

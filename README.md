# 🎬 Motion Agent

![Versao](https://img.shields.io/badge/versao-1.0.0-blue)
![Plataforma](https://img.shields.io/badge/plataforma-Windows-0078D4?logo=windows)
![Licenca](https://img.shields.io/badge/licenca-MIT-green)
![Status](https://img.shields.io/badge/status-ativo-brightgreen)

Software desktop para Windows que usa Inteligencia Artificial para criar videos motion graphics 2D de forma autonoma. O usuario fornece imagens de referencia, um prompt de estilo e uma chave de API — o agente faz o resto.

---

## Sobre o projeto

Motion Agent e um aplicativo Electron que conecta uma interface React a um agente Python. O agente interpreta cada cena, gera codigo TypeScript/React para o Remotion, salva os arquivos no projeto e aciona a renderizacao final, tudo sem que o usuario precise abrir um editor ou escrever uma linha de codigo.

O fluxo completo funciona assim:

```
Usuario fornece
  imagens por cena + prompt de estilo + chave de API

Agente faz
  le a configuracao via stdin
  analisa referencias visuais com modelo de visao
  gera codigo Remotion por cena (TypeScript/React)
  salva arquivos no projeto (hot-reload automatico)
  verifica coerencia visual entre as cenas
  renderiza o .mp4 via Remotion CLI
  abre a pasta de saida
```

A comunicacao entre o processo Electron e o agente Python acontece por JSON via stdio. O Electron escreve a configuracao no stdin do processo Python e le mensagens de progresso no stdout em tempo real.

---

## Funcionalidades

### Aba Projeto
Configuracoes tecnicas do projeto: resolucao (720p, 1080p, 1080v, 4K, quadrado), FPS, formato de saida (H.264, H.265, WebM, ProRes). Campos para apontar o caminho do projeto Remotion e da pasta de saida. Toggles para modo passo a passo, log detalhado, verificacao de coerencia e abertura automatica da pasta ao finalizar.

### Aba Frames
Gerenciador de cenas com drag and drop para reordenar. Cada frame representa uma cena do video: voce sobe a imagem de referencia, escreve a descricao e define a duracao em segundos. Ha um botao para gerar descricoes automaticas via IA para todos os frames de uma vez.

### Aba Roteiro
Prompt de estilo principal da geracao. Suporta chips rapidos para ritmo, tom, transicoes e tipografia. Modulo de audio integrado com tres modos: gravacao direta pelo microfone, upload de arquivo de audio ou geracao de narrecao via TTS (OpenAI ou ElevenLabs).

### Aba Referencia
Analise de video de referencia via OpenCV + IA de visao. Mood board para upload de imagens de estilo. Extracao automatica de paleta de cores, tipografia e ritmo do material enviado. Gera um prompt sugerido com base na analise que pode ser enviado diretamente para a aba Roteiro.

### Aba API
Selecao de provider entre os 20+ suportados. Campo de modelo principal e modelo de visao separados (util quando voce quer Llama para texto e GPT-4o para interpretar imagens). Configuracoes avancadas: temperatura, max tokens, system prompt customizado, timeout e toggle de streaming.

---

## Providers de IA suportados

| Provider | Tipo | Observacoes |
|---|---|---|
| OpenAI | Cloud | GPT-4o, o1, o3 — recomendado para geracao de codigo |
| Anthropic | Cloud | Claude 3.5 / 4.x — excelente para raciocinio estruturado |
| Google Gemini | Cloud | Gemini 1.5 / 2.0 — contexto de 1M tokens |
| Mistral AI | Cloud | Modelos leves e rapidos |
| Cohere | Cloud | Command R+ |
| Groq | Cloud | Velocidade muito alta (sem visao) |
| Together AI | Cloud | Acesso a dezenas de modelos open |
| Perplexity AI | Cloud | Llama com busca online |
| DeepSeek | Cloud | R1, V3 |
| xAI | Cloud | Grok |
| OpenRouter | Cloud | Uma chave para acessar 100+ modelos |
| Hugging Face | Cloud | Inference API |
| Replicate | Cloud | Modelos hospedados |
| Fireworks AI | Cloud | Inferencia rapida |
| Anyscale | Cloud | Endpoints gerenciados |
| Azure OpenAI | Cloud | Deploy proprio na Azure |
| Amazon Bedrock | Cloud | Claude, Llama via AWS |
| Vertex AI | Cloud | Gemini via Google Cloud |
| Ollama | Local | Qualquer modelo local, gratuito e privado |
| LM Studio | Local | Interface grafica para modelos locais |
| Personalizado | Qualquer | Endpoint OpenAI-compatible proprio |

---

## Stack tecnica

| Camada | Tecnologia |
|---|---|
| Desktop shell | Electron 29 |
| Frontend | React 18 + Vite 5 |
| Animacoes UI | Framer Motion 11 |
| Estado global | Zustand |
| Drag and drop | @dnd-kit |
| Agente IA | Python 3.14 |
| HTTP (agente) | httpx |
| SDKs de IA | openai, anthropic, google-generativeai, mistralai, cohere, groq, together |
| Processamento de imagem | Pillow, OpenCV |
| Audio | pydub, sounddevice, pyaudio |
| Motor de video | Remotion |

---

## Como instalar

### Pre-requisitos

- Windows 10 ou 11
- Node.js 18 ou superior
- Python 3.14 ou superior
- Git

### Passo a passo

```bash
# 1. Clone o repositorio
git clone https://github.com/Leandrohenri-code/motion-agent.git
cd motion-agent

# 2. Instale as dependencias Node.js
npm install

# 3. Crie e ative o ambiente virtual Python
python -m venv .venv
.venv\Scripts\activate

# 4. Instale as dependencias Python
pip install -r requirements.txt
```

> **Aviso para Windows:** se o `pyaudio` falhar na instalacao, use:
> ```
> pip install pipwin && pipwin install pyaudio
> ```

```bash
# 5. Configure as variaveis de ambiente
cp .env.example .env

# 6. Rode em modo desenvolvimento
npm run dev
```

Isso inicia o servidor Vite na porta 5173 e o Electron em seguida (via `concurrently` + `wait-on`).

### Build para producao

```bash
npm run build:win   # Gera o instalador .exe para Windows
npm run build       # Plataforma atual
```

---

## Comunicacao Electron e Python

O agente Python e iniciado como processo filho pelo Electron. A troca de mensagens acontece por JSON no stdio do processo:

**Electron escreve no stdin do Python (uma linha por mensagem):**
```json
{ "project": {...}, "frames": [...], "script": {...}, "api": {...} }
```

**Python escreve no stdout (uma linha por evento):**
```json
{ "type": "progress", "scene": 2, "total": 5, "status": "gerando", "percent": 40 }
{ "type": "log",      "level": "info",    "message": "Gerando cena 2/5..." }
{ "type": "scene_done","scene": 2,        "code": "import { AbsoluteFill..." }
{ "type": "awaiting_approval", "scene": 2 }
{ "type": "done",     "output_path": "C:/Users/.../output.mp4" }
{ "type": "error",    "message": "...", "retryable": true }
```

No modo passo a passo, o agente pausa apos cada cena e aguarda uma resposta do Electron:

```json
{ "type": "approve_scene" }
{ "type": "reject_scene",  "feedback": "use cores mais vibrantes" }
{ "type": "retry_scene" }
{ "type": "abort" }
```

Quando o usuario rejeita uma cena com feedback, o agente incorpora o texto ao contexto e regenera a cena antes de continuar para a proxima.

---

## Design visual

Interface inspirada em ferramentas como Linear, Raycast, Vercel e Arc Browser. As escolhas principais foram:

- Fundo `#0d0d0f` com superficies em `#1a1a1e` e `#141416`
- Accent principal violeta `#6c63ff` e accent secundario teal `#00d4aa`
- Fonte Geist (fallback system-ui)
- Animacoes via Framer Motion com spring physics
- Componentes proprios: Badge, Spinner, Tooltip, FolderInput, LogTerminal

---

## Estrutura do projeto

```
motion-agent/
├── electron/
│   ├── main.js                  Processo principal do Electron
│   ├── preload.js               Bridge segura para a UI (contextBridge)
│   └── ipc/
│       ├── agent-bridge.js      Spawn do processo Python + roteamento de mensagens
│       ├── file-system.js       Dialogos de arquivo, persistencia de config local
│       └── audio-handler.js     Handlers de audio nativos
├── src/
│   ├── App.jsx                  Componente raiz
│   ├── store/
│   │   └── useAppStore.js       Estado global Zustand (projeto, frames, roteiro, API, agente)
│   ├── components/
│   │   ├── layout/              Sidebar, TabBar, StatusBar
│   │   ├── shared/              Badge, Spinner, Tooltip, FolderInput, LogTerminal, Modal
│   │   └── tabs/                ProjectTab, FramesTab, ScriptTab, ReferenceTab, ApiTab
│   └── styles/                  globals.css, components.css
├── agent/
│   ├── main_agent.py            Orquestrador (ponto de entrada do processo Python)
│   ├── ai_client.py             Cliente universal de IA (suporte a 4 SDKs)
│   ├── provider_registry.py     Registro dos 20+ providers com URLs e configuracoes
│   ├── scene_generator.py       Geracao de componentes Remotion por cena
│   ├── remotion_writer.py       Escrita dos arquivos .tsx no projeto Remotion
│   ├── remotion_controller.py   Renderizacao via CLI do Remotion
│   ├── reference_analyzer.py    Analise visual de referencias com IA de visao
│   ├── coherence_checker.py     Verificacao de coerencia entre cenas
│   ├── audio_processor.py       Transcricao (Whisper) e TTS (OpenAI, ElevenLabs)
│   ├── model_fetcher.py         Listagem dinamica de modelos por provider
│   ├── prompt_builder.py        Construcao de prompts a partir da analise de referencia
│   ├── style_extractor.py       Extracao de caracteristicas de estilo
│   └── utils/
│       ├── json_streamer.py     Funcoes de saida JSON para o Electron
│       ├── image_utils.py       Conversao base64, resize, extracao de cores
│       └── file_utils.py        Utilitarios de leitura e escrita de arquivos
├── requirements.txt
├── package.json
├── vite.config.js
└── electron-builder.yml
```

---

## Nota de seguranca

Este repositorio e uma **versao de portfolio** de um produto comercial ativo. Os seguintes modulos tiveram a implementacao substituida por stubs que preservam as assinaturas dos metodos e a estrutura das classes:

- `agent/main_agent.py` — logica de orquestracao e fluxo de geracao
- `agent/scene_generator.py` — prompts de sistema e logica de parsing do codigo gerado
- `agent/reference_analyzer.py` — prompts de visao e interpretacao da resposta JSON
- `agent/coherence_checker.py` — prompt de verificacao de coerencia entre cenas
- `agent/ai_client.py` — implementacoes das chamadas HTTP/SDK por provider (a arquitetura de dispatch esta visivel)

As API keys nunca ficam em arquivos do projeto. Elas sao armazenadas localmente em `%USERPROFILE%\.motion-agent\.keys.json`, que e gerado em runtime e nunca entra no repositorio.

---

## Demo ao vivo

Em breve.

---

## Licenca

MIT

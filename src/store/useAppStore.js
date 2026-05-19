import { create } from 'zustand';

const DEFAULT_PROJECT = {
  name: '',
  description: '',
  remotionPath: '',
  remotionEntry: '',
  outputPath: '',
  resolution: '1080p',
  fps: 30,
  format: 'mp4-h264',
  stepByStep: true,
  verboseLog: true,
  coherenceCheck: true,
  openFolderOnDone: false,
  remotionDetected: false,
  lockedReferenceMode: false,
};

const DEFAULT_SCRIPT = {
  executionPrompt: '',
  suggestedPrompt: '',
  suggestedAt: null,
  styleChips: {
    rhythm: '',
    tone: '',
    transitions: '',
    typography: '',
  },
  audio: {
    enabled: false,
    mode: 'record',
    recordedBlob: null,
    recordedUrl: null,
    uploadedPath: '',
    ttsText: '',
    ttsProvider: 'openai',
    ttsApiKey: '',
    ttsVoice: '',
    ttsSpeed: 1.0,
    generatedPath: '',
    generatedUrl: null,
  },
};

const DEFAULT_REFERENCE = {
  videoPath: '',
  styleImages: [],
  manualDescription: '',
  analysis: null,
  isAnalyzing: false,
  analyzeStep: '',
  analyzeError: '',
};

const DEFAULT_API = {
  provider: 'openai',
  apiKey: '',
  baseUrl: '',
  selectedModel: '',
  visionModel: '',
  sameModelForVision: true,
  models: [],
  isLoadingModels: false,
  modelError: '',
  temperature: 0.7,
  maxTokens: 4096,
  systemPrompt: '',
  streaming: true,
  timeout: 120,
  advancedOpen: false,
};

const DEFAULT_AGENT = {
  isRunning: false,
  currentScene: 0,
  totalScenes: 0,
  logs: [],
  generatedCode: '',
  awaitingApproval: false,
  awaitingScene: null,
  errors: [],
  status: 'idle',
  outputPath: '',
};

export const useAppStore = create((set, get) => ({
  activeTab: 'project',
  logPanelOpen: true,
  logPanelHeight: 180,
  logActiveTab: 'log',

  project: { ...DEFAULT_PROJECT },
  frames: [],
  script: { ...DEFAULT_SCRIPT },
  reference: { ...DEFAULT_REFERENCE },
  api: { ...DEFAULT_API },
  agent: { ...DEFAULT_AGENT },

  // ── Navigation ──
  setActiveTab: (tab) => set({ activeTab: tab }),
  setLogPanelOpen: (open) => set({ logPanelOpen: open }),
  setLogPanelHeight: (h) => set({ logPanelHeight: h }),
  setLogActiveTab: (tab) => set({ logActiveTab: tab }),

  // ── Project ──
  updateProject: (patch) =>
    set((s) => ({ project: { ...s.project, ...patch } })),

  // ── Frames ──
  addFrames: (newFrames) =>
    set((s) => ({ frames: [...s.frames, ...newFrames] })),

  updateFrame: (id, patch) =>
    set((s) => ({
      frames: s.frames.map((f) => (f.id === id ? { ...f, ...patch } : f)),
    })),

  removeFrame: (id) =>
    set((s) => ({ frames: s.frames.filter((f) => f.id !== id) })),

  clearFrames: () => set({ frames: [] }),

  reorderFrames: (frames) => set({ frames }),

  // ── Script ──
  updateScript: (patch) =>
    set((s) => ({ script: { ...s.script, ...patch } })),

  updateAudio: (patch) =>
    set((s) => ({
      script: { ...s.script, audio: { ...s.script.audio, ...patch } },
    })),

  updateStyleChips: (patch) =>
    set((s) => ({
      script: {
        ...s.script,
        styleChips: { ...s.script.styleChips, ...patch },
      },
    })),

  setSuggestedPrompt: (prompt) =>
    set((s) => ({
      script: { ...s.script, suggestedPrompt: prompt, suggestedAt: new Date().toISOString() },
    })),

  // ── Reference ──
  updateReference: (patch) =>
    set((s) => ({ reference: { ...s.reference, ...patch } })),

  addStyleImage: (img) =>
    set((s) => ({
      reference: { ...s.reference, styleImages: [...s.reference.styleImages, img] },
    })),

  removeStyleImage: (idx) =>
    set((s) => ({
      reference: {
        ...s.reference,
        styleImages: s.reference.styleImages.filter((_, i) => i !== idx),
      },
    })),

  // ── API ──
  updateApi: (patch) =>
    set((s) => ({ api: { ...s.api, ...patch } })),

  setModels: (models) =>
    set((s) => ({ api: { ...s.api, models, isLoadingModels: false, modelError: '' } })),

  // ── Generation ──
  startGeneration: async () => {
    const { project, frames, script, api, updateAgent, addLog } = get();

    const apiKey = await window.electronAPI?.loadApiKey(api.provider).catch(() => null) || api.apiKey;

    const config = {
      project: {
        remotion_path: project.remotionPath,
        output_path: project.outputPath,
        resolution: project.resolution,
        fps: project.fps,
        format: project.format,
        step_by_step: project.stepByStep,
        verbose_log: project.verboseLog,
        coherence_check: project.coherenceCheck,
        open_folder_on_done: project.openFolderOnDone,
        locked_reference_mode: project.lockedReferenceMode,
      },
      frames: frames.map((f) => ({
        id: f.id,
        name: f.name,
        media_type: f.mediaType || 'image',
        preview: f.preview || null,
        description: f.description,
        duration: parseFloat(f.duration) || 3,
      })),
      script: {
        execution_prompt: script.executionPrompt,
        style: script.styleChips,
        audio: {
          enabled: script.audio.enabled,
          uploaded_path: script.audio.uploadedPath || null,
          tts_text: script.audio.ttsText || null,
          tts_provider: script.audio.ttsProvider,
          tts_voice: script.audio.ttsVoice,
        },
      },
      api: {
        provider: api.provider,
        api_key: apiKey,
        base_url: api.baseUrl || null,
        model: api.selectedModel,
        vision_model: api.visionModel || api.selectedModel,
        temperature: api.temperature,
        max_tokens: api.maxTokens,
        system_prompt: api.systemPrompt,
        timeout: api.timeout,
        streaming: api.streaming,
      },
      reference: {
        preview: get().reference?.preview || null,
        manualDescription: get().reference?.manualDescription || '',
        analysis: get().reference?.analysis || '',
      },
    };

    updateAgent({ isRunning: true, status: 'running', currentScene: 0, totalScenes: frames.length, logs: [], errors: [], outputPath: '' });
    addLog({ level: 'info', message: `▶ Iniciando geração — ${frames.length} cena(s) · modelo: ${api.selectedModel || api.provider}` });

    window.electronAPI?.startAgent(config);
  },

  stopGeneration: () => {
    window.electronAPI?.stopAgent();
    get().updateAgent({ isRunning: false, status: 'idle' });
    get().addLog({ level: 'warn', message: '⏹ Geração interrompida pelo usuário' });
  },

  approveScene: (sceneNum) => {
    window.electronAPI?.sendAgentMessage({ type: 'approve_scene', scene: sceneNum });
    get().updateAgent({ awaitingApproval: false, awaitingScene: null, status: 'running' });
    get().addLog({ level: 'success', message: `✅ Cena ${sceneNum} aprovada — continuando...` });
  },

  rejectScene: (sceneNum, feedback) => {
    window.electronAPI?.sendAgentMessage({ type: 'reject_scene', scene: sceneNum, feedback: feedback || '' });
    get().updateAgent({ awaitingApproval: false, awaitingScene: null, status: 'running' });
    get().addLog({ level: 'warn', message: `🔄 Cena ${sceneNum} rejeitada — regenerando${feedback ? ` com feedback: "${feedback}"` : ''}...` });
  },

  retryScene: (sceneNum) => {
    window.electronAPI?.sendAgentMessage({ type: 'retry_scene', scene: sceneNum });
    get().updateAgent({ awaitingApproval: false, awaitingScene: null, status: 'running' });
    get().addLog({ level: 'info', message: `🔄 Cena ${sceneNum} sendo regenerada...` });
  },

  // ── Agent ──
  updateAgent: (patch) =>
    set((s) => ({ agent: { ...s.agent, ...patch } })),

  addLog: (log) =>
    set((s) => ({
      agent: {
        ...s.agent,
        logs: [...s.agent.logs.slice(-499), { ...log, id: Date.now() + Math.random() }],
      },
    })),

  clearLogs: () =>
    set((s) => ({ agent: { ...s.agent, logs: [] } })),

  addError: (err) =>
    set((s) => ({
      agent: { ...s.agent, errors: [...s.agent.errors, err] },
    })),

  clearErrors: () =>
    set((s) => ({ agent: { ...s.agent, errors: [] } })),

  handleAgentMessage: (msg) => {
    const { updateAgent, addLog, addError, updateFrame } = get();
    switch (msg.type) {
      case 'progress':
        updateAgent({
          currentScene: msg.scene,
          totalScenes: msg.total,
          status: 'running',
        });
        addLog({ level: 'info', message: `Cena ${msg.scene}/${msg.total}: ${msg.status}`, scene: msg.scene });
        if (msg.percent !== undefined) updateAgent({ percent: msg.percent });
        break;
      case 'log':
        addLog({ level: msg.level || 'info', message: msg.message, scene: msg.scene });
        break;
      case 'scene_done':
        updateFrame(get().frames[msg.scene - 1]?.id, { status: 'done', generatedCode: msg.code });
        updateAgent({ generatedCode: msg.code });
        addLog({ level: 'success', message: `✅ Cena ${msg.scene} concluída`, scene: msg.scene });
        break;
      case 'awaiting_approval':
        updateAgent({ awaitingApproval: true, awaitingScene: msg.scene, status: 'waiting' });
        addLog({ level: 'info', message: `👁 Aguardando aprovação da cena ${msg.scene}` });
        break;
      case 'done':
        updateAgent({ isRunning: false, status: 'done', outputPath: msg.output_path });
        addLog({ level: 'success', message: `🎬 Vídeo gerado: ${msg.output_path}` });
        break;
      case 'error':
        addError(msg);
        addLog({ level: 'error', message: `❌ Erro na cena ${msg.scene}: ${msg.message}` });
        if (msg.scene) {
          updateFrame(get().frames[msg.scene - 1]?.id, { status: 'error', errorMsg: msg.message });
        }
        break;
      case 'agent_closed':
        updateAgent({ isRunning: false, status: msg.code === 0 ? 'done' : 'idle' });
        break;
      default:
        addLog({ level: 'info', message: JSON.stringify(msg) });
    }
  },

  // ── Persistence ──
  loadFromConfig: (config) => {
    if (!config) return;
    set({
      project: { ...DEFAULT_PROJECT, ...config.project },
      script: { ...DEFAULT_SCRIPT, ...config.script, audio: { ...DEFAULT_SCRIPT.audio, ...(config.script?.audio || {}) } },
      reference: { ...DEFAULT_REFERENCE, ...config.reference },
      api: { ...DEFAULT_API, ...config.api },
    });
  },

  toConfig: () => {
    const { project, script, reference, api } = get();
    return {
      project,
      script: { ...script, audio: { ...script.audio, recordedBlob: null, recordedUrl: null } },
      reference: { ...reference, analysis: reference.analysis },
      api: { ...api, apiKey: '', models: [] },
    };
  },
}));

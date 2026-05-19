import React, { useRef, useState } from 'react';
import { Mic, MicOff, Volume2, ArrowUp, Edit3, Copy, Play, Square, Layers, AlertCircle, CheckCircle, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { FolderInput } from '../shared/FolderInput';
import { Spinner } from '../shared/Spinner';
import { Badge } from '../shared/Badge';

const RHYTHM_OPTS = ['Lento', 'Médio', 'Rápido', 'Dinâmico'];
const TONE_OPTS   = ['Profissional', 'Descontraído', 'Energético', 'Minimalista', 'Luxo'];
const TRANS_OPTS  = ['Suaves', 'Cortadas', 'Com efeito', 'Sem transição'];
const TYPO_OPTS   = ['Bold/Impactante', 'Elegante/Fina', 'Geométrica', 'Manuscrita'];

function AudioTab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 500,
        background: active ? '#1a1a1e' : 'transparent',
        border: active ? '1px solid #22222c' : '1px solid transparent',
        color: active ? '#f0f0f2' : '#8a8a9a',
        cursor: 'pointer', transition: 'all 0.15s ease',
      }}
    >
      {label}
    </button>
  );
}

function ChipGroup({ label, options, selected, onSelect }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <span style={{ fontSize: 11, color: '#8a8a9a', fontWeight: 500 }}>{label}</span>
      <div className="chip-group">
        {options.map((opt) => (
          <button
            key={opt}
            className={`chip${selected === opt ? ' active' : ''}`}
            onClick={() => onSelect(selected === opt ? '' : opt)}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}

// Painel de geração
function GeneratePanel() {
  const { frames, script, api, project, agent, setActiveTab, startGeneration, stopGeneration } = useAppStore();
  const [warnings, setWarnings] = useState([]);

  const totalDuration = frames.reduce((s, f) => s + (parseFloat(f.duration) || 3), 0);

  const handleGenerate = () => {
    const w = [];
    if (!frames.length)                                             w.push({ msg: 'Nenhuma cena carregada', tab: 'frames' });
    if (!script.executionPrompt.trim())                             w.push({ msg: 'Prompt de estilo vazio', tab: null });
    if (!api.apiKey && api.provider !== 'ollama' && api.provider !== 'lmstudio')
                                                                    w.push({ msg: 'API key não configurada', tab: 'api' });
    if (w.length) { setWarnings(w); return; }
    setWarnings([]);
    startGeneration();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>

      {/* Faixa de cenas carregadas */}
      {frames.length > 0 ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: '#1a1a1e', borderRadius: 8, border: '1px solid #22222c' }}>
          <Layers size={12} style={{ color: '#6c63ff', flexShrink: 0 }} />
          <div style={{ display: 'flex', gap: 3, flex: 1, overflowX: 'auto' }}>
            {frames.slice(0, 14).map((f, i) => (
              <div key={f.id} style={{ position: 'relative', flexShrink: 0 }}>
                {f.preview
                  ? <img src={f.preview} alt="" style={{ width: 36, height: 24, objectFit: 'cover', borderRadius: 3, border: '1px solid #22222c', display: 'block' }} />
                  : <div style={{ width: 36, height: 24, borderRadius: 3, background: '#22222c', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><span style={{ fontSize: 8, color: '#44444e' }}>{i+1}</span></div>
                }
              </div>
            ))}
            {frames.length > 14 && (
              <div style={{ width: 36, height: 24, borderRadius: 3, background: '#22222c', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <span style={{ fontSize: 8, color: '#8a8a9a' }}>+{frames.length - 14}</span>
              </div>
            )}
          </div>
          <span style={{ fontSize: 11, color: '#8a8a9a', flexShrink: 0, whiteSpace: 'nowrap' }}>
            {frames.length} cena{frames.length > 1 ? 's' : ''} · {totalDuration.toFixed(1)}s
          </span>
          <button onClick={() => setActiveTab('frames')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#44444e', display: 'flex', padding: 2 }}>
            <ChevronRight size={13} />
          </button>
        </div>
      ) : (
        <button
          onClick={() => setActiveTab('frames')}
          style={{ padding: '10px 16px', background: '#1a1a1e', border: '1px dashed #44444e', borderRadius: 8, cursor: 'pointer', color: '#8a8a9a', fontSize: 12, display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
        >
          <Layers size={14} style={{ color: '#44444e' }} />
          Nenhuma cena carregada — clique para ir à aba Frames
          <ChevronRight size={13} style={{ marginLeft: 'auto', color: '#44444e' }} />
        </button>
      )}

      {/* Avisos de validação (só aparecem ao tentar gerar) */}
      {warnings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {warnings.map((w, i) => (
            <div
              key={i}
              onClick={w.tab ? () => { setActiveTab(w.tab); setWarnings([]); } : undefined}
              style={{ padding: '7px 12px', background: '#ff4d6d10', border: '1px solid #ff4d6d30', borderRadius: 7, fontSize: 12, color: '#ff4d6d', display: 'flex', alignItems: 'center', gap: 8, cursor: w.tab ? 'pointer' : 'default' }}
            >
              <AlertCircle size={13} />
              {w.msg}
              {w.tab && <span style={{ marginLeft: 'auto', fontSize: 11, color: '#ff4d6d90' }}>Corrigir →</span>}
            </div>
          ))}
        </div>
      )}

      {/* Barra de progresso */}
      {agent.isRunning && agent.totalScenes > 0 && (
        <div style={{ padding: '10px 14px', background: '#1a1a1e', borderRadius: 8, border: '1px solid #6c63ff30' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 11, color: '#8a8a9a' }}>
            <span style={{ animation: 'dotPulse 1.5s ease infinite', color: '#6c63ff' }}>● Gerando cena {agent.currentScene} de {agent.totalScenes}...</span>
            <span>{Math.round((agent.currentScene / agent.totalScenes) * 100)}%</span>
          </div>
          <div style={{ height: 5, background: '#22222c', borderRadius: 99 }}>
            <div style={{
              height: '100%', borderRadius: 99,
              background: 'linear-gradient(90deg, #6c63ff, #00d4aa)',
              width: `${(agent.currentScene / agent.totalScenes) * 100}%`,
              transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      )}

      {/* Botão principal */}
      {!agent.isRunning ? (
        <button
          onClick={handleGenerate}
          style={{
            width: '100%', padding: '14px 20px',
            borderRadius: 10, border: 'none', cursor: 'pointer',
            background: 'linear-gradient(135deg, #6c63ff, #00d4aa)',
            boxShadow: '0 4px 24px #6c63ff50',
            color: '#fff', fontSize: 15, fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 6px 32px #6c63ff70'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 4px 24px #6c63ff50'; e.currentTarget.style.transform = 'none'; }}
        >
          <Play size={18} fill="#fff" />
          Enviar para o Remotion e gerar vídeo
        </button>
      ) : (
        <button
          onClick={stopGeneration}
          style={{ width: '100%', padding: '14px 20px', borderRadius: 10, border: 'none', cursor: 'pointer', background: '#ff4d6d', color: '#fff', fontSize: 15, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}
        >
          <Square size={16} fill="#fff" />
          Parar geração
        </button>
      )}

      {/* Vídeo pronto */}
      {agent.status === 'done' && agent.outputPath && (
        <div style={{ padding: '10px 14px', background: '#00d4aa10', border: '1px solid #00d4aa30', borderRadius: 8, fontSize: 12, color: '#00d4aa', display: 'flex', alignItems: 'center', gap: 8 }}>
          <CheckCircle size={14} />
          <span style={{ flex: 1 }}>Vídeo gerado com sucesso!</span>
          <span style={{ fontFamily: 'monospace', fontSize: 10, color: '#8a8a9a' }}>{agent.outputPath}</span>
        </div>
      )}
    </div>
  );
}

// Botão de enviar prompt (reusa a lógica do GeneratePanel via ref compartilhado)
function PromptSendButton({ sendRef }) {
  const { frames, script, api, agent, startGeneration } = useAppStore();
  const [warn, setWarn] = useState('');

  const handleClick = () => {
    if (agent.isRunning) return;
    if (!frames.length)              { setWarn('Adicione cenas na aba Frames primeiro'); return; }
    if (!script.executionPrompt.trim()) { setWarn('Escreva o prompt acima antes de enviar'); return; }
    if (!api.apiKey && api.provider !== 'ollama' && api.provider !== 'lmstudio')
                                     { setWarn('Configure a API key na aba API'); return; }
    setWarn('');
    startGeneration();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {warn && (
        <div style={{ fontSize: 12, color: '#ff4d6d', display: 'flex', alignItems: 'center', gap: 6 }}>
          <AlertCircle size={12} /> {warn}
        </div>
      )}
      <button
        ref={sendRef}
        onClick={handleClick}
        disabled={agent.isRunning}
        style={{
          width: '100%', padding: '13px 20px',
          borderRadius: 10, border: 'none',
          cursor: agent.isRunning ? 'not-allowed' : 'pointer',
          background: agent.isRunning
            ? '#22222c'
            : 'linear-gradient(135deg, #6c63ff, #00d4aa)',
          boxShadow: agent.isRunning ? 'none' : '0 4px 24px #6c63ff50',
          color: agent.isRunning ? '#44444e' : '#fff',
          fontSize: 15, fontWeight: 700,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={(e) => {
          if (!agent.isRunning) {
            e.currentTarget.style.boxShadow = '0 6px 32px #6c63ff70';
            e.currentTarget.style.transform = 'translateY(-1px)';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = agent.isRunning ? 'none' : '0 4px 24px #6c63ff50';
          e.currentTarget.style.transform = 'none';
        }}
      >
        {agent.isRunning ? (
          <><Spinner size={16} /> Gerando cena {agent.currentScene} de {agent.totalScenes}...</>
        ) : (
          <><Play size={17} fill="#fff" /> Gerar vídeo no Remotion</>
        )}
      </button>
    </div>
  );
}

export function ScriptTab() {
  const { script, updateScript, updateAudio, updateStyleChips } = useAppStore();
  const { audio, suggestedPrompt, suggestedAt, executionPrompt, styleChips } = script;

  const [audioTab, setAudioTab] = useState('record');
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const chunksRef = useRef([]);
  const promptRef = useRef(null);
  const promptSendRef = useRef(null);

  const useSuggested = () => {
    updateScript({ executionPrompt: suggestedPrompt });
    if (promptRef.current) promptRef.current.focus();
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const mr = new MediaRecorder(stream);
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        updateAudio({ recordedBlob: blob, recordedUrl: url });
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      setMediaRecorder(mr);
      setIsRecording(true);
    } catch {}
  };

  const stopRecording = () => {
    mediaRecorder?.stop();
    setIsRecording(false);
    setMediaRecorder(null);
  };

  const buildStyleSuffix = () => {
    const parts = [];
    if (styleChips.rhythm)      parts.push(`Ritmo: ${styleChips.rhythm}`);
    if (styleChips.tone)        parts.push(`Tom: ${styleChips.tone}`);
    if (styleChips.transitions) parts.push(`Transições: ${styleChips.transitions}`);
    if (styleChips.typography)  parts.push(`Tipografia: ${styleChips.typography}`);
    return parts.join(' · ');
  };

  return (
    <div className="tab-content">

      {/* ── Painel de geração — sempre visível no topo ── */}
      <GeneratePanel />

      {/* ── Prompt de execução ── */}
      <div className="section" style={{ marginTop: 4 }}>
        <div className="section-title">Prompt de estilo</div>
        <div className="card" style={{ border: '1px solid #22222c' }}>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ position: 'relative' }}>
              <textarea
                ref={promptRef}
                className="input"
                style={{ minHeight: 140, resize: 'vertical', lineHeight: 1.6, paddingBottom: 36 }}
                placeholder="Descreva o estilo do vídeo: animações, tipografia, cores, ritmo, transições, personalidade visual...&#10;&#10;Ctrl+Enter para gerar"
                value={executionPrompt}
                onChange={(e) => updateScript({ executionPrompt: e.target.value })}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    promptSendRef.current?.click();
                  }
                }}
              />
              <span style={{
                position: 'absolute', bottom: 10, left: 12,
                fontSize: 10, color: '#44444e', pointerEvents: 'none',
              }}>
                Ctrl+Enter para gerar
              </span>
              <span style={{
                position: 'absolute', bottom: 10, right: 10,
                fontSize: 11, color: '#44444e', pointerEvents: 'none',
              }}>
                {executionPrompt.length} chars
              </span>
            </div>

            {(styleChips.rhythm || styleChips.tone || styleChips.transitions || styleChips.typography) && (
              <div style={{ padding: '6px 10px', background: '#1a1a1e', borderRadius: 6, fontSize: 11, color: '#8a8a9a' }}>
                <span style={{ color: '#44444e' }}>Chips aplicados: </span>{buildStyleSuffix()}
              </div>
            )}

            {suggestedPrompt && (
              <button className="btn btn-secondary btn-sm" onClick={useSuggested} style={{ alignSelf: 'flex-start' }}>
                <ArrowUp size={12} /> Usar sugestão da análise de referência
              </button>
            )}

            {/* Botão de enviar logo abaixo do prompt */}
            <PromptSendButton sendRef={promptSendRef} />
          </div>
        </div>
      </div>

      {/* ── Estilo rápido ── */}
      <div className="card">
        <div className="card-header"><span className="card-title">Estilo rápido</span></div>
        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <ChipGroup label="Ritmo"      options={RHYTHM_OPTS} selected={styleChips.rhythm}      onSelect={(v) => updateStyleChips({ rhythm: v })} />
          <ChipGroup label="Tom"        options={TONE_OPTS}   selected={styleChips.tone}        onSelect={(v) => updateStyleChips({ tone: v })} />
          <ChipGroup label="Transições" options={TRANS_OPTS}  selected={styleChips.transitions} onSelect={(v) => updateStyleChips({ transitions: v })} />
          <ChipGroup label="Tipografia" options={TYPO_OPTS}   selected={styleChips.typography}  onSelect={(v) => updateStyleChips({ typography: v })} />
        </div>
      </div>

      {/* ── Áudio ── */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Áudio</span>
          <label className="toggle" style={{ marginLeft: 'auto' }}>
            <input type="checkbox" checked={audio.enabled} onChange={(e) => updateAudio({ enabled: e.target.checked })} />
            <span className="toggle-track" />
          </label>
        </div>

        {audio.enabled && (
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', gap: 4, background: '#0d0d0f', borderRadius: 8, padding: 3 }}>
              {['record', 'upload', 'tts'].map((t) => (
                <AudioTab
                  key={t}
                  label={t === 'record' ? 'Gravar voz' : t === 'upload' ? 'Upload de arquivo' : 'Texto para fala (TTS)'}
                  active={audioTab === t}
                  onClick={() => setAudioTab(t)}
                />
              ))}
            </div>

            {audioTab === 'record' && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, padding: '8px 0' }}>
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  style={{
                    width: 64, height: 64, borderRadius: '50%',
                    background: isRecording ? '#ff4d6d' : '#6c63ff',
                    border: 'none', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', transition: 'all 0.15s ease',
                    animation: isRecording ? 'dotPulse 1.5s ease infinite' : undefined,
                    boxShadow: isRecording ? '0 0 20px #ff4d6d60' : '0 0 16px #6c63ff40',
                  }}
                >
                  {isRecording ? <MicOff size={22} /> : <Mic size={22} />}
                </button>
                <span style={{ fontSize: 12, color: isRecording ? '#ff4d6d' : '#8a8a9a' }}>
                  {isRecording ? 'Gravando... clique para parar' : audio.recordedUrl ? 'Gravação pronta — clique para regravar' : 'Clique para gravar'}
                </span>
                {audio.recordedUrl && (
                  <div style={{ width: '100%' }}>
                    <audio controls src={audio.recordedUrl} style={{ width: '100%', height: 32 }} />
                    <button className="btn btn-secondary btn-sm" style={{ marginTop: 8 }} onClick={() => updateAudio({ recordedBlob: null, recordedUrl: null })}>
                      Regravar
                    </button>
                  </div>
                )}
              </div>
            )}

            {audioTab === 'upload' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <FolderInput
                  label="Arquivo de áudio"
                  value={audio.uploadedPath}
                  onChange={(v) => updateAudio({ uploadedPath: v })}
                  type="file"
                  accept={['mp3', 'wav', 'm4a', 'ogg', 'flac']}
                />
                {audio.uploadedPath && (
                  <audio controls src={`file://${audio.uploadedPath}`} style={{ width: '100%', height: 32 }} />
                )}
              </div>
            )}

            {audioTab === 'tts' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="input-group">
                  <label className="input-label">Texto para narração</label>
                  <textarea className="input" style={{ minHeight: 80 }} value={audio.ttsText} onChange={(e) => updateAudio({ ttsText: e.target.value })} placeholder="Digite o texto que será narrado..." />
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">Provedor TTS</label>
                    <select className="select" value={audio.ttsProvider} onChange={(e) => updateAudio({ ttsProvider: e.target.value })}>
                      <option value="openai">OpenAI TTS</option>
                      <option value="elevenlabs">ElevenLabs</option>
                      <option value="google">Google TTS</option>
                      <option value="azure">Azure TTS</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">API Key do provedor</label>
                    <input className="input" type="password" value={audio.ttsApiKey} onChange={(e) => updateAudio({ ttsApiKey: e.target.value })} placeholder="sk-..." />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Voz</label>
                    <select className="select" value={audio.ttsVoice} onChange={(e) => updateAudio({ ttsVoice: e.target.value })}>
                      {['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'].map((v) => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Velocidade: {audio.ttsSpeed}×</label>
                    <input type="range" min="0.5" max="2" step="0.1" value={audio.ttsSpeed} onChange={(e) => updateAudio({ ttsSpeed: parseFloat(e.target.value) })} style={{ width: '100%', accentColor: '#6c63ff' }} />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-secondary btn-sm"><Volume2 size={13} /> Gerar preview</button>
                  <button className="btn btn-primary btn-sm">Usar esta narração</button>
                </div>
                {audio.generatedUrl && (
                  <audio controls src={audio.generatedUrl} style={{ width: '100%', height: 32 }} />
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Sugestão de referência ── */}
      {suggestedPrompt && (
        <>
          <div className="divider-label">💡 Sugestão gerada pela análise de referência</div>
          <div className="card" style={{ borderColor: '#6c63ff40' }}>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                <Badge variant="accent">Gerado pela IA</Badge>
                {suggestedAt && (
                  <span style={{ fontSize: 11, color: '#44444e' }}>
                    {new Date(suggestedAt).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>
              <div style={{ background: '#0d0d0f', borderRadius: 8, padding: 12, fontSize: 13, color: '#c0c0d0', lineHeight: 1.7, border: '1px solid #1a1a1e', maxHeight: 180, overflowY: 'auto' }}>
                {suggestedPrompt}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={useSuggested}>
                  <ArrowUp size={12} /> Usar este prompt
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => { updateScript({ executionPrompt: suggestedPrompt }); if (promptRef.current) promptRef.current.focus(); }}>
                  <Edit3 size={12} /> Editar e usar
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => navigator.clipboard.writeText(suggestedPrompt)}>
                  <Copy size={12} /> Copiar
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

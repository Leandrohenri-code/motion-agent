import React, { useRef, useState, useEffect } from 'react';
import { Mic, MicOff, Upload, Volume2, ArrowUp, Edit3, Copy } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { FolderInput } from '../shared/FolderInput';
import { Spinner } from '../shared/Spinner';
import { Badge } from '../shared/Badge';

const RHYTHM_OPTS   = ['Lento', 'Médio', 'Rápido', 'Dinâmico'];
const TONE_OPTS     = ['Profissional', 'Descontraído', 'Energético', 'Minimalista', 'Luxo'];
const TRANS_OPTS    = ['Suaves', 'Cortadas', 'Com efeito', 'Sem transição'];
const TYPO_OPTS     = ['Bold/Impactante', 'Elegante/Fina', 'Geométrica', 'Manuscrita'];

function AudioTab({ label, children, active, onClick }) {
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

export function ScriptTab() {
  const { script, updateScript, updateAudio, updateStyleChips } = useAppStore();
  const { audio, suggestedPrompt, suggestedAt, executionPrompt, styleChips } = script;

  const [audioTab, setAudioTab] = useState('record');
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordedChunks, setRecordedChunks] = useState([]);
  const chunksRef = useRef([]);
  const promptRef = useRef(null);

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
      {/* SECTION A — Execution Prompt */}
      <div className="section">
        <div className="section-title">Prompt de execução</div>

        <div className="card">
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ position: 'relative' }}>
              <textarea
                ref={promptRef}
                className="input"
                style={{ minHeight: 160, resize: 'vertical', lineHeight: 1.6 }}
                placeholder="Descreva como você quer que o vídeo seja feito. Estilo de animação, personalidade, ritmo, tipografia, cores, transições entre cenas..."
                value={executionPrompt}
                onChange={(e) => updateScript({ executionPrompt: e.target.value })}
              />
              <span style={{
                position: 'absolute', bottom: 10, right: 10,
                fontSize: 11, color: '#44444e', pointerEvents: 'none',
              }}>
                {executionPrompt.length} chars
              </span>
            </div>

            {styleChips.rhythm || styleChips.tone || styleChips.transitions || styleChips.typography ? (
              <div style={{
                padding: '6px 10px', background: '#1a1a1e', borderRadius: 6,
                fontSize: 11, color: '#8a8a9a',
              }}>
                <span style={{ color: '#44444e' }}>Estilo aplicado: </span>
                {buildStyleSuffix()}
              </div>
            ) : null}

            {suggestedPrompt && (
              <button className="btn btn-secondary btn-sm" onClick={useSuggested} style={{ alignSelf: 'flex-start' }}>
                <ArrowUp size={12} /> Usar sugestão gerada
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Estilo rápido */}
      <div className="card">
        <div className="card-header"><span className="card-title">Estilo rápido</span></div>
        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <ChipGroup label="Ritmo"       options={RHYTHM_OPTS}  selected={styleChips.rhythm}      onSelect={(v) => updateStyleChips({ rhythm: v })} />
          <ChipGroup label="Tom"         options={TONE_OPTS}    selected={styleChips.tone}        onSelect={(v) => updateStyleChips({ tone: v })} />
          <ChipGroup label="Transições"  options={TRANS_OPTS}   selected={styleChips.transitions} onSelect={(v) => updateStyleChips({ transitions: v })} />
          <ChipGroup label="Tipografia"  options={TYPO_OPTS}    selected={styleChips.typography}  onSelect={(v) => updateStyleChips({ typography: v })} />
        </div>
      </div>

      {/* Audio section */}
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
            {/* Audio sub-tabs */}
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
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => updateAudio({ recordedBlob: null, recordedUrl: null })}>
                        Regravar
                      </button>
                    </div>
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
                      <option value="alloy">Alloy</option>
                      <option value="echo">Echo</option>
                      <option value="fable">Fable</option>
                      <option value="onyx">Onyx</option>
                      <option value="nova">Nova</option>
                      <option value="shimmer">Shimmer</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Velocidade: {audio.ttsSpeed}×</label>
                    <input type="range" min="0.5" max="2" step="0.1" value={audio.ttsSpeed} onChange={(e) => updateAudio({ ttsSpeed: parseFloat(e.target.value) })} style={{ width: '100%', accentColor: '#6c63ff' }} />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-secondary btn-sm">
                    <Volume2 size={13} /> Gerar preview
                  </button>
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

      {/* SECTION B — Suggested Prompt */}
      <div className="divider-label">💡 Sugestão gerada pela análise de referência</div>

      <div className="card" style={{ borderColor: suggestedPrompt ? '#6c63ff40' : '#22222c' }}>
        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {!suggestedPrompt ? (
            <div style={{ textAlign: 'center', padding: '20px 0', color: '#44444e', fontSize: 13 }}>
              Vá até a aba <strong style={{ color: '#8a8a9a' }}>Referência</strong> e clique em "Analisar" para gerar uma sugestão de prompt baseada no seu vídeo de referência.
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                <Badge variant="accent">Gerado pela IA</Badge>
                {suggestedAt && (
                  <span style={{ fontSize: 11, color: '#44444e' }}>
                    {new Date(suggestedAt).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>
              <div style={{
                background: '#0d0d0f', borderRadius: 8, padding: 12,
                fontSize: 13, color: '#c0c0d0', lineHeight: 1.7,
                border: '1px solid #1a1a1e',
                maxHeight: 180, overflowY: 'auto',
              }}>
                {suggestedPrompt}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={useSuggested}>
                  <ArrowUp size={12} /> Usar este prompt
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => {
                  updateScript({ executionPrompt: suggestedPrompt });
                  if (promptRef.current) promptRef.current.focus();
                }}>
                  <Edit3 size={12} /> Editar e usar
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => navigator.clipboard.writeText(suggestedPrompt)}>
                  <Copy size={12} /> Copiar
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useRef, useState } from 'react';
import { Search, ArrowUp, Copy, RefreshCw, X, Upload } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { FolderInput } from '../shared/FolderInput';
import { Badge } from '../shared/Badge';
import { Spinner } from '../shared/Spinner';

const ANALYZE_STEPS = [
  'Extraindo frames do vídeo...',
  'Analisando paleta de cores...',
  'Detectando tipografia...',
  'Analisando timing e ritmo...',
  'Gerando prompt otimizado...',
];

export function ReferenceTab() {
  const { reference, updateReference, addStyleImage, removeStyleImage, setSuggestedPrompt, api, setActiveTab } = useAppStore();
  const [analyzeStep, setAnalyzeStep] = useState(0);
  const [videoDragOver, setVideoDragOver] = useState(false);
  const imgInputRef = useRef(null);

  const hasInput = reference.videoPath || reference.styleImages.length > 0 || reference.manualDescription.trim();

  const handleVideoDrop = (e) => {
    e.preventDefault();
    setVideoDragOver(false);
    const file = Array.from(e.dataTransfer.files).find((f) => f.type.startsWith('video/') || f.name.match(/\.(mp4|mov|avi|webm)$/i));
    if (file) updateReference({ videoPath: file.path || file.name });
  };

  const handleStyleImagesDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith('image/'));
    files.forEach((file) => {
      const url = URL.createObjectURL(file);
      addStyleImage({ name: file.name, url, file });
    });
  };

  const handleStyleImagesInput = (e) => {
    Array.from(e.target.files || []).forEach((file) => {
      const url = URL.createObjectURL(file);
      addStyleImage({ name: file.name, url, file });
    });
    e.target.value = '';
  };

  const handleAnalyze = async () => {
    updateReference({ isAnalyzing: true, analyzeError: '' });
    const apiKey = await window.electronAPI?.loadApiKey(api.provider).catch(() => null) || api.apiKey;

    // Step animation
    for (let i = 0; i < ANALYZE_STEPS.length; i++) {
      setAnalyzeStep(i);
      await new Promise((r) => setTimeout(r, 700 + Math.random() * 300));
    }

    const ANALYSIS_INSTRUCTION = `Analise as informações de referência fornecidas (descrição e/ou imagens de mood board). Gere:
1. Características detectadas: estilo, tipografia, ritmo, transições, fundo, mood
2. Paleta de 6 cores dominantes em hexadecimal
3. Prompt detalhado em português para guiar a criação de um vídeo motion graphics com esse estilo

Responda SOMENTE em JSON válido com este formato exato:
{
  "characteristics": { "style": "...", "typography": "...", "rhythm": "...", "transitions": "...", "background": "...", "mood": "..." },
  "palette": ["#hex1","#hex2","#hex3","#hex4","#hex5","#hex6"],
  "prompt": "prompt detalhado aqui..."
}`;

    // Monta partes de conteúdo
    const textParts = [];
    if (reference.videoPath) {
      textParts.push(`Vídeo de referência: ${reference.videoPath}`);
    }
    if (reference.manualDescription) {
      textParts.push(`Descrição manual do estilo: ${reference.manualDescription}`);
    }
    textParts.push(ANALYSIS_INSTRUCTION);

    // Converte imagens de estilo para base64
    const imageBase64List = [];
    for (const img of reference.styleImages.slice(0, 5)) {
      if (img.file) {
        try {
          const b64 = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(img.file);
          });
          imageBase64List.push(b64);
        } catch { /* pula imagem com erro */ }
      } else if (img.url) {
        imageBase64List.push(img.url);
      }
    }

    try {
      let analysisText = '';

      if (api.provider === 'anthropic') {
        // ── Anthropic SDK format ──
        const contentBlocks = [];
        for (const b64 of imageBase64List) {
          const mediaType = b64.startsWith('data:image/png') ? 'image/png' : 'image/jpeg';
          const data = b64.split(',')[1];
          contentBlocks.push({ type: 'image', source: { type: 'base64', media_type: mediaType, data } });
        }
        contentBlocks.push({ type: 'text', text: textParts.join('\n\n') });

        const res = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01',
          },
          body: JSON.stringify({
            model: api.visionModel || api.selectedModel || 'claude-3-5-haiku-20241022',
            max_tokens: 1500,
            messages: [{ role: 'user', content: contentBlocks }],
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error?.message || `Erro ${res.status}`);
        }
        const data = await res.json();
        analysisText = data.content?.[0]?.text || '';

      } else if (api.provider === 'google') {
        // ── Google Gemini format ──
        const parts = [];
        for (const b64 of imageBase64List) {
          const mimeType = b64.startsWith('data:image/png') ? 'image/png' : 'image/jpeg';
          const data = b64.split(',')[1];
          parts.push({ inlineData: { mimeType, data } });
        }
        parts.push({ text: textParts.join('\n\n') });

        const model = api.visionModel || api.selectedModel || 'gemini-1.5-flash';
        const res = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contents: [{ parts }] }),
          }
        );
        if (!res.ok) throw new Error(`Erro ${res.status}`);
        const data = await res.json();
        analysisText = data.candidates?.[0]?.content?.parts?.[0]?.text || '';

      } else {
        // ── OpenAI-compatible format (OpenAI, Groq, Together, OpenRouter, etc.) ──
        const PROVIDER_URLS = {
          openai:     'https://api.openai.com/v1',
          groq:       'https://api.groq.com/openai/v1',
          together:   'https://api.together.ai/v1',
          openrouter: 'https://openrouter.ai/api/v1',
          mistral:    'https://api.mistral.ai/v1',
          deepseek:   'https://api.deepseek.com/v1',
          xai:        'https://api.x.ai/v1',
          fireworks:  'https://api.fireworks.ai/inference/v1',
          anyscale:   'https://api.endpoints.anyscale.com/v1',
          perplexity: 'https://api.perplexity.ai',
          ollama:     api.baseUrl || 'http://localhost:11434/v1',
          lmstudio:   api.baseUrl || 'http://localhost:1234/v1',
        };
        const baseUrl = api.baseUrl || PROVIDER_URLS[api.provider] || `https://api.${api.provider}.com/v1`;

        const contentParts = [];
        for (const b64 of imageBase64List) {
          contentParts.push({ type: 'image_url', image_url: { url: b64 } });
        }
        contentParts.push({ type: 'text', text: textParts.join('\n\n') });

        const body = {
          model: api.visionModel || api.selectedModel || 'gpt-4o-mini',
          messages: [{ role: 'user', content: contentParts.length === 1 ? textParts.join('\n\n') : contentParts }],
          max_tokens: 1500,
        };
        // json_object só para OpenAI/Groq que suportam
        if (['openai', 'groq'].includes(api.provider)) {
          body.response_format = { type: 'json_object' };
        }

        const res = await fetch(`${baseUrl}/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error?.message || `Erro ${res.status} — verifique sua API key`);
        }
        const data = await res.json();
        analysisText = data.choices?.[0]?.message?.content || '';
      }

      // Extrai JSON da resposta (tolera markdown code block)
      const jsonMatch = analysisText.match(/```(?:json)?\s*([\s\S]*?)```/) || [null, analysisText];
      const jsonText = (jsonMatch[1] || analysisText).trim();
      const analysis = JSON.parse(jsonText);

      if (!analysis.prompt) throw new Error('Resposta sem campo "prompt"');

      updateReference({ analysis, isAnalyzing: false, analyzeError: '' });
      setSuggestedPrompt(analysis.prompt);

    } catch (err) {
      const errorMsg = err.message || 'Erro desconhecido';
      // Se não há chave configurada ou a análise falha, usa fallback descritivo baseado no texto manual
      if (reference.manualDescription || reference.videoPath) {
        const desc = reference.manualDescription || 'estilo moderno e profissional';
        const fallback = {
          characteristics: {
            style: 'Moderno e profissional',
            typography: 'Sans-serif, clean e bold',
            rhythm: 'Médio (cortes ~2-3s)',
            transitions: 'Fade suave + deslize',
            background: 'Sólido escuro ou gradiente',
            mood: 'Profissional e sofisticado',
          },
          palette: ['#6c63ff', '#00d4aa', '#1a1a1e', '#f0f0f2', '#ff4d6d', '#ffb340'],
          prompt: `Crie um vídeo motion graphics com o seguinte estilo: ${desc}. Use tipografia clean e bold com animações de entrada suaves. Aplique transições em fade com deslizes sutis. Mantenha ritmo médio com cortes a cada 2-3 segundos.`,
        };
        updateReference({ analysis: fallback, isAnalyzing: false, analyzeError: `Análise via IA falhou (${errorMsg}) — prompt gerado com base na descrição manual.` });
        setSuggestedPrompt(fallback.prompt);
      } else {
        updateReference({ isAnalyzing: false, analyzeError: `Erro: ${errorMsg}` });
      }
    }
  };

  const sendToScript = () => {
    if (reference.analysis?.prompt) {
      setSuggestedPrompt(reference.analysis.prompt);
      setActiveTab('script');
    }
  };

  return (
    <div className="tab-content">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, height: '100%' }}>
        {/* LEFT COLUMN — Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Video reference */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Vídeo de referência</span>
              <Badge variant="neutral">opcional</Badge>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {!reference.videoPath ? (
                <div
                  className={`drop-zone${videoDragOver ? ' drag-over' : ''}`}
                  style={{ padding: 24 }}
                  onDragOver={(e) => { e.preventDefault(); setVideoDragOver(true); }}
                  onDragLeave={() => setVideoDragOver(false)}
                  onDrop={handleVideoDrop}
                >
                  <span style={{ fontSize: 22 }}>🎬</span>
                  <span style={{ fontSize: 13, color: '#8a8a9a' }}>Arraste um vídeo aqui</span>
                  <span style={{ fontSize: 11, color: '#44444e' }}>MP4, MOV, AVI, WEBM</span>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ flex: 1, fontSize: 12, color: '#8a8a9a' }} className="truncate">{reference.videoPath}</span>
                  <button className="btn btn-danger btn-sm btn-icon" onClick={() => updateReference({ videoPath: '' })}>
                    <X size={13} />
                  </button>
                </div>
              )}
              <FolderInput
                value={reference.videoPath}
                onChange={(v) => updateReference({ videoPath: v })}
                type="file"
                accept={['mp4', 'mov', 'avi', 'webm']}
                placeholder="Ou selecione o caminho do arquivo..."
              />
              <p style={{ fontSize: 11, color: '#44444e', lineHeight: 1.6 }}>
                O agente analisará o estilo visual, timing, tipografia e paleta do vídeo para guiar a criação.
              </p>
            </div>
          </div>

          {/* Style images */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Referências de estilo visual</span>
              <Badge variant="neutral">opcional · até 10</Badge>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div
                className="drop-zone"
                style={{ padding: 16, minHeight: 70 }}
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleStyleImagesDrop}
                onClick={() => imgInputRef.current?.click()}
              >
                <Upload size={18} style={{ color: '#44444e' }} />
                <span style={{ fontSize: 12, color: '#8a8a9a' }}>Arraste imagens de mood board</span>
                <input ref={imgInputRef} type="file" multiple accept="image/*" style={{ display: 'none' }} onChange={handleStyleImagesInput} />
              </div>
              {reference.styleImages.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {reference.styleImages.map((img, i) => (
                    <div key={i} style={{ position: 'relative', width: 56, height: 56 }}>
                      <img src={img.url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 6, border: '1px solid #22222c' }} />
                      <button
                        onClick={() => removeStyleImage(i)}
                        style={{
                          position: 'absolute', top: -4, right: -4,
                          background: '#ff4d6d', border: 'none', borderRadius: '50%',
                          width: 16, height: 16, cursor: 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: '#fff',
                        }}
                      >
                        <X size={9} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Manual description */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Descritivo manual</span>
              <Badge variant="neutral">opcional</Badge>
            </div>
            <div className="card-body">
              <textarea
                className="input"
                style={{ minHeight: 80 }}
                placeholder="Ex: minimalista como Apple, cores terrosas, fonte bold, muito espaço em branco..."
                value={reference.manualDescription}
                onChange={(e) => updateReference({ manualDescription: e.target.value })}
              />
            </div>
          </div>

          {/* Analyze button */}
          <button
            className="btn btn-primary btn-large"
            style={{ width: '100%' }}
            disabled={!hasInput || reference.isAnalyzing}
            onClick={handleAnalyze}
          >
            {reference.isAnalyzing ? (
              <><Spinner size={15} color="#fff" /> {ANALYZE_STEPS[analyzeStep]}</>
            ) : (
              <><Search size={16} /> Analisar referências</>
            )}
          </button>

          {reference.analyzeError && (
            <div style={{ padding: '8px 12px', background: '#ffb34010', borderRadius: 8, border: '1px solid #ffb34030', fontSize: 11, color: '#ffb340', lineHeight: 1.5 }}>
              ⚠️ {reference.analyzeError}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN — Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {!reference.analysis ? (
            <div style={{
              flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              color: '#44444e', gap: 12, textAlign: 'center',
            }}>
              <span style={{ fontSize: 40 }}>🔍</span>
              <p style={{ fontSize: 13, lineHeight: 1.6, maxWidth: 260 }}>
                Adicione um vídeo, imagens de referência ou uma descrição manual e clique em <strong style={{ color: '#8a8a9a' }}>Analisar referências</strong> para ver os resultados aqui.
              </p>
            </div>
          ) : (
            <>
              {/* Palette */}
              <div className="card">
                <div className="card-header"><span className="card-title">Paleta extraída</span></div>
                <div className="card-body">
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                    {(reference.analysis.palette || []).map((color, i) => (
                      <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                        <div style={{
                          width: 40, height: 40, borderRadius: '50%', background: color,
                          border: '2px solid #22222c', cursor: 'pointer',
                        }} title={color} onClick={() => navigator.clipboard.writeText(color)} />
                        <span style={{ fontSize: 10, color: '#8a8a9a', fontFamily: 'monospace' }}>{color}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Characteristics */}
              <div className="card">
                <div className="card-header"><span className="card-title">Características detectadas</span></div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {Object.entries(reference.analysis.characteristics || {}).map(([key, val]) => (
                    <div key={key} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                      <span style={{ fontSize: 11, color: '#44444e', width: 90, flexShrink: 0, textTransform: 'capitalize', paddingTop: 1 }}>{key}:</span>
                      <Badge variant="neutral">{val}</Badge>
                    </div>
                  ))}
                </div>
              </div>

              {/* Suggested prompt */}
              <div className="card" style={{ flex: 1 }}>
                <div className="card-header">
                  <span className="card-title">Prompt sugerido</span>
                </div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div style={{
                    background: '#0d0d0f', borderRadius: 8, padding: 12,
                    fontSize: 13, color: '#c0c0d0', lineHeight: 1.7,
                    border: '1px solid #1a1a1e', minHeight: 80,
                  }}>
                    {reference.analysis.prompt}
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-primary btn-sm" onClick={sendToScript}>
                      <ArrowUp size={12} /> Enviar para Roteiro
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigator.clipboard.writeText(reference.analysis.prompt)}>
                      <Copy size={12} /> Copiar
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={handleAnalyze}>
                      <RefreshCw size={12} /> Regenerar
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { Eye, EyeOff, ChevronDown, ChevronUp, Download, Upload, Trash2, Check, Zap } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Spinner } from '../shared/Spinner';
import { Badge } from '../shared/Badge';

const PROVIDERS = [
  { id: 'openai',      name: 'OpenAI',                     placeholder: 'sk-...',          docs: 'https://platform.openai.com/api-keys',       local: false, color: '#10a37f', description: 'GPT-4o, o1, o3 — referência em geração de código' },
  { id: 'anthropic',   name: 'Anthropic',                  placeholder: 'sk-ant-...',      docs: 'https://console.anthropic.com/settings/keys', local: false, color: '#c17f3e', description: 'Claude 3.5 / 4.x — excelente em raciocínio estruturado' },
  { id: 'google',      name: 'Google Gemini',              placeholder: 'AIza...',         docs: 'https://aistudio.google.com/app/apikey',      local: false, color: '#4285f4', description: 'Gemini 1.5 / 2.0 — contexto de 1M tokens' },
  { id: 'mistral',     name: 'Mistral AI',                 placeholder: '...',             docs: 'https://console.mistral.ai/api-keys',         local: false, color: '#ff7000', description: 'Modelos leves e eficientes' },
  { id: 'cohere',      name: 'Cohere',                     placeholder: '...',             docs: 'https://dashboard.cohere.com/api-keys',       local: false, color: '#39594d', description: 'Command R+ — especializado em RAG' },
  { id: 'groq',        name: 'Groq',                       placeholder: 'gsk_...',         docs: 'https://console.groq.com/keys',               local: false, color: '#f55036', description: 'Velocidade extrema — inferência em hardware dedicado' },
  { id: 'together',    name: 'Together AI',                placeholder: '...',             docs: 'https://api.together.ai/',                    local: false, color: '#0f6fff', description: 'Acesso a dezenas de modelos open-source' },
  { id: 'perplexity',  name: 'Perplexity AI',              placeholder: 'pplx-...',        docs: 'https://www.perplexity.ai/settings/api',      local: false, color: '#20b2aa', description: 'Llama com busca online integrada' },
  { id: 'deepseek',    name: 'DeepSeek',                   placeholder: 'sk-...',          docs: 'https://platform.deepseek.com/api_keys',      local: false, color: '#4d6bfe', description: 'R1, V3 — modelos de alto desempenho' },
  { id: 'xai',         name: 'xAI (Grok)',                 placeholder: 'xai-...',         docs: 'https://x.ai/api',                            local: false, color: '#1da1f2', description: 'Grok — modelos da xAI' },
  { id: 'openrouter',  name: 'OpenRouter',                 placeholder: 'sk-or-...',       docs: 'https://openrouter.ai/keys',                  local: false, color: '#6c63ff', description: '100+ modelos com uma única chave' },
  { id: 'huggingface', name: 'Hugging Face',               placeholder: 'hf_...',          docs: 'https://huggingface.co/settings/tokens',      local: false, color: '#ff9d00', description: 'Inference API — modelos open-source' },
  { id: 'replicate',   name: 'Replicate',                  placeholder: 'r8_...',          docs: 'https://replicate.com/account/api-tokens',    local: false, color: '#000000', description: 'Modelos hospedados na nuvem' },
  { id: 'fireworks',   name: 'Fireworks AI',               placeholder: '...',             docs: 'https://fireworks.ai/account/api-keys',       local: false, color: '#ff6b35', description: 'Inferência rápida e econômica' },
  { id: 'anyscale',    name: 'Anyscale',                   placeholder: 'esecret_...',     docs: 'https://app.endpoints.anyscale.com/',         local: false, color: '#00b4d8', description: 'Endpoints gerenciados com LLMs' },
  { id: 'ollama',      name: 'Ollama',                     placeholder: '',               docs: 'https://ollama.ai',                            local: true,  color: '#000000', description: 'Modelos locais — gratuito e privado', defaultUrl: 'http://localhost:11434' },
  { id: 'lmstudio',   name: 'LM Studio',                   placeholder: '',               docs: 'https://lmstudio.ai',                          local: true,  color: '#8b5cf6', description: 'Interface gráfica para modelos locais', defaultUrl: 'http://localhost:1234' },
  { id: 'azure',       name: 'Azure OpenAI',               placeholder: '...',             docs: 'https://portal.azure.com/',                   local: false, color: '#0078d4', description: 'Deploy próprio de modelos OpenAI na Azure', hasBaseUrl: true },
  { id: 'custom',      name: 'Personalizado',              placeholder: '...',             docs: '',                                            local: false, color: '#6c63ff', description: 'Qualquer endpoint compatível com OpenAI', hasBaseUrl: true },
];

const MODEL_CAPABILITIES = {
  'gpt-4o':                        { ctx: '128K', caps: ['Vision', 'Tools', 'Reasoning'] },
  'gpt-4o-mini':                   { ctx: '128K', caps: ['Vision', 'Tools', 'Fast'] },
  'gpt-4-turbo':                   { ctx: '128K', caps: ['Vision', 'Tools'] },
  'o1-preview':                    { ctx: '128K', caps: ['Reasoning'] },
  'o1-mini':                       { ctx: '128K', caps: ['Reasoning', 'Fast'] },
  'claude-opus-4-7':               { ctx: '200K', caps: ['Vision', 'Tools', 'Reasoning'] },
  'claude-sonnet-4-6':             { ctx: '200K', caps: ['Vision', 'Tools'] },
  'claude-haiku-4-5-20251001':     { ctx: '200K', caps: ['Vision', 'Tools', 'Fast'] },
  'claude-3-5-sonnet-20241022':    { ctx: '200K', caps: ['Vision', 'Tools'] },
  'claude-3-5-haiku-20241022':     { ctx: '200K', caps: ['Vision', 'Tools', 'Fast'] },
  'claude-3-opus-20240229':        { ctx: '200K', caps: ['Vision', 'Tools', 'Reasoning'] },
  'gemini-1.5-pro':                { ctx: '1M',   caps: ['Vision', 'Tools', 'Reasoning'] },
  'gemini-1.5-flash':              { ctx: '1M',   caps: ['Vision', 'Tools', 'Fast'] },
  'gemini-2.0-flash':              { ctx: '1M',   caps: ['Vision', 'Tools', 'Fast'] },
  'mixtral-8x7b-32768':            { ctx: '32K',  caps: ['Fast'] },
  'llama-3.1-70b-versatile':       { ctx: '128K', caps: ['Fast'] },
  'deepseek-chat':                 { ctx: '64K',  caps: ['Tools', 'Reasoning'] },
  'deepseek-reasoner':             { ctx: '64K',  caps: ['Reasoning'] },
  'grok-2':                        { ctx: '128K', caps: ['Vision', 'Tools'] },
  'grok-2-vision':                 { ctx: '32K',  caps: ['Vision'] },
};

function ProviderBadge({ provider }) {
  const initial = provider.name.charAt(0).toUpperCase();
  const color = provider.color || '#6c63ff';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '12px 16px',
      background: `${color}12`,
      border: `1px solid ${color}30`,
      borderRadius: 10,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 10,
        background: `${color}25`,
        border: `1.5px solid ${color}50`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 15, fontWeight: 700, color,
        flexShrink: 0,
      }}>
        {initial}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f0f2' }}>{provider.name}</div>
        <div style={{ fontSize: 11, color: '#8a8a9a', marginTop: 1 }}>{provider.description}</div>
      </div>
      <Badge variant={provider.local ? 'success' : 'info'}>
        {provider.local ? 'Local' : 'Cloud'}
      </Badge>
    </div>
  );
}

function ModelCard({ model, selected, onSelect }) {
  const caps = MODEL_CAPABILITIES[model.id] || {
    ctx: model.context_length ? `${Math.round(model.context_length / 1000)}K` : null,
    caps: [],
  };
  return (
    <div
      className={`card${selected ? ' card-active' : ''}`}
      style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
      onClick={() => onSelect(model.id)}
    >
      <div style={{ padding: '10px 12px', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div style={{
          width: 16, height: 16, borderRadius: '50%', border: `2px solid ${selected ? '#6c63ff' : '#44444e'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2,
        }}>
          {selected && <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#6c63ff' }} />}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: '#f0f0f2', wordBreak: 'break-all', lineHeight: 1.4 }}>{model.id}</div>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 5 }}>
            {caps.ctx && <Badge variant="neutral">{caps.ctx}</Badge>}
            {caps.caps.map((c) => (
              <Badge key={c} variant={c === 'Vision' ? 'info' : c === 'Fast' ? 'success' : c === 'Reasoning' ? 'accent' : 'neutral'}>
                {c}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ApiTab() {
  const { api, updateApi, setModels } = useAppStore();
  const [showKey, setShowKey] = useState(false);
  const [modelSearch, setModelSearch] = useState('');
  const [modelFilter, setModelFilter] = useState('all');
  const [visionSame, setVisionSame] = useState(api.sameModelForVision ?? true);
  const [saved, setSaved] = useState(false);
  const autoLoadTimer = useRef(null);

  const provider = PROVIDERS.find((p) => p.id === api.provider) || PROVIDERS[0];
  const isLocal = provider.local;
  const hasBaseUrl = provider.local || provider.hasBaseUrl;

  // Auto-fill base URL for local providers
  useEffect(() => {
    if (provider.defaultUrl && !api.baseUrl) {
      updateApi({ baseUrl: provider.defaultUrl });
    }
  }, [api.provider]);

  // Load saved API key when provider changes
  useEffect(() => {
    window.electronAPI?.loadApiKey(api.provider).then((key) => {
      if (key) {
        updateApi({ apiKey: key });
        // Se já tem chave salva, carrega modelos automaticamente
        triggerAutoLoad(key);
      }
    });
  }, [api.provider]);

  const triggerAutoLoad = (key) => {
    if (autoLoadTimer.current) clearTimeout(autoLoadTimer.current);
    autoLoadTimer.current = setTimeout(() => {
      loadModels(key);
    }, 800);
  };

  const handleKeyChange = (e) => {
    const key = e.target.value;
    updateApi({ apiKey: key, modelError: '' });
    if (key.length > 10) {
      triggerAutoLoad(key);
    }
  };

  const handleSaveKey = async () => {
    await window.electronAPI?.saveApiKey(api.provider, api.apiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const loadModels = async (keyOverride) => {
    const key = keyOverride ?? api.apiKey;
    updateApi({ isLoadingModels: true, modelError: '', models: [] });
    try {
      await window.electronAPI?.saveApiKey(api.provider, key);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);

      let models = [];

      if (api.provider === 'anthropic') {
        models = [
          { id: 'claude-opus-4-7' },
          { id: 'claude-sonnet-4-6' },
          { id: 'claude-haiku-4-5-20251001' },
          { id: 'claude-3-5-sonnet-20241022' },
          { id: 'claude-3-5-haiku-20241022' },
          { id: 'claude-3-opus-20240229' },
        ];
      } else if (api.provider === 'openai') {
        const res = await fetch('https://api.openai.com/v1/models', {
          headers: { Authorization: `Bearer ${key}` },
        });
        if (!res.ok) throw new Error(res.status === 401 ? 'Chave de API inválida' : `Erro ${res.status}`);
        const data = await res.json();
        models = data.data
          .filter((m) => m.id.startsWith('gpt') || m.id.startsWith('o1') || m.id.startsWith('o3'))
          .sort((a, b) => a.id.localeCompare(b.id));
      } else if (api.provider === 'google') {
        const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${key}`);
        if (!res.ok) throw new Error(res.status === 400 ? 'Chave inválida' : `Erro ${res.status}`);
        const data = await res.json();
        models = (data.models || [])
          .filter((m) => m.name.includes('gemini'))
          .map((m) => ({ id: m.name.replace('models/', '') }));
      } else if (api.provider === 'ollama') {
        const baseUrl = api.baseUrl || 'http://localhost:11434';
        const res = await fetch(`${baseUrl}/api/tags`);
        if (!res.ok) throw new Error('Ollama offline — verifique se está rodando');
        const data = await res.json();
        models = (data.models || []).map((m) => ({ id: m.name }));
      } else if (api.provider === 'lmstudio') {
        const baseUrl = api.baseUrl || 'http://localhost:1234';
        const res = await fetch(`${baseUrl}/v1/models`);
        if (!res.ok) throw new Error('LM Studio offline');
        const data = await res.json();
        models = (data.data || []).map((m) => ({ id: m.id }));
      } else if (api.provider === 'openrouter') {
        const res = await fetch('https://openrouter.ai/api/v1/models', {
          headers: { Authorization: `Bearer ${key}` },
        });
        if (!res.ok) throw new Error('Chave inválida ou erro na requisição');
        const data = await res.json();
        models = (data.data || []).map((m) => ({ id: m.id, context_length: m.context_length }));
      } else if (api.provider === 'groq') {
        const res = await fetch('https://api.groq.com/openai/v1/models', {
          headers: { Authorization: `Bearer ${key}` },
        });
        if (!res.ok) throw new Error(res.status === 401 ? 'Chave inválida' : `Erro ${res.status}`);
        const data = await res.json();
        models = (data.data || []).sort((a, b) => a.id.localeCompare(b.id));
      } else if (api.provider === 'mistral') {
        const res = await fetch('https://api.mistral.ai/v1/models', {
          headers: { Authorization: `Bearer ${key}` },
        });
        if (!res.ok) throw new Error(res.status === 401 ? 'Chave inválida' : `Erro ${res.status}`);
        const data = await res.json();
        models = (data.data || []).sort((a, b) => a.id.localeCompare(b.id));
      } else if (api.provider === 'perplexity') {
        models = [
          { id: 'llama-3.1-sonar-small-128k-online' },
          { id: 'llama-3.1-sonar-large-128k-online' },
          { id: 'llama-3.1-sonar-huge-128k-online' },
        ];
      } else if (api.provider === 'huggingface') {
        models = [
          { id: 'meta-llama/Llama-3.1-8B-Instruct' },
          { id: 'meta-llama/Llama-3.1-70B-Instruct' },
          { id: 'mistralai/Mistral-7B-Instruct-v0.3' },
          { id: 'Qwen/Qwen2.5-72B-Instruct' },
        ];
      } else if (api.provider === 'deepseek') {
        const res = await fetch('https://api.deepseek.com/v1/models', {
          headers: { Authorization: `Bearer ${key}` },
        });
        if (!res.ok) throw new Error(res.status === 401 ? 'Chave inválida' : `Erro ${res.status}`);
        const data = await res.json();
        models = (data.data || []).sort((a, b) => a.id.localeCompare(b.id));
      } else if (api.provider === 'xai') {
        const res = await fetch('https://api.x.ai/v1/models', {
          headers: { Authorization: `Bearer ${key}` },
        });
        if (!res.ok) throw new Error(res.status === 401 ? 'Chave inválida' : `Erro ${res.status}`);
        const data = await res.json();
        models = (data.data || []).sort((a, b) => a.id.localeCompare(b.id));
      } else {
        const baseUrl = api.baseUrl || `https://api.${api.provider}.com/v1`;
        const res = await fetch(`${baseUrl}/models`, {
          headers: { Authorization: `Bearer ${key}` },
        });
        if (!res.ok) throw new Error(`Erro ${res.status} — verifique a chave e a URL base`);
        const data = await res.json();
        models = data.data || data.models || [];
      }

      setModels(models);
    } catch (e) {
      updateApi({ isLoadingModels: false, modelError: e.message || 'Erro ao carregar modelos' });
    }
  };

  const filteredModels = api.models.filter((m) => {
    const caps = MODEL_CAPABILITIES[m.id]?.caps || [];
    if (modelSearch && !m.id.toLowerCase().includes(modelSearch.toLowerCase())) return false;
    if (modelFilter === 'all') return true;
    return caps.map((c) => c.toLowerCase()).includes(modelFilter.toLowerCase());
  });

  const exportConfig = () => {
    const cfg = { provider: api.provider, baseUrl: api.baseUrl, selectedModel: api.selectedModel, visionModel: api.visionModel, temperature: api.temperature, maxTokens: api.maxTokens, streaming: api.streaming, timeout: api.timeout };
    const blob = new Blob([JSON.stringify(cfg, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'motion-agent-config.json'; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="tab-content">

      {/* ── Seleção de provedor ── */}
      <div className="section">
        <div className="section-title">Provedor de IA</div>
        <div className="card">
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

            <div className="input-group">
              <label className="input-label">Selecione o provedor</label>
              <select
                className="select"
                value={api.provider}
                onChange={(e) => updateApi({ provider: e.target.value, models: [], selectedModel: '', apiKey: '', modelError: '' })}
              >
                <optgroup label="☁️ Cloud">
                  {PROVIDERS.filter((p) => !p.local).map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </optgroup>
                <optgroup label="🖥️ Local">
                  {PROVIDERS.filter((p) => p.local).map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </optgroup>
              </select>
            </div>

            {/* Badge visual do provedor selecionado */}
            <ProviderBadge provider={provider} />

            {!isLocal && (
              <div className="input-group">
                <label className="input-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>API Key — <span style={{ color: provider.color || '#6c63ff', fontWeight: 600 }}>{provider.name}</span></span>
                  {provider.docs && (
                    <a
                      href="#"
                      onClick={(e) => { e.preventDefault(); window.electronAPI?.openExternal?.(provider.docs); }}
                      style={{ fontSize: 11, color: '#6c63ff', textDecoration: 'none' }}
                    >
                      Obter chave ↗
                    </a>
                  )}
                </label>

                <div style={{ display: 'flex', gap: 8 }}>
                  <div style={{ flex: 1, position: 'relative' }}>
                    <input
                      className="input"
                      type={showKey ? 'text' : 'password'}
                      value={api.apiKey}
                      onChange={handleKeyChange}
                      placeholder={provider.placeholder || 'Cole sua API key aqui...'}
                      style={{ paddingRight: 72 }}
                    />
                    <div style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      {api.isLoadingModels && <Spinner size={12} />}
                      <button
                        onClick={() => setShowKey(!showKey)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#8a8a9a', display: 'flex' }}
                      >
                        {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                  </div>
                  <button
                    className={`btn btn-sm ${saved ? 'btn-teal' : 'btn-secondary'}`}
                    onClick={handleSaveKey}
                    disabled={!api.apiKey}
                  >
                    {saved ? <><Check size={13} /> Salvo</> : 'Salvar'}
                  </button>
                </div>

                <span className="input-hint">
                  {api.isLoadingModels
                    ? '⏳ Validando chave e carregando modelos...'
                    : api.models.length > 0
                      ? `✅ Chave válida — ${api.models.length} modelos disponíveis`
                      : 'Cole a chave e os modelos serão carregados automaticamente'}
                </span>
              </div>
            )}

            {hasBaseUrl && (
              <div className="input-group">
                <label className="input-label">URL Base</label>
                <input
                  className="input"
                  value={api.baseUrl}
                  onChange={(e) => updateApi({ baseUrl: e.target.value })}
                  placeholder={provider.defaultUrl || 'https://api.exemplo.com/v1'}
                />
                {isLocal && (
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ marginTop: 6, alignSelf: 'flex-start' }}
                    onClick={() => loadModels()}
                    disabled={api.isLoadingModels}
                  >
                    {api.isLoadingModels ? <><Spinner size={12} color="#fff" /> Carregando...</> : <><Zap size={13} /> Conectar e listar modelos</>}
                  </button>
                )}
              </div>
            )}

            {api.modelError && (
              <div style={{ padding: '10px 14px', background: '#ff4d6d10', borderRadius: 8, border: '1px solid #ff4d6d30', fontSize: 12, color: '#ff4d6d', display: 'flex', alignItems: 'center', gap: 8 }}>
                ❌ {api.modelError}
                <button
                  className="btn btn-secondary btn-sm"
                  style={{ marginLeft: 'auto', fontSize: 11 }}
                  onClick={() => loadModels()}
                >
                  Tentar novamente
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Seleção de modelo principal ── */}
      {api.models.length > 0 && (
        <div className="section">
          <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            Modelo principal
            <Badge variant="accent">{api.models.length} disponíveis</Badge>
            {api.selectedModel && (
              <Badge variant="success" dot>{api.selectedModel}</Badge>
            )}
          </div>

          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              className="input"
              style={{ flex: 1, minWidth: 160 }}
              placeholder="Buscar modelo..."
              value={modelSearch}
              onChange={(e) => setModelSearch(e.target.value)}
            />
            {['all', 'Vision', 'Fast', 'Reasoning', 'Tools'].map((f) => (
              <button
                key={f}
                className={`chip${modelFilter === f ? ' active' : ''}`}
                onClick={() => setModelFilter(f)}
              >
                {f === 'all' ? 'Todos' : f}
              </button>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, maxHeight: 300, overflowY: 'auto' }}>
            {filteredModels.map((m) => (
              <ModelCard
                key={m.id}
                model={m}
                selected={api.selectedModel === m.id}
                onSelect={(id) => {
                  updateApi({ selectedModel: id });
                  if (visionSame) updateApi({ visionModel: id });
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Modelo de visão ── */}
      {api.models.length > 0 && (
        <div className="section">
          <div className="section-title">Modelo de visão (análise de frames e referências)</div>
          <div className="card">
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
                <input
                  type="checkbox"
                  checked={visionSame}
                  onChange={(e) => {
                    setVisionSame(e.target.checked);
                    updateApi({ sameModelForVision: e.target.checked });
                    if (e.target.checked) updateApi({ visionModel: api.selectedModel });
                  }}
                  style={{ accentColor: '#6c63ff' }}
                />
                Usar o mesmo modelo principal
              </label>
              {!visionSame && (
                <select
                  className="select"
                  value={api.visionModel}
                  onChange={(e) => updateApi({ visionModel: e.target.value })}
                >
                  <option value="">Selecione um modelo de visão...</option>
                  {api.models.map((m) => <option key={m.id} value={m.id}>{m.id}</option>)}
                </select>
              )}
              {api.visionModel && (
                <span className="input-hint" style={{ color: '#00d4aa' }}>
                  ✅ Modelo de visão: {api.visionModel}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Configurações avançadas ── */}
      <div className="card">
        <div
          className="card-header"
          style={{ cursor: 'pointer' }}
          onClick={() => updateApi({ advancedOpen: !api.advancedOpen })}
        >
          <span className="card-title">Configurações avançadas</span>
          {api.advancedOpen ? <ChevronUp size={14} style={{ color: '#8a8a9a' }} /> : <ChevronDown size={14} style={{ color: '#8a8a9a' }} />}
        </div>
        {api.advancedOpen && (
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">Temperature: {api.temperature}</label>
                <input type="range" min="0" max="2" step="0.1" value={api.temperature} onChange={(e) => updateApi({ temperature: parseFloat(e.target.value) })} style={{ width: '100%', accentColor: '#6c63ff' }} />
              </div>
              <div className="input-group">
                <label className="input-label">Max tokens: {api.maxTokens.toLocaleString()}</label>
                <input type="range" min="256" max="128000" step="256" value={api.maxTokens} onChange={(e) => updateApi({ maxTokens: parseInt(e.target.value) })} style={{ width: '100%', accentColor: '#6c63ff' }} />
              </div>
            </div>
            <div className="input-group">
              <label className="input-label">System prompt adicional</label>
              <textarea className="input" style={{ minHeight: 60 }} value={api.systemPrompt} onChange={(e) => updateApi({ systemPrompt: e.target.value })} placeholder="Instruções adicionais para o modelo..." />
            </div>
            <div className="grid-2">
              <div className="toggle-row">
                <div className="toggle-info">
                  <span className="toggle-label">Streaming de resposta</span>
                </div>
                <label className="toggle">
                  <input type="checkbox" checked={api.streaming} onChange={(e) => updateApi({ streaming: e.target.checked })} />
                  <span className="toggle-track" />
                </label>
              </div>
              <div className="input-group">
                <label className="input-label">Timeout de requisição</label>
                <select className="select" value={api.timeout} onChange={(e) => updateApi({ timeout: parseInt(e.target.value) })}>
                  {[30, 60, 120, 300].map((t) => <option key={t} value={t}>{t}s</option>)}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <Badge variant="success" dot>Configurações salvas automaticamente</Badge>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={exportConfig}>
            <Download size={13} /> Exportar
          </button>
          <button className="btn btn-secondary btn-sm">
            <Upload size={13} /> Importar
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => updateApi({ apiKey: '', selectedModel: '', visionModel: '', models: [], modelError: '' })}>
            <Trash2 size={13} /> Limpar
          </button>
        </div>
      </div>
    </div>
  );
}

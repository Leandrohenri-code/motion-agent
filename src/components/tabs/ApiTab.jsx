import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, RefreshCw, ChevronDown, ChevronUp, Download, Upload, Trash2, Check } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Spinner } from '../shared/Spinner';
import { Badge } from '../shared/Badge';

const PROVIDERS = [
  { id: 'openai',      name: 'OpenAI',                placeholder: 'sk-...',          docs: 'https://platform.openai.com/api-keys',      local: false },
  { id: 'anthropic',   name: 'Anthropic (Claude)',    placeholder: 'sk-ant-...',      docs: 'https://console.anthropic.com/settings/keys', local: false },
  { id: 'google',      name: 'Google Gemini',         placeholder: 'AIza...',         docs: 'https://aistudio.google.com/app/apikey',      local: false },
  { id: 'mistral',     name: 'Mistral AI',            placeholder: '...',             docs: 'https://console.mistral.ai/api-keys',         local: false },
  { id: 'cohere',      name: 'Cohere',                placeholder: '...',             docs: 'https://dashboard.cohere.com/api-keys',       local: false },
  { id: 'groq',        name: 'Groq',                  placeholder: 'gsk_...',         docs: 'https://console.groq.com/keys',               local: false },
  { id: 'together',    name: 'Together AI',           placeholder: '...',             docs: 'https://api.together.ai/',                    local: false },
  { id: 'perplexity',  name: 'Perplexity AI',         placeholder: 'pplx-...',        docs: 'https://www.perplexity.ai/settings/api',      local: false },
  { id: 'deepseek',    name: 'DeepSeek',              placeholder: 'sk-...',          docs: 'https://platform.deepseek.com/api_keys',      local: false },
  { id: 'xai',         name: 'xAI (Grok)',            placeholder: 'xai-...',         docs: 'https://x.ai/api',                            local: false },
  { id: 'openrouter',  name: 'OpenRouter (100+ models)', placeholder: 'sk-or-...',  docs: 'https://openrouter.ai/keys',                  local: false },
  { id: 'huggingface', name: 'Hugging Face Inference', placeholder: 'hf_...',        docs: 'https://huggingface.co/settings/tokens',      local: false },
  { id: 'replicate',   name: 'Replicate',             placeholder: 'r8_...',          docs: 'https://replicate.com/account/api-tokens',    local: false },
  { id: 'fireworks',   name: 'Fireworks AI',          placeholder: '...',             docs: 'https://fireworks.ai/account/api-keys',       local: false },
  { id: 'anyscale',    name: 'Anyscale',              placeholder: 'esecret_...',     docs: 'https://app.endpoints.anyscale.com/',         local: false },
  { id: 'ollama',      name: 'Ollama (local)',         placeholder: '',               docs: 'https://ollama.ai',                           local: true,  defaultUrl: 'http://localhost:11434' },
  { id: 'lmstudio',   name: 'LM Studio (local)',      placeholder: '',               docs: 'https://lmstudio.ai',                         local: true,  defaultUrl: 'http://localhost:1234' },
  { id: 'azure',       name: 'Azure OpenAI',          placeholder: '...',             docs: 'https://portal.azure.com/',                   local: false, hasBaseUrl: true },
  { id: 'bedrock',     name: 'Amazon Bedrock',        placeholder: 'AWS Access Key', docs: 'https://aws.amazon.com/bedrock/',             local: false },
  { id: 'vertex',      name: 'Vertex AI (Google Cloud)', placeholder: 'API Key', docs: 'https://cloud.google.com/vertex-ai',          local: false },
  { id: 'custom',      name: '➕ Personalizado',       placeholder: '...',             docs: '',                                            local: false, hasBaseUrl: true },
];

const MODEL_CAPABILITIES = {
  'gpt-4o':          { ctx: '128K', caps: ['Vision', 'Tools', 'Reasoning'] },
  'gpt-4o-mini':     { ctx: '128K', caps: ['Vision', 'Tools', 'Fast'] },
  'gpt-4-turbo':     { ctx: '128K', caps: ['Vision', 'Tools'] },
  'o1-preview':      { ctx: '128K', caps: ['Reasoning'] },
  'o1-mini':         { ctx: '128K', caps: ['Reasoning', 'Fast'] },
  'claude-3-5-sonnet-20241022': { ctx: '200K', caps: ['Vision', 'Tools'] },
  'claude-3-5-haiku-20241022':  { ctx: '200K', caps: ['Vision', 'Tools', 'Fast'] },
  'claude-3-opus-20240229':     { ctx: '200K', caps: ['Vision', 'Tools', 'Reasoning'] },
  'gemini-1.5-pro':  { ctx: '1M',   caps: ['Vision', 'Tools', 'Reasoning'] },
  'gemini-1.5-flash':{ ctx: '1M',   caps: ['Vision', 'Tools', 'Fast'] },
  'mixtral-8x7b-32768':   { ctx: '32K', caps: ['Fast'] },
  'llama-3.1-70b-versatile': { ctx: '128K', caps: ['Fast'] },
};

function ModelCard({ model, selected, onSelect }) {
  const caps = MODEL_CAPABILITIES[model.id] || { ctx: model.context_length ? `${Math.round(model.context_length / 1000)}K` : '?', caps: [] };
  return (
    <div
      className={`card${selected ? ' card-active' : ''}`}
      style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
      onClick={() => onSelect(model.id)}
    >
      <div style={{ padding: '10px 12px', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div style={{
          width: 18, height: 18, borderRadius: '50%', border: `2px solid ${selected ? '#6c63ff' : '#44444e'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1,
        }}>
          {selected && <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#6c63ff' }} />}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: '#f0f0f2' }} className="truncate">{model.id}</div>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
            {caps.ctx && (
              <Badge variant="neutral">{caps.ctx}</Badge>
            )}
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
  const [visionSame, setVisionSame] = useState(api.sameModelForVision);
  const [saved, setSaved] = useState(false);

  const provider = PROVIDERS.find((p) => p.id === api.provider) || PROVIDERS[0];
  const isLocal = provider.local;
  const hasBaseUrl = provider.local || provider.hasBaseUrl;

  // Auto-fill base URL for local providers
  useEffect(() => {
    if (provider.defaultUrl && !api.baseUrl) {
      updateApi({ baseUrl: provider.defaultUrl });
    }
  }, [api.provider]);

  // Load saved API key
  useEffect(() => {
    window.electronAPI?.loadApiKey(api.provider).then((key) => {
      if (key) updateApi({ apiKey: key });
    });
  }, [api.provider]);

  const handleSaveKey = async () => {
    await window.electronAPI?.saveApiKey(api.provider, api.apiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleLoadModels = async () => {
    updateApi({ isLoadingModels: true, modelError: '', models: [] });
    try {
      await window.electronAPI?.saveApiKey(api.provider, api.apiKey);
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
          headers: { Authorization: `Bearer ${api.apiKey}` },
        });
        if (!res.ok) throw new Error(res.status === 401 ? 'Chave inválida' : `Erro ${res.status}`);
        const data = await res.json();
        models = data.data.filter((m) => m.id.startsWith('gpt') || m.id.startsWith('o1')).sort((a, b) => a.id.localeCompare(b.id));
      } else if (api.provider === 'ollama') {
        const baseUrl = api.baseUrl || 'http://localhost:11434';
        const res = await fetch(`${baseUrl}/api/tags`);
        if (!res.ok) throw new Error('Ollama offline');
        const data = await res.json();
        models = (data.models || []).map((m) => ({ id: m.name }));
      } else if (api.provider === 'openrouter') {
        const res = await fetch('https://openrouter.ai/api/v1/models', {
          headers: { Authorization: `Bearer ${api.apiKey}` },
        });
        if (!res.ok) throw new Error('Erro ao carregar modelos');
        const data = await res.json();
        models = (data.data || []).map((m) => ({ id: m.id, context_length: m.context_length }));
      } else {
        const baseUrl = api.baseUrl || `https://api.${api.provider}.com/v1`;
        const res = await fetch(`${baseUrl}/models`, {
          headers: { Authorization: `Bearer ${api.apiKey}` },
        });
        if (!res.ok) throw new Error(`Erro ${res.status}`);
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
      {/* Provider */}
      <div className="section">
        <div className="section-title">Provedor de IA</div>
        <div className="card">
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="input-group">
              <label className="input-label">Provedor</label>
              <select className="select" value={api.provider} onChange={(e) => updateApi({ provider: e.target.value, models: [], selectedModel: '', apiKey: '' })}>
                {PROVIDERS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              {api.provider === 'openrouter' && (
                <span className="input-hint" style={{ color: '#6c63ff' }}>💡 OpenRouter dá acesso a 100+ modelos com uma única chave</span>
              )}
            </div>

            {!isLocal && (
              <div className="input-group">
                <label className="input-label">
                  API Key
                  {provider.docs && (
                    <a href="#" onClick={(e) => { e.preventDefault(); window.electronAPI?.openExternal(provider.docs); }} style={{ marginLeft: 8, fontSize: 11, color: '#6c63ff', textDecoration: 'none' }}>
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
                      onChange={(e) => updateApi({ apiKey: e.target.value })}
                      placeholder={provider.placeholder || 'Insira sua API key...'}
                      style={{ paddingRight: 36 }}
                    />
                    <button
                      onClick={() => setShowKey(!showKey)}
                      style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#8a8a9a' }}
                    >
                      {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                  <button className={`btn btn-sm ${saved ? 'btn-teal' : 'btn-secondary'}`} onClick={handleSaveKey}>
                    {saved ? <><Check size={13} /> Salvo</> : 'Salvar'}
                  </button>
                </div>
                <span className="input-hint">Armazenado com segurança no Keychain do sistema operacional</span>
              </div>
            )}

            {hasBaseUrl && (
              <div className="input-group">
                <label className="input-label">URL Base</label>
                <input className="input" value={api.baseUrl} onChange={(e) => updateApi({ baseUrl: e.target.value })} placeholder={provider.defaultUrl || 'https://api.exemplo.com/v1'} />
              </div>
            )}

            <button className="btn btn-primary" onClick={handleLoadModels} disabled={api.isLoadingModels || (!isLocal && !api.apiKey)}>
              {api.isLoadingModels ? <><Spinner size={14} color="#fff" /> Carregando...</> : <><RefreshCw size={14} /> Carregar modelos disponíveis</>}
            </button>

            {api.modelError && (
              <div style={{ padding: '8px 12px', background: '#ff4d6d10', borderRadius: 8, border: '1px solid #ff4d6d30', fontSize: 12, color: '#ff4d6d' }}>
                ❌ {api.modelError}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Model selection */}
      {api.models.length > 0 && (
        <div className="section">
          <div className="section-title">Modelo principal — {api.models.length} disponíveis</div>

          {/* Filters */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input className="input" style={{ flex: 1 }} placeholder="Buscar modelo..." value={modelSearch} onChange={(e) => setModelSearch(e.target.value)} />
            {['all', 'Vision', 'Fast', 'Reasoning', 'Tools'].map((f) => (
              <button key={f} className={`chip${modelFilter === f ? ' active' : ''}`} onClick={() => setModelFilter(f)}>
                {f === 'all' ? 'Todos' : f}
              </button>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, maxHeight: 280, overflowY: 'auto' }}>
            {filteredModels.map((m) => (
              <ModelCard key={m.id} model={m} selected={api.selectedModel === m.id} onSelect={(id) => {
                updateApi({ selectedModel: id });
                if (visionSame) updateApi({ visionModel: id });
              }} />
            ))}
          </div>
        </div>
      )}

      {/* Vision model */}
      {api.models.length > 0 && (
        <div className="section">
          <div className="section-title">Modelo de visão (frames e referências)</div>
          <div className="card">
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
                <input type="checkbox" checked={visionSame} onChange={(e) => {
                  setVisionSame(e.target.checked);
                  updateApi({ sameModelForVision: e.target.checked });
                  if (e.target.checked) updateApi({ visionModel: api.selectedModel });
                }} style={{ accentColor: '#6c63ff' }} />
                Usar o mesmo modelo principal
              </label>
              {!visionSame && (
                <select className="select" value={api.visionModel} onChange={(e) => updateApi({ visionModel: e.target.value })}>
                  <option value="">Selecione um modelo de visão...</option>
                  {api.models.map((m) => <option key={m.id} value={m.id}>{m.id}</option>)}
                </select>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Advanced settings */}
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

      {/* Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <Badge variant="success" dot>Configurações salvas automaticamente</Badge>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={exportConfig}>
            <Download size={13} /> Exportar
          </button>
          <button className="btn btn-secondary btn-sm">
            <Upload size={13} /> Importar
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => updateApi({ apiKey: '', selectedModel: '', visionModel: '', models: [] })}>
            <Trash2 size={13} /> Limpar
          </button>
        </div>
      </div>
    </div>
  );
}

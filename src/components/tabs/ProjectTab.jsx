import React, { useEffect } from 'react';
import { Play, ExternalLink } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { FolderInput } from '../shared/FolderInput';
import { Badge } from '../shared/Badge';

const RESOLUTIONS = [
  { value: '720p',     label: '720p (1280×720)' },
  { value: '1080p',    label: '1080p (1920×1080)' },
  { value: '1080v',    label: '1080p Vertical (1080×1920)' },
  { value: '4k',       label: '4K (3840×2160)' },
  { value: 'square',   label: 'Quadrado (1080×1080)' },
];

const FORMATS = [
  { value: 'mp4-h264', label: 'MP4 (H.264)' },
  { value: 'mp4-h265', label: 'MP4 (H.265)' },
  { value: 'webm',     label: 'WebM' },
  { value: 'prores',   label: 'ProRes' },
];

function Toggle({ label, description, checked, onChange }) {
  return (
    <div className="toggle-row">
      <div className="toggle-info">
        <span className="toggle-label">{label}</span>
        {description && <span className="toggle-desc">{description}</span>}
      </div>
      <label className="toggle">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        <span className="toggle-track" />
      </label>
    </div>
  );
}

export function ProjectTab() {
  const { project, updateProject, agent, frames } = useAppStore();

  useEffect(() => {
    if (project.remotionPath) {
      window.electronAPI?.detectRemotion(project.remotionPath).then((found) => {
        updateProject({ remotionDetected: found });
      });
    }
  }, [project.remotionPath]);

  const handleStart = async () => {
    const { api, script, reference } = useAppStore.getState();
    const config = {
      project,
      frames: frames.map((f) => ({ id: f.id, preview: f.preview, description: f.description, duration: f.duration })),
      script,
      reference,
      api: { ...api, apiKey: await window.electronAPI?.loadApiKey(api.provider) || api.apiKey },
    };
    const unsub = window.electronAPI?.onAgentMessage((msg) => {
      useAppStore.getState().handleAgentMessage(msg);
    });
    useAppStore.getState().updateAgent({ isRunning: true, status: 'running', currentScene: 0, totalScenes: frames.length, logs: [] });
    await window.electronAPI?.startAgent(config);
  };

  const handleOpenStudio = () => {
    if (project.remotionPath) {
      window.electronAPI?.openRemotionStudio(project.remotionPath);
    }
  };

  return (
    <div className="tab-content">
      {/* Identificação */}
      <div className="section">
        <div className="section-title">Identificação</div>
        <div className="grid-2">
          <div className="input-group">
            <label className="input-label">Nome do projeto</label>
            <input className="input" value={project.name} onChange={(e) => updateProject({ name: e.target.value })} placeholder="Meu vídeo incrível" />
          </div>
          <div className="input-group">
            <label className="input-label">Descrição curta <span style={{ color: '#44444e' }}>(opcional)</span></label>
            <input className="input" value={project.description} onChange={(e) => updateProject({ description: e.target.value })} placeholder="Vídeo de apresentação do produto" />
          </div>
        </div>
      </div>

      {/* Remotion */}
      <div className="section">
        <div className="section-title">Remotion</div>
        <div className="card">
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <FolderInput
              label="Pasta do projeto Remotion"
              value={project.remotionPath}
              onChange={(v) => updateProject({ remotionPath: v })}
              type="folder"
              hint="Ex: C:\meus-projetos\meu-video"
            />
            <FolderInput
              label="Arquivo de entrada Remotion"
              value={project.remotionEntry}
              onChange={(v) => updateProject({ remotionEntry: v })}
              type="file"
              accept={['tsx', 'ts', 'js']}
              hint="Arquivo principal do projeto (index.ts ou Root.tsx)"
            />
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              {project.remotionPath ? (
                <Badge variant={project.remotionDetected ? 'success' : 'warning'} dot>
                  {project.remotionDetected ? '✓ Remotion detectado' : '⚠ Remotion não encontrado'}
                </Badge>
              ) : (
                <span style={{ fontSize: 12, color: '#44444e' }}>Selecione a pasta do projeto</span>
              )}
              <button className="btn btn-secondary btn-sm" onClick={handleOpenStudio} disabled={!project.remotionPath}>
                <ExternalLink size={13} /> Abrir Remotion Studio
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Saída */}
      <div className="section">
        <div className="section-title">Saída</div>
        <div className="card">
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <FolderInput
              label="Pasta de saída do vídeo final"
              value={project.outputPath}
              onChange={(v) => updateProject({ outputPath: v })}
              type="folder"
            />
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">Resolução</label>
                <select className="select" value={project.resolution} onChange={(e) => updateProject({ resolution: e.target.value })}>
                  {RESOLUTIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">FPS</label>
                <select className="select" value={project.fps} onChange={(e) => updateProject({ fps: Number(e.target.value) })}>
                  {[24, 30, 60].map((f) => <option key={f} value={f}>{f} FPS</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Formato de saída</label>
                <select className="select" value={project.format} onChange={(e) => updateProject({ format: e.target.value })}>
                  {FORMATS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Comportamento */}
      <div className="section">
        <div className="section-title">Comportamento do agente</div>
        <div className="card">
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column' }}>
            <Toggle
              label="Modo passo a passo"
              description="Pausa após cada cena para aprovação manual — recomendado"
              checked={project.stepByStep}
              onChange={(v) => updateProject({ stepByStep: v })}
            />
            <div style={{ borderTop: '1px solid #22222c' }} />
            <Toggle
              label="Log detalhado"
              description="Exibe o raciocínio completo do agente em tempo real"
              checked={project.verboseLog}
              onChange={(v) => updateProject({ verboseLog: v })}
            />
            <div style={{ borderTop: '1px solid #22222c' }} />
            <Toggle
              label="Verificação de coerência"
              description="IA revisa a consistência visual entre todas as cenas antes do export"
              checked={project.coherenceCheck}
              onChange={(v) => updateProject({ coherenceCheck: v })}
            />
            <div style={{ borderTop: '1px solid #22222c' }} />
            <Toggle
              label="Abrir pasta ao finalizar"
              description="Abre automaticamente a pasta de saída quando o vídeo for gerado"
              checked={project.openFolderOnDone}
              onChange={(v) => updateProject({ openFolderOnDone: v })}
            />
          </div>
        </div>
      </div>

      {/* Spacer + Start button */}
      <div style={{ flex: 1 }} />
      <button
        className="btn btn-primary btn-large"
        style={{ width: '100%', fontSize: 15, padding: '14px 24px' }}
        onClick={handleStart}
        disabled={agent.isRunning || frames.length === 0}
      >
        <Play size={16} /> Iniciar Geração
      </button>
    </div>
  );
}

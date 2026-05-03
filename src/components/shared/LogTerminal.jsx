import React, { useRef, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Trash2, Download, ChevronUp, ChevronDown } from 'lucide-react';

const levelColors = {
  info:    '#f0f0f2',
  warn:    '#ffb340',
  warning: '#ffb340',
  error:   '#ff4d6d',
  success: '#00d4aa',
};

export function LogTerminal() {
  const { agent, logPanelOpen, logPanelHeight, logActiveTab, setLogPanelOpen, setLogPanelHeight, setLogActiveTab, clearLogs, clearErrors } = useAppStore();
  const logRef = useRef(null);
  const isResizing = useRef(false);
  const startY = useRef(0);
  const startH = useRef(0);

  useEffect(() => {
    if (logRef.current && logPanelOpen) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [agent.logs, logPanelOpen]);

  const startResize = (e) => {
    isResizing.current = true;
    startY.current = e.clientY;
    startH.current = logPanelHeight;
    document.addEventListener('mousemove', onResize);
    document.addEventListener('mouseup', stopResize);
  };

  const onResize = (e) => {
    if (!isResizing.current) return;
    const delta = startY.current - e.clientY;
    const newH = Math.max(80, Math.min(500, startH.current + delta));
    setLogPanelHeight(newH);
  };

  const stopResize = () => {
    isResizing.current = false;
    document.removeEventListener('mousemove', onResize);
    document.removeEventListener('mouseup', stopResize);
  };

  const exportLog = () => {
    const text = agent.logs.map((l) => `[${new Date(l.id).toISOString()}] [${l.level.toUpperCase()}] ${l.message}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'motion-agent.log'; a.click();
    URL.revokeObjectURL(url);
  };

  const statusColor = {
    idle: '#8a8a9a',
    running: '#6c63ff',
    waiting: '#ffb340',
    done: '#00d4aa',
    error: '#ff4d6d',
  }[agent.status] || '#8a8a9a';

  const statusLabel = {
    idle: 'Ocioso',
    running: `Gerando cena ${agent.currentScene}/${agent.totalScenes}...`,
    waiting: 'Aguardando aprovação',
    done: 'Concluído',
    error: 'Erro',
  }[agent.status] || 'Ocioso';

  const tabs = ['log', 'code', 'errors'];
  const tabLabels = { log: 'Log do Agente', code: 'Código Gerado', errors: 'Erros' };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      borderTop: '1px solid #22222c',
      background: '#0d0d0f',
      flexShrink: 0,
    }}>
      {/* Resize handle */}
      <div
        onMouseDown={startResize}
        style={{
          height: 4,
          cursor: 'row-resize',
          background: 'transparent',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = '#6c63ff40')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
      />

      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 0,
        padding: '0 12px',
        height: 36,
        borderBottom: logPanelOpen ? '1px solid #22222c' : 'none',
        flexShrink: 0,
      }}>
        {/* Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginRight: 16 }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%', background: statusColor,
            flexShrink: 0,
            animation: agent.status === 'running' ? 'dotPulse 1.5s ease infinite' : undefined,
          }} />
          <span style={{ fontSize: 11, color: statusColor, fontWeight: 500 }}>{statusLabel}</span>
        </div>

        {/* Tabs */}
        {logPanelOpen && tabs.map((t) => (
          <button
            key={t}
            onClick={() => setLogActiveTab(t)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '0 10px', height: '100%',
              fontSize: 11, fontWeight: 500,
              color: logActiveTab === t ? '#f0f0f2' : '#44444e',
              borderBottom: logActiveTab === t ? '2px solid #6c63ff' : '2px solid transparent',
              transition: 'all 0.15s ease',
              display: 'flex', alignItems: 'center', gap: 5,
            }}
          >
            {tabLabels[t]}
            {t === 'errors' && agent.errors.length > 0 && (
              <span style={{
                background: '#ff4d6d20', color: '#ff4d6d',
                border: '1px solid #ff4d6d30',
                borderRadius: 999, padding: '0 5px', fontSize: 10,
              }}>{agent.errors.length}</span>
            )}
          </button>
        ))}

        <div style={{ flex: 1 }} />

        {/* Actions */}
        {logPanelOpen && (
          <>
            <button className="btn btn-ghost btn-sm btn-icon" onClick={logActiveTab === 'errors' ? clearErrors : clearLogs} title="Limpar">
              <Trash2 size={13} />
            </button>
            <button className="btn btn-ghost btn-sm btn-icon" onClick={exportLog} title="Exportar log">
              <Download size={13} />
            </button>
          </>
        )}
        <button
          className="btn btn-ghost btn-sm btn-icon"
          onClick={() => setLogPanelOpen(!logPanelOpen)}
          title={logPanelOpen ? 'Minimizar' : 'Expandir'}
        >
          {logPanelOpen ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
        </button>
      </div>

      {/* Content */}
      {logPanelOpen && (
        <div ref={logRef} style={{ height: logPanelHeight, overflow: 'auto' }}>
          {logActiveTab === 'log' && (
            <div style={{ padding: '8px 0', fontFamily: "'Geist Mono', monospace", fontSize: 12 }}>
              {agent.logs.length === 0 ? (
                <div style={{ padding: '16px 16px', color: '#44444e', textAlign: 'center' }}>
                  Nenhum log ainda. Inicie a geração para ver o progresso.
                </div>
              ) : (
                agent.logs.map((log) => (
                  <div key={log.id} style={{
                    display: 'flex', gap: 10, padding: '2px 16px',
                    lineHeight: 1.6,
                    borderLeft: log.scene ? '2px solid #6c63ff20' : 'none',
                    marginLeft: log.scene ? 0 : 0,
                  }}>
                    <span style={{ color: '#44444e', flexShrink: 0, fontSize: 11 }}>
                      {new Date(log.id).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                    <span style={{ color: levelColors[log.level] || '#f0f0f2' }}>{log.message}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {logActiveTab === 'code' && (
            <div style={{ height: '100%' }}>
              {agent.generatedCode ? (
                <SyntaxHighlighter
                  language="tsx"
                  style={vscDarkPlus}
                  customStyle={{ background: 'transparent', margin: 0, fontSize: 12, height: '100%' }}
                >
                  {agent.generatedCode}
                </SyntaxHighlighter>
              ) : (
                <div style={{ padding: 16, color: '#44444e', textAlign: 'center', fontSize: 13 }}>
                  Nenhum código gerado ainda.
                </div>
              )}
            </div>
          )}

          {logActiveTab === 'errors' && (
            <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {agent.errors.length === 0 ? (
                <div style={{ color: '#44444e', textAlign: 'center', padding: 16, fontSize: 13 }}>
                  Nenhum erro.
                </div>
              ) : (
                agent.errors.map((err, i) => (
                  <div key={i} style={{
                    background: '#ff4d6d10', border: '1px solid #ff4d6d30',
                    borderRadius: 8, padding: '10px 12px',
                  }}>
                    <div style={{ fontSize: 12, color: '#ff4d6d', fontWeight: 500 }}>
                      {err.scene ? `Cena ${err.scene}: ` : ''}{err.message}
                    </div>
                    {err.retryable && (
                      <span style={{ fontSize: 11, color: '#8a8a9a' }}>Pode tentar novamente</span>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

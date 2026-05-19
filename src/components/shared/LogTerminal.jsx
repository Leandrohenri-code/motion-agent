import React, { useRef, useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Trash2, Download, ChevronUp, ChevronDown, CheckCircle, XCircle, RefreshCw, Eye } from 'lucide-react';

const levelColors = {
  info:    '#f0f0f2',
  warn:    '#ffb340',
  warning: '#ffb340',
  error:   '#ff4d6d',
  success: '#00d4aa',
};

// ── Painel de Aprovação de Cena ─────────────────────────────────────────────
function ApprovalPanel({ sceneNum }) {
  const { approveScene, rejectScene, retryScene, agent } = useAppStore();
  const [feedback, setFeedback] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);
  const generatedCode = agent.generatedCode;

  return (
    <div style={{
      background: 'linear-gradient(135deg, #6c63ff18, #00d4aa10)',
      border: '1px solid #6c63ff40',
      borderRadius: 0,
      padding: '12px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      flexShrink: 0,
    }}>
      {/* Título */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Eye size={14} style={{ color: '#6c63ff' }} />
        <span style={{ fontSize: 13, fontWeight: 700, color: '#f0f0f2' }}>
          Cena {sceneNum} pronta — revise e decida
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 11, color: '#8a8a9a' }}>
          Modo passo a passo ativo
        </span>
      </div>

      {/* Campo de feedback */}
      {showFeedback && (
        <textarea
          autoFocus
          placeholder="Descreva o que mudar nesta cena (opcional)..."
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          style={{
            background: '#0d0d0f',
            border: '1px solid #22222c',
            borderRadius: 6,
            color: '#f0f0f2',
            fontSize: 12,
            padding: '8px 10px',
            resize: 'none',
            minHeight: 60,
            fontFamily: 'inherit',
            outline: 'none',
          }}
        />
      )}

      {/* Botões */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {/* Aprovar */}
        <button
          onClick={() => approveScene(sceneNum)}
          style={{
            flex: 1, minWidth: 120,
            padding: '10px 16px',
            borderRadius: 8, border: 'none', cursor: 'pointer',
            background: 'linear-gradient(135deg, #00d4aa, #00b896)',
            color: '#0d0d0f',
            fontSize: 13, fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            boxShadow: '0 2px 12px #00d4aa40',
          }}
        >
          <CheckCircle size={15} /> Aprovar e continuar
        </button>

        {/* Rejeitar com feedback */}
        <button
          onClick={() => {
            if (!showFeedback) { setShowFeedback(true); return; }
            rejectScene(sceneNum, feedback);
            setFeedback('');
            setShowFeedback(false);
          }}
          style={{
            flex: 1, minWidth: 120,
            padding: '10px 16px',
            borderRadius: 8, border: 'none', cursor: 'pointer',
            background: showFeedback ? '#ff4d6d' : '#ff4d6d20',
            outline: '1px solid #ff4d6d40',
            color: showFeedback ? '#fff' : '#ff4d6d',
            fontSize: 13, fontWeight: 600,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}
        >
          <XCircle size={15} />
          {showFeedback ? 'Enviar feedback e regenerar' : 'Rejeitar e dar feedback'}
        </button>

        {/* Retry silencioso */}
        <button
          onClick={() => retryScene(sceneNum)}
          style={{
            padding: '10px 14px',
            borderRadius: 8, border: '1px solid #44444e', cursor: 'pointer',
            background: 'transparent',
            color: '#8a8a9a',
            fontSize: 12, fontWeight: 500,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
          }}
          title="Regenerar sem feedback"
        >
          <RefreshCw size={13} /> Regenerar
        </button>
      </div>
    </div>
  );
}

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

      {/* Painel de aprovação — aparece quando aguardando, independente do painel estar aberto */}
      {agent.awaitingApproval && agent.awaitingScene && (
        <ApprovalPanel sceneNum={agent.awaitingScene} />
      )}

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

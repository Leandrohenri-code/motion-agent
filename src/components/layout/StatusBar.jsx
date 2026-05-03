import React from 'react';
import { useAppStore } from '../../store/useAppStore';

export function StatusBar() {
  const { agent, project } = useAppStore();

  const statusColor = {
    idle:    '#8a8a9a',
    running: '#6c63ff',
    waiting: '#ffb340',
    done:    '#00d4aa',
    error:   '#ff4d6d',
  }[agent.status] || '#8a8a9a';

  const statusText = {
    idle:    '● Ocioso',
    running: `● Gerando cena ${agent.currentScene}/${agent.totalScenes}...`,
    waiting: '● Aguardando aprovação',
    done:    '● Concluído',
    error:   '● Erro',
  }[agent.status] || '● Ocioso';

  return (
    <div style={{
      height: 28,
      flexShrink: 0,
      background: '#0a0a0c',
      borderTop: '1px solid #22222c',
      display: 'flex',
      alignItems: 'center',
      padding: '0 12px',
      gap: 8,
      fontSize: 11,
      fontWeight: 500,
    }}>
      <span style={{
        color: statusColor,
        animation: agent.status === 'running' ? 'pulse 1.5s ease infinite' : undefined,
      }}>
        {statusText}
      </span>

      <div style={{ flex: 1, textAlign: 'center', color: '#44444e' }}>
        {project.name || 'Sem projeto'}
      </div>

      <span style={{ color: '#44444e' }}>
        Remotion: <span style={{ color: '#44444e' }}>Offline</span>
      </span>
    </div>
  );
}

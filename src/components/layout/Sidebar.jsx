import React, { useState } from 'react';
import { Settings, Layers, FileText, Video, Key, Activity } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Tooltip } from '../shared/Tooltip';

const TABS = [
  { id: 'project',   icon: Settings, label: 'Projeto'   },
  { id: 'frames',    icon: Layers,   label: 'Frames'    },
  { id: 'script',    icon: FileText, label: 'Roteiro'   },
  { id: 'reference', icon: Video,    label: 'Referência' },
  { id: 'api',       icon: Key,      label: 'API'       },
];

export function Sidebar() {
  const { activeTab, setActiveTab, agent, project } = useAppStore();
  const [remotionOnline] = useState(false);

  return (
    <nav style={{
      width: 56,
      flexShrink: 0,
      background: '#0d0d0f',
      borderRight: '1px solid #22222c',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      paddingTop: 12,
      paddingBottom: 12,
      gap: 4,
    }}>
      {/* Logo */}
      <div style={{
        width: 36, height: 36,
        borderRadius: 8,
        background: 'linear-gradient(135deg, #6c63ff, #00d4aa)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 12, fontWeight: 600, color: '#fff',
        marginBottom: 12,
        flexShrink: 0,
        boxShadow: '0 0 16px #6c63ff40',
      }}>
        MA
      </div>

      {/* Navigation */}
      {TABS.map(({ id, icon: Icon, label }) => {
        const isActive = activeTab === id;
        const isRunningTab = agent.isRunning && isActive;
        return (
          <Tooltip key={id} label={label} placement="right">
            <button
              onClick={() => setActiveTab(id)}
              style={{
                width: 40, height: 40,
                borderRadius: 8,
                background: isActive ? '#1a1a1e' : 'transparent',
                border: 'none',
                borderLeft: isActive ? '2px solid #6c63ff' : '2px solid transparent',
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: isActive ? '#f0f0f2' : '#8a8a9a',
                transition: 'all 0.15s ease',
                position: 'relative',
                animation: isRunningTab ? 'glow 2s ease infinite' : undefined,
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = '#141416';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <Icon size={18} />
              {isRunningTab && (
                <span style={{
                  position: 'absolute', top: 6, right: 6,
                  width: 5, height: 5, borderRadius: '50%',
                  background: '#6c63ff',
                  animation: 'dotPulse 1.5s ease infinite',
                }} />
              )}
            </button>
          </Tooltip>
        );
      })}

      <div style={{ flex: 1 }} />

      {/* Remotion status */}
      <Tooltip label={remotionOnline ? 'Remotion: Online' : 'Remotion: Offline'} placement="right">
        <button
          onClick={() => {
            if (project.remotionPath) {
              window.electronAPI?.openRemotionStudio(project.remotionPath);
            }
          }}
          style={{
            width: 40, height: 40,
            borderRadius: 8,
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: remotionOnline ? '#00d4aa' : '#44444e',
            transition: 'all 0.15s ease',
          }}
        >
          <Activity size={16} />
        </button>
      </Tooltip>
    </nav>
  );
}

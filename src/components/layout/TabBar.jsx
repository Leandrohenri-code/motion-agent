import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Plus, Zap, Search } from 'lucide-react';

const TAB_META = {
  project:   { title: 'Projeto', icon: '⚙️' },
  frames:    { title: 'Frames',  icon: '🖼️' },
  script:    { title: 'Roteiro', icon: '✍️' },
  reference: { title: 'Referência', icon: '🎬' },
  api:       { title: 'API',     icon: '🔑' },
};

export function TabBar() {
  const { activeTab, project, frames, agent, setActiveTab } = useAppStore();
  const meta = TAB_META[activeTab] || { title: '', icon: '' };

  const renderActions = () => {
    if (activeTab === 'frames') {
      return (
        <div style={{ display: 'flex', gap: 8 }}>
          <span style={{ fontSize: 12, color: '#8a8a9a', display: 'flex', alignItems: 'center' }}>
            {frames.length} cenas · {frames.reduce((s, f) => s + (parseFloat(f.duration) || 3), 0)}s
          </span>
        </div>
      );
    }
    if (activeTab === 'reference') {
      return (
        <button className="btn btn-secondary btn-sm" onClick={() => {}}>
          <Search size={13} /> Analisar
        </button>
      );
    }
    return null;
  };

  return (
    <div style={{
      height: 48,
      flexShrink: 0,
      borderBottom: '1px solid #22222c',
      display: 'flex',
      alignItems: 'center',
      padding: '0 20px',
      gap: 8,
    }}>
      <span style={{ fontSize: 16, fontWeight: 600, color: '#f0f0f2' }}>
        {meta.icon} {meta.title}
      </span>
      {project.name && (
        <>
          <span style={{ color: '#22222c', fontSize: 16 }}>/</span>
          <span style={{ fontSize: 12, color: '#44444e' }} className="truncate" title={project.name}>
            {project.name}
          </span>
        </>
      )}
      <div style={{ flex: 1 }} />
      {renderActions()}
    </div>
  );
}

import React from 'react';
import { FolderOpen, File } from 'lucide-react';

export function FolderInput({ label, value, onChange, placeholder, type = 'folder', accept, hint }) {
  const api = window.electronAPI;

  const handleBrowse = async () => {
    let result = null;
    if (type === 'folder') {
      result = await api.browseFolder();
    } else {
      const filters = accept ? [{ name: 'Files', extensions: accept }] : undefined;
      result = await api.browseFile(filters);
    }
    if (result) onChange(result);
  };

  return (
    <div className="input-group">
      {label && <label className="input-label">{label}</label>}
      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <span style={{
            position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
            color: '#44444e', pointerEvents: 'none',
          }}>
            {type === 'folder' ? <FolderOpen size={14} /> : <File size={14} />}
          </span>
          <input
            className="input"
            style={{ paddingLeft: 30 }}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder || (type === 'folder' ? 'Selecione uma pasta...' : 'Selecione um arquivo...')}
          />
        </div>
        <button className="btn btn-secondary btn-sm" onClick={handleBrowse} type="button">
          Procurar
        </button>
      </div>
      {hint && <span className="input-hint">{hint}</span>}
    </div>
  );
}

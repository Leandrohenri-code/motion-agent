import React from 'react';

export function ProgressBar({ value = 0, max = 100, color = '#6c63ff', height = 4, showLabel = false }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {showLabel && (
        <span style={{ fontSize: 11, color: '#8a8a9a', textAlign: 'right' }}>{Math.round(pct)}%</span>
      )}
      <div style={{
        width: '100%',
        height,
        background: '#22222c',
        borderRadius: 999,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: color,
          borderRadius: 999,
          transition: 'width 0.3s ease',
          boxShadow: pct > 0 ? `0 0 8px ${color}60` : undefined,
        }} />
      </div>
    </div>
  );
}

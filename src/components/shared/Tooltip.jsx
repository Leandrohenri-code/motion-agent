import React, { useState, useRef } from 'react';

export function Tooltip({ children, label, placement = 'top' }) {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef(null);

  const show = () => {
    timerRef.current = setTimeout(() => setVisible(true), 400);
  };
  const hide = () => {
    clearTimeout(timerRef.current);
    setVisible(false);
  };

  const placementStyle = {
    top:    { bottom: 'calc(100% + 6px)', left: '50%', transform: 'translateX(-50%)' },
    bottom: { top: 'calc(100% + 6px)',    left: '50%', transform: 'translateX(-50%)' },
    left:   { right: 'calc(100% + 6px)',  top: '50%',  transform: 'translateY(-50%)' },
    right:  { left: 'calc(100% + 6px)',   top: '50%',  transform: 'translateY(-50%)' },
  };

  return (
    <span
      style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={show}
      onMouseLeave={hide}
    >
      {children}
      {visible && label && (
        <span style={{
          position: 'absolute',
          ...placementStyle[placement],
          background: '#1f1f26',
          border: '1px solid #2a2a32',
          borderRadius: 6,
          padding: '4px 8px',
          fontSize: 12,
          color: '#f0f0f2',
          whiteSpace: 'nowrap',
          pointerEvents: 'none',
          zIndex: 9999,
          animation: 'fadeIn 0.15s ease',
          boxShadow: '0 4px 16px #00000060',
        }}>
          {label}
        </span>
      )}
    </span>
  );
}

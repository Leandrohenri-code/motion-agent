import React, { useCallback, useRef } from 'react';
import { Plus, Trash2, GripVertical, X, Wand2 } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Badge } from '../shared/Badge';
import { Spinner } from '../shared/Spinner';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const ACCEPTED = '.jpg,.jpeg,.png,.webp,.gif,.tiff,.tif,.bmp,.avif,.heic,.heif,.svg';

const STATUS_BADGE = {
  pending:  <Badge variant="neutral" dot>⏳ Aguardando</Badge>,
  running:  <Badge variant="accent"  dot pulse>🔄 Gerando...</Badge>,
  done:     <Badge variant="success" dot>✅ Concluído</Badge>,
  error:    <Badge variant="error"   dot>❌ Erro</Badge>,
  review:   <Badge variant="warning" dot>👁 Em revisão</Badge>,
};

function FrameCard({ frame, index }) {
  const { updateFrame, removeFrame } = useAppStore();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: frame.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="card" data-card>
      <div style={{ display: 'flex', gap: 0 }}>
        {/* Drag handle */}
        <div
          {...attributes}
          {...listeners}
          style={{
            width: 28, cursor: 'grab', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#44444e', flexShrink: 0,
          }}
        >
          <GripVertical size={14} />
        </div>

        {/* Thumbnail */}
        <div style={{ position: 'relative', width: 100, flexShrink: 0 }}>
          <img
            src={frame.preview}
            alt={`Frame ${index + 1}`}
            style={{ width: '100%', height: 90, objectFit: 'cover' }}
          />
          {/* Scene number badge */}
          <span style={{
            position: 'absolute', top: 6, left: 6,
            background: '#6c63ff', color: '#fff',
            borderRadius: 999, padding: '1px 7px', fontSize: 10, fontWeight: 600,
          }}>
            {index + 1}
          </span>
          {/* Remove button */}
          <button
            onClick={() => removeFrame(frame.id)}
            style={{
              position: 'absolute', top: 4, right: 4,
              background: '#00000080', border: 'none', borderRadius: '50%',
              width: 20, height: 20, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#f0f0f2', transition: 'all 0.15s ease',
            }}
          >
            <X size={11} />
          </button>
        </div>

        {/* Details */}
        <div style={{ flex: 1, padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <span style={{ fontSize: 11, color: '#8a8a9a' }} className="truncate">{frame.name}</span>
            {frame.status && STATUS_BADGE[frame.status]}
          </div>

          <textarea
            className="input"
            style={{ fontSize: 12, minHeight: 50, resize: 'none' }}
            placeholder="Descreva o que acontece nesta cena: texto, animações, elementos visuais..."
            value={frame.description}
            onChange={(e) => updateFrame(frame.id, { description: e.target.value })}
          />

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 11, color: '#8a8a9a', flexShrink: 0 }}>Duração:</label>
            <input
              className="input"
              style={{ width: 70, fontSize: 12, padding: '4px 8px' }}
              type="number"
              min="0.5"
              max="60"
              step="0.5"
              value={frame.duration}
              onChange={(e) => updateFrame(frame.id, { duration: e.target.value })}
            />
            <span style={{ fontSize: 11, color: '#8a8a9a' }}>s</span>
            {frame.status === 'error' && (
              <button className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto', fontSize: 11 }}>
                Retentar
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function FramesTab() {
  const { frames, addFrames, clearFrames, reorderFrames, updateFrame, api } = useAppStore();
  const fileInputRef = useRef(null);
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [autoDescribing, setAutoDescribing] = React.useState(false);

  const sensors = useSensors(useSensor(PointerSensor));

  const processFiles = useCallback(async (files) => {
    const newFrames = [];
    for (const file of files) {
      const url = URL.createObjectURL(file);
      newFrames.push({
        id: `frame-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        name: file.name,
        file,
        preview: url,
        description: '',
        duration: '3',
        status: 'pending',
      });
    }
    addFrames(newFrames);
  }, [addFrames]);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith('image/') || f.name.match(/\.(svg|heic|heif|avif|tiff?|bmp)$/i));
    if (files.length) processFiles(files);
  };

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length) processFiles(files);
    e.target.value = '';
  };

  const handleDragEnd = ({ active, over }) => {
    if (active.id !== over?.id) {
      const oldIndex = frames.findIndex((f) => f.id === active.id);
      const newIndex = frames.findIndex((f) => f.id === over.id);
      reorderFrames(arrayMove(frames, oldIndex, newIndex));
    }
  };

  const handleAutoDescribe = async () => {
    setAutoDescribing(true);
    const apiKey = await window.electronAPI?.loadApiKey(api.provider) || api.apiKey;
    for (const frame of frames) {
      if (!frame.preview) continue;
      try {
        // Get base64 of image for vision model
        const base64 = frame.file
          ? await new Promise((resolve) => {
              const reader = new FileReader();
              reader.onload = (e) => resolve(e.target.result);
              reader.readAsDataURL(frame.file);
            })
          : frame.preview;
        updateFrame(frame.id, { status: 'running' });
        // Call vision API to describe the frame
        const res = await fetch(`https://api.openai.com/v1/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify({
            model: api.visionModel || 'gpt-4o-mini',
            messages: [{
              role: 'user',
              content: [
                { type: 'image_url', image_url: { url: base64 } },
                { type: 'text', text: 'Descreva em 1-2 frases o que deve acontecer nesta cena de vídeo motion graphics. Mencione elementos visuais, texto, animações e estilo. Responda em português.' },
              ],
            }],
            max_tokens: 150,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          const desc = data.choices?.[0]?.message?.content || '';
          updateFrame(frame.id, { description: desc, status: 'pending' });
        } else {
          updateFrame(frame.id, { status: 'pending' });
        }
      } catch {
        updateFrame(frame.id, { status: 'pending' });
      }
    }
    setAutoDescribing(false);
  };

  const totalDuration = frames.reduce((s, f) => s + (parseFloat(f.duration) || 3), 0);

  return (
    <div className="tab-content">
      {/* Drop zone */}
      <div
        className={`drop-zone${isDragOver ? ' drag-over' : ''}`}
        style={{ minHeight: 120, padding: 28 }}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <span className="drop-icon" style={{ fontSize: 28 }}>🖼️</span>
        <span style={{ fontSize: 14, fontWeight: 500, color: '#8a8a9a' }}>
          Arraste imagens aqui ou clique para selecionar
        </span>
        <span style={{ fontSize: 12, color: '#44444e' }}>
          JPG, PNG, WEBP, GIF, TIFF, BMP, AVIF, HEIC, SVG · múltiplos arquivos
        </span>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED}
          style={{ display: 'none' }}
          onChange={handleFileInput}
        />
      </div>

      {/* Action bar */}
      {frames.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => fileInputRef.current?.click()}>
            <Plus size={13} /> Adicionar frame
          </button>
          <button className="btn btn-danger btn-sm" onClick={clearFrames}>
            <Trash2 size={13} /> Limpar tudo
          </button>
          <span style={{ flex: 1, fontSize: 12, color: '#8a8a9a', textAlign: 'center' }}>
            {frames.length} cenas · {totalDuration}s totais
          </span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleAutoDescribe}
            disabled={autoDescribing}
          >
            {autoDescribing ? <Spinner size={12} /> : <Wand2 size={13} />}
            Auto-descrever frames
          </button>
        </div>
      )}

      {/* Frame grid */}
      {frames.length > 0 && (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={frames.map((f) => f.id)} strategy={verticalListSortingStrategy}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {frames.map((frame, i) => (
                <FrameCard key={frame.id} frame={frame} index={i} />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {frames.length === 0 && (
        <div style={{ textAlign: 'center', color: '#44444e', padding: '24px 0', fontSize: 13 }}>
          Adicione imagens acima para começar. Cada imagem representa uma cena do vídeo.
        </div>
      )}
    </div>
  );
}

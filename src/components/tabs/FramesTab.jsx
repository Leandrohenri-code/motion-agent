import React, { useCallback, useRef, useState } from 'react';
import { Plus, Trash2, GripVertical, X, Wand2, Image, Film, Play, ChevronRight } from 'lucide-react';
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

const ACCEPTED_IMAGES = '.jpg,.jpeg,.png,.webp,.gif,.tiff,.tif,.bmp,.avif,.heic,.heif,.svg';
const ACCEPTED_VIDEOS = '.mp4,.mov,.avi,.webm,.mkv,.m4v,.wmv,.flv';

const STATUS_BADGE = {
  pending: <Badge variant="neutral" dot>⏳ Aguardando</Badge>,
  running: <Badge variant="accent"  dot pulse>🔄 Gerando...</Badge>,
  done:    <Badge variant="success" dot>✅ Concluído</Badge>,
  error:   <Badge variant="error"   dot>❌ Erro</Badge>,
  review:  <Badge variant="warning" dot>👁 Em revisão</Badge>,
};

// Extrai thumbnail e duração de um arquivo de vídeo via canvas
function extractVideoMeta(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const video = document.createElement('video');
    video.src = url;
    video.muted = true;
    video.playsInline = true;
    video.currentTime = 0.5;
    video.onloadeddata = () => {
      const canvas = document.createElement('canvas');
      canvas.width = 160;
      canvas.height = 90;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, 160, 90);
      const thumbnail = canvas.toDataURL('image/jpeg', 0.8);
      const duration = isFinite(video.duration) ? Math.round(video.duration * 10) / 10 : 3;
      URL.revokeObjectURL(url);
      resolve({ thumbnail, duration, objectUrl: URL.createObjectURL(file) });
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      resolve({ thumbnail: null, duration: 3, objectUrl: URL.createObjectURL(file) });
    };
  });
}

// ── Card de imagem ───────────────────────────────────────────────────────────

function ImageCard({ frame, index }) {
  const { updateFrame, removeFrame } = useAppStore();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: frame.id });

  return (
    <div ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 }} className="card">
      <div style={{ display: 'flex' }}>
        <div {...attributes} {...listeners} style={{ width: 28, cursor: 'grab', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#44444e', flexShrink: 0 }}>
          <GripVertical size={14} />
        </div>

        {/* Thumbnail */}
        <div style={{ position: 'relative', width: 100, flexShrink: 0 }}>
          <img src={frame.preview} alt={`Cena ${index + 1}`} style={{ width: '100%', height: 90, objectFit: 'cover' }} />
          <span style={{ position: 'absolute', top: 6, left: 6, background: '#6c63ff', color: '#fff', borderRadius: 999, padding: '1px 7px', fontSize: 10, fontWeight: 600 }}>
            {index + 1}
          </span>
          <button onClick={() => removeFrame(frame.id)} style={{ position: 'absolute', top: 4, right: 4, background: '#00000080', border: 'none', borderRadius: '50%', width: 20, height: 20, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f0f0f2' }}>
            <X size={11} />
          </button>
        </div>

        {/* Info */}
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
            <input className="input" style={{ width: 70, fontSize: 12, padding: '4px 8px' }} type="number" min="0.5" max="60" step="0.5" value={frame.duration} onChange={(e) => updateFrame(frame.id, { duration: e.target.value })} />
            <span style={{ fontSize: 11, color: '#8a8a9a' }}>s</span>
            {frame.status === 'error' && <button className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto', fontSize: 11 }}>Retentar</button>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Card de vídeo ────────────────────────────────────────────────────────────

function VideoCard({ frame, index }) {
  const { updateFrame, removeFrame } = useAppStore();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: frame.id });
  const [playing, setPlaying] = useState(false);
  const videoRef = useRef(null);

  const togglePlay = (e) => {
    e.stopPropagation();
    if (!videoRef.current) return;
    if (playing) { videoRef.current.pause(); setPlaying(false); }
    else          { videoRef.current.play();  setPlaying(true);  }
  };

  return (
    <div ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 }} className="card">
      <div style={{ display: 'flex' }}>
        <div {...attributes} {...listeners} style={{ width: 28, cursor: 'grab', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#44444e', flexShrink: 0 }}>
          <GripVertical size={14} />
        </div>

        {/* Thumbnail + player */}
        <div style={{ position: 'relative', width: 100, flexShrink: 0, background: '#0d0d0f' }}>
          {frame.objectUrl ? (
            <video
              ref={videoRef}
              src={frame.objectUrl}
              style={{ width: '100%', height: 90, objectFit: 'cover' }}
              onEnded={() => setPlaying(false)}
              muted
            />
          ) : frame.preview ? (
            <img src={frame.preview} alt="" style={{ width: '100%', height: 90, objectFit: 'cover' }} />
          ) : (
            <div style={{ width: '100%', height: 90, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Film size={24} style={{ color: '#44444e' }} />
            </div>
          )}

          {/* Play/pause overlay */}
          {frame.objectUrl && (
            <button onClick={togglePlay} style={{ position: 'absolute', inset: 0, background: playing ? 'transparent' : '#00000060', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', transition: 'all 0.15s ease' }}>
              {!playing && <Play size={20} style={{ filter: 'drop-shadow(0 1px 4px #000)' }} />}
            </button>
          )}

          {/* Scene badge */}
          <span style={{ position: 'absolute', top: 6, left: 6, background: '#00d4aa', color: '#0d0d0f', borderRadius: 999, padding: '1px 7px', fontSize: 10, fontWeight: 600, pointerEvents: 'none' }}>
            {index + 1}
          </span>

          {/* Duration badge */}
          <span style={{ position: 'absolute', bottom: 6, right: 6, background: '#00000090', color: '#f0f0f2', borderRadius: 4, padding: '1px 5px', fontSize: 10, fontWeight: 500, fontFamily: 'monospace', pointerEvents: 'none' }}>
            {parseFloat(frame.duration) > 0 ? `${parseFloat(frame.duration).toFixed(1)}s` : '—'}
          </span>

          {/* Remove */}
          <button onClick={() => removeFrame(frame.id)} style={{ position: 'absolute', top: 4, right: 4, background: '#00000080', border: 'none', borderRadius: '50%', width: 20, height: 20, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f0f0f2' }}>
            <X size={11} />
          </button>
        </div>

        {/* Info */}
        <div style={{ flex: 1, padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, minWidth: 0 }}>
              <Film size={11} style={{ color: '#00d4aa', flexShrink: 0 }} />
              <span style={{ fontSize: 11, color: '#8a8a9a' }} className="truncate">{frame.name}</span>
            </div>
            {frame.status && STATUS_BADGE[frame.status]}
          </div>

          <textarea
            className="input"
            style={{ fontSize: 12, minHeight: 50, resize: 'none' }}
            placeholder="Descreva o conteúdo deste vídeo: o que aparece, animações, texto, estilo..."
            value={frame.description}
            onChange={(e) => updateFrame(frame.id, { description: e.target.value })}
          />

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 11, color: '#8a8a9a', flexShrink: 0 }}>Duração:</label>
            <input className="input" style={{ width: 70, fontSize: 12, padding: '4px 8px' }} type="number" min="0.1" max="600" step="0.1" value={frame.duration} onChange={(e) => updateFrame(frame.id, { duration: e.target.value })} />
            <span style={{ fontSize: 11, color: '#8a8a9a' }}>s</span>
            <Badge variant="info" style={{ marginLeft: 'auto', fontSize: 10 }}>vídeo</Badge>
            {frame.status === 'error' && <button className="btn btn-secondary btn-sm" style={{ fontSize: 11 }}>Retentar</button>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Componente principal ─────────────────────────────────────────────────────

export function FramesTab() {
  const { frames, addFrames, clearFrames, reorderFrames, updateFrame, api, setActiveTab } = useAppStore();
  const [mode, setMode] = useState('images'); // 'images' | 'videos'
  const [isDragOver, setIsDragOver] = useState(false);
  const [autoDescribing, setAutoDescribing] = useState(false);
  const sensors = useSensors(useSensor(PointerSensor));

  // ── Processar imagens ──────────────────────────────────────────────────────

  const processImageFiles = useCallback(async (files) => {
    // Converte cada File para base64 (necessário para o Python e para preview)
    const newFrames = await Promise.all(files.map((file) => new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve({
          id: `frame-${Date.now()}-${Math.random().toString(36).slice(2)}`,
          mediaType: 'image',
          name: file.name,
          file,
          preview: e.target.result,   // base64 data URL — válido para UI e para o Python
          objectUrl: null,
          description: '',
          duration: '3',
          status: 'pending',
        });
      };
      reader.onerror = () => resolve({
        id: `frame-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        mediaType: 'image',
        name: file.name,
        file,
        preview: URL.createObjectURL(file),
        objectUrl: null,
        description: '',
        duration: '3',
        status: 'pending',
      });
      reader.readAsDataURL(file);
    })));
    addFrames(newFrames);
  }, [addFrames]);

  // Abre dialog nativo do Electron para selecionar múltiplas imagens
  const openNativeImageDialog = useCallback(async () => {
    const paths = await window.electronAPI?.browseFiles({ type: 'images' });
    if (!paths || !paths.length) return;
    const newFrames = await Promise.all(paths.map(async (filePath) => {
      const base64 = await window.electronAPI?.readFileBase64(filePath) || null;
      const name = filePath.split(/[\\/]/).pop();
      return {
        id: `frame-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        mediaType: 'image',
        name,
        file: null,
        preview: base64,
        objectUrl: null,
        description: '',
        duration: '3',
        status: 'pending',
      };
    }));
    addFrames(newFrames.filter((f) => f.preview));
  }, [addFrames]);

  // Abre dialog nativo para vídeos
  const openNativeVideoDialog = useCallback(async () => {
    const paths = await window.electronAPI?.browseFiles({ type: 'videos' });
    if (!paths || !paths.length) return;
    const newFrames = [];
    for (const filePath of paths) {
      const name = filePath.split(/[\\/]/).pop();
      newFrames.push({
        id: `frame-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        mediaType: 'video',
        name,
        file: null,
        preview: null,
        objectUrl: `file://${filePath}`,
        filePath,
        description: '',
        duration: '3',
        status: 'pending',
      });
    }
    addFrames(newFrames);
  }, [addFrames]);

  // ── Processar vídeos ───────────────────────────────────────────────────────

  const processVideoFiles = useCallback(async (files) => {
    const newFrames = [];
    for (const file of files) {
      const { thumbnail, duration, objectUrl } = await extractVideoMeta(file);
      newFrames.push({
        id: `frame-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        mediaType: 'video',
        name: file.name,
        file,
        preview: thumbnail,
        objectUrl,
        description: '',
        duration: String(duration),
        status: 'pending',
      });
    }
    addFrames(newFrames);
  }, [addFrames]);

  // ── Drop handler ───────────────────────────────────────────────────────────

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const allFiles = Array.from(e.dataTransfer.files);
    if (mode === 'images') {
      const imgs = allFiles.filter((f) => f.type.startsWith('image/') || f.name.match(/\.(svg|heic|heif|avif|tiff?|bmp)$/i));
      if (imgs.length) processImageFiles(imgs);
    } else {
      const vids = allFiles.filter((f) => f.type.startsWith('video/') || f.name.match(/\.(mp4|mov|avi|webm|mkv|m4v|wmv|flv)$/i));
      if (vids.length) processVideoFiles(vids);
    }
  };

  const handleDragEnd = ({ active, over }) => {
    if (active.id !== over?.id) {
      const oldIdx = frames.findIndex((f) => f.id === active.id);
      const newIdx = frames.findIndex((f) => f.id === over.id);
      reorderFrames(arrayMove(frames, oldIdx, newIdx));
    }
  };

  // ── Auto-descrever ─────────────────────────────────────────────────────────

  const handleAutoDescribe = async () => {
    setAutoDescribing(true);
    const apiKey = await window.electronAPI?.loadApiKey(api.provider) || api.apiKey;
    for (const frame of frames) {
      try {
        let base64 = null;
        if (frame.mediaType === 'video') {
          // Use o thumbnail do vídeo (primeiro frame extraído)
          base64 = frame.preview;
        } else {
          base64 = frame.file
            ? await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.readAsDataURL(frame.file);
              })
            : frame.preview;
        }
        if (!base64) continue;
        updateFrame(frame.id, { status: 'running' });
        const res = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify({
            model: api.visionModel || 'gpt-4o-mini',
            messages: [{
              role: 'user',
              content: [
                { type: 'image_url', image_url: { url: base64 } },
                { type: 'text', text: `Esta é uma ${frame.mediaType === 'video' ? 'cena de vídeo (frame de referência)' : 'imagem de cena'}. Descreva em 1-2 frases o que deve acontecer nesta cena de vídeo motion graphics. Mencione elementos visuais, texto, animações e estilo. Responda em português.` },
              ],
            }],
            max_tokens: 150,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          updateFrame(frame.id, { description: data.choices?.[0]?.message?.content || '', status: 'pending' });
        } else {
          updateFrame(frame.id, { status: 'pending' });
        }
      } catch {
        updateFrame(frame.id, { status: 'pending' });
      }
    }
    setAutoDescribing(false);
  };

  // ── Totais ─────────────────────────────────────────────────────────────────

  const totalDuration = frames.reduce((s, f) => s + (parseFloat(f.duration) || 3), 0);
  const imgCount   = frames.filter((f) => f.mediaType !== 'video').length;
  const vidCount   = frames.filter((f) => f.mediaType === 'video').length;

  const accept = mode === 'images' ? ACCEPTED_IMAGES : ACCEPTED_VIDEOS;
  const dropIcon = mode === 'images' ? '🖼️' : '🎬';
  const dropLabel = mode === 'images'
    ? 'Arraste imagens aqui ou clique para selecionar'
    : 'Arraste vídeos aqui ou clique para selecionar';
  const dropHint = mode === 'images'
    ? 'JPG, PNG, WEBP, GIF, TIFF, BMP, AVIF, HEIC, SVG · múltiplos arquivos'
    : 'MP4, MOV, AVI, WEBM, MKV, M4V, WMV · múltiplos arquivos';

  return (
    <div className="tab-content">

      {/* ── Mode switcher ── */}
      <div style={{ display: 'flex', background: '#0d0d0f', borderRadius: 10, padding: 3, gap: 2, alignSelf: 'flex-start' }}>
        {[
          { id: 'images', icon: <Image size={14} />, label: 'Imagens' },
          { id: 'videos', icon: <Film size={14} />,  label: 'Vídeos'  },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '7px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 500,
              background: mode === m.id ? (m.id === 'images' ? '#6c63ff' : '#00d4aa') : 'transparent',
              color: mode === m.id ? (m.id === 'images' ? '#fff' : '#0d0d0f') : '#8a8a9a',
              transition: 'all 0.15s ease',
              boxShadow: mode === m.id ? (m.id === 'images' ? '0 2px 12px #6c63ff40' : '0 2px 12px #00d4aa40') : 'none',
            }}
          >
            {m.icon} {m.label}
          </button>
        ))}
      </div>

      {/* ── Descrição do modo ── */}
      <p style={{ fontSize: 12, color: '#44444e', marginTop: -8 }}>
        {mode === 'images'
          ? 'Cada imagem representa uma cena — o agente interpreta o visual e gera a animação correspondente.'
          : 'Cada vídeo representa uma cena de referência — o agente analisa o conteúdo e recria a animação no Remotion.'}
      </p>

      {/* ── Drop zone ── */}
      <div
        className={`drop-zone${isDragOver ? ' drag-over' : ''}`}
        style={{ minHeight: 120, padding: 28 }}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => mode === 'images' ? openNativeImageDialog() : openNativeVideoDialog()}
      >
        <span className="drop-icon" style={{ fontSize: 28 }}>{dropIcon}</span>
        <span style={{ fontSize: 14, fontWeight: 500, color: '#8a8a9a' }}>{dropLabel}</span>
        <span style={{ fontSize: 12, color: '#44444e' }}>{dropHint}</span>
      </div>

      {/* ── Barra de ações ── */}
      {frames.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => mode === 'images' ? openNativeImageDialog() : openNativeVideoDialog()}
          >
            <Plus size={13} /> Adicionar {mode === 'images' ? 'imagem' : 'vídeo'}
          </button>
          <button className="btn btn-danger btn-sm" onClick={clearFrames}>
            <Trash2 size={13} /> Limpar tudo
          </button>

          {/* Totais */}
          <span style={{ flex: 1, fontSize: 12, color: '#8a8a9a', textAlign: 'center' }}>
            {frames.length} cenas · {totalDuration.toFixed(1)}s totais
            {imgCount > 0 && vidCount > 0 && (
              <span style={{ color: '#44444e', marginLeft: 6 }}>
                ({imgCount} img · {vidCount} vid)
              </span>
            )}
          </span>

          <button className="btn btn-secondary btn-sm" onClick={handleAutoDescribe} disabled={autoDescribing}>
            {autoDescribing ? <Spinner size={12} /> : <Wand2 size={13} />}
            Auto-descrever
          </button>
        </div>
      )}

      {/* ── Lista de frames ── */}
      {frames.length > 0 && (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={frames.map((f) => f.id)} strategy={verticalListSortingStrategy}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {frames.map((frame, i) =>
                frame.mediaType === 'video'
                  ? <VideoCard key={frame.id} frame={frame} index={i} />
                  : <ImageCard key={frame.id} frame={frame} index={i} />
              )}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {frames.length === 0 && (
        <div style={{ textAlign: 'center', color: '#44444e', padding: '24px 0', fontSize: 13 }}>
          {mode === 'images'
            ? 'Adicione imagens acima — cada imagem vira uma cena do vídeo.'
            : 'Adicione vídeos acima — cada vídeo vira uma cena do vídeo final.'}
        </div>
      )}

      {/* CTA para o Roteiro */}
      {frames.length > 0 && (
        <button
          onClick={() => setActiveTab('script')}
          style={{
            width: '100%',
            padding: '13px 20px',
            borderRadius: 10,
            border: '1px solid #6c63ff40',
            background: 'linear-gradient(135deg, #6c63ff12, #00d4aa08)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            color: '#f0f0f2',
            fontSize: 14,
            fontWeight: 600,
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'linear-gradient(135deg, #6c63ff25, #00d4aa15)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'linear-gradient(135deg, #6c63ff12, #00d4aa08)'; }}
        >
          Ir para o Roteiro e configurar o prompt
          <ChevronRight size={16} style={{ color: '#6c63ff' }} />
        </button>
      )}
    </div>
  );
}

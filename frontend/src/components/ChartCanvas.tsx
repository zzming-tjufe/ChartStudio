import { useCallback, useRef, useState } from 'react';
import {
  axesRectFromMeta,
  axesToScreen,
  haToAnchor,
  pointToScreen,
  screenToAxes,
  vaToBaseline,
} from '../coords';
import { useEditorStore } from '../store';
import type { Annotation } from '../types';

function parseFill(fill: unknown): string {
  if (fill === false || fill === 'false' || fill === 'none' || fill === 0) return 'none';
  if (typeof fill === 'string') return fill;
  return 'none';
}

export function ChartCanvas() {
  const svg = useEditorStore((s) => s.svg);
  const meta = useEditorStore((s) => s.meta);
  const config = useEditorStore((s) => s.config);
  const selectedId = useEditorStore((s) => s.selectedId);
  const selectAnnotation = useEditorStore((s) => s.selectAnnotation);
  const updateAnnotation = useEditorStore((s) => s.updateAnnotation);

  const overlayRef = useRef<SVGSVGElement>(null);
  const [drag, setDrag] = useState<{
    id: string;
    kind: 'text' | 'rectangle';
    offsetX: number;
    offsetY: number;
  } | null>(null);

  const annotations = config?.annotations ?? [];

  const onPointerDown = useCallback(
    (e: React.PointerEvent, ann: Annotation, kind: 'text' | 'rectangle') => {
      if (!meta || ann.position?.coord !== 'axes') return;
      e.stopPropagation();
      selectAnnotation(ann.id);
      const axes = axesRectFromMeta(meta);
      const pt = axesToScreen(ann.position.x, ann.position.y, axes);
      const rect = overlayRef.current?.getBoundingClientRect();
      if (!rect) return;
      const localX = e.clientX - rect.left;
      const localY = e.clientY - rect.top;
      (e.target as Element).setPointerCapture(e.pointerId);
      setDrag({
        id: ann.id,
        kind,
        offsetX: localX - pt.x,
        offsetY: localY - pt.y,
      });
    },
    [meta, selectAnnotation],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!drag || !meta) return;
      const ann = annotations.find((a) => a.id === drag.id);
      if (!ann?.position) return;
      const axes = axesRectFromMeta(meta);
      const rect = overlayRef.current?.getBoundingClientRect();
      if (!rect) return;

      const localX = e.clientX - rect.left - drag.offsetX;
      const localY = e.clientY - rect.top - drag.offsetY;
      const { x, y } = screenToAxes(localX, localY, axes);

      updateAnnotation(drag.id, {
        position: { ...ann.position, coord: 'axes', x, y },
      });
    },
    [drag, meta, annotations, updateAnnotation],
  );

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    if (drag) {
      try {
        (e.target as Element).releasePointerCapture(e.pointerId);
      } catch {
        /* ignore */
      }
    }
    setDrag(null);
  }, [drag]);

  if (!meta || !svg) {
    return (
      <div className="canvas-empty">
        <p>在左侧输入项目路径并点击「打开配置」</p>
        <p className="muted">预览区将显示 Matplotlib 渲染的 SVG，可拖动 coord=axes 的标注</p>
      </div>
    );
  }

  const axes = axesRectFromMeta(meta);
  const w = meta.canvasWidth;
  const h = meta.canvasHeight;

  return (
    <div className="canvas-wrap" style={{ width: '100%', maxWidth: w, aspectRatio: `${w} / ${h}` }}>
      <div className="base-svg" style={{ width: '100%', height: '100%' }} dangerouslySetInnerHTML={{ __html: svg }} />
      <svg
        ref={overlayRef}
        className="overlay-svg"
        width="100%"
        height="100%"
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="xMidYMid meet"
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        {/* axes 区域参考框（调试/对齐） */}
        <rect
          x={axes.left}
          y={axes.top}
          width={axes.width}
          height={axes.height}
          fill="none"
          stroke="#94a3b8"
          strokeDasharray="4 4"
          pointerEvents="none"
        />

        {annotations.map((ann) => {
          if (ann.type === 'arrow') {
            const p0 = pointToScreen(ann.start, meta, axes);
            const p1 = pointToScreen(ann.end, meta, axes);
            if (!p0 || !p1) return null;
            const color = ann.style?.color ?? '#333333';
            return (
              <g key={ann.id} pointerEvents="none" opacity={0.85}>
                <line
                  x1={p0.x}
                  y1={p0.y}
                  x2={p1.x}
                  y2={p1.y}
                  stroke={color}
                  strokeWidth={ann.style?.line_width ?? 1.5}
                  markerEnd="url(#arrowhead)"
                />
              </g>
            );
          }

          if (ann.type === 'text' && ann.position) {
            const pt = pointToScreen(ann.position, meta, axes);
            if (!pt) {
              return (
                <text key={ann.id} x={12} y={20} fill="#999" fontSize={12}>
                  {ann.id} (非 axes 坐标，只读)
                </text>
              );
            }
            const editable = ann.position.coord === 'axes';
            const selected = ann.id === selectedId;
            const fs = ann.style?.font_size ?? 11;
            return (
              <g key={ann.id}>
                <text
                  x={pt.x}
                  y={pt.y}
                  fill={ann.style?.color ?? '#333333'}
                  fontSize={fs}
                  textAnchor={haToAnchor(ann.style?.ha)}
                  dominantBaseline={vaToBaseline(ann.style?.va)}
                  stroke={selected ? '#2563eb' : 'transparent'}
                  strokeWidth={selected ? 1 : 0}
                  style={{ cursor: editable ? 'move' : 'default', pointerEvents: editable ? 'all' : 'none' }}
                  onPointerDown={(e) => editable && onPointerDown(e, ann, 'text')}
                >
                  {ann.text}
                </text>
              </g>
            );
          }

          if (ann.type === 'rectangle' && ann.position && ann.size) {
            if (ann.position.coord !== 'axes') return null;
            const bl = axesToScreen(ann.position.x, ann.position.y, axes);
            const rw = ann.size.width * axes.width;
            const rh = ann.size.height * axes.height;
            const x = bl.x;
            const y = bl.y - rh;
            const selected = ann.id === selectedId;
            return (
              <rect
                key={ann.id}
                x={x}
                y={y}
                width={rw}
                height={rh}
                fill={parseFill(ann.style?.fill)}
                fillOpacity={ann.style?.alpha ?? 1}
                stroke={selected ? '#2563eb' : ann.style?.edge_color ?? '#333333'}
                strokeWidth={ann.style?.line_width ?? 1}
                opacity={ann.style?.alpha ?? 1}
                style={{ cursor: 'move' }}
                onPointerDown={(e) => onPointerDown(e, ann, 'rectangle')}
              />
            );
          }

          return null;
        })}

        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#E53935" />
          </marker>
        </defs>
      </svg>
    </div>
  );
}

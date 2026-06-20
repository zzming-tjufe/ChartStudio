import { useEditorStore } from '../store';
import type { Annotation } from '../types';

function num(v: unknown, fallback = 0): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export function PropertyPanel() {
  const config = useEditorStore((s) => s.config);
  const selectedId = useEditorStore((s) => s.selectedId);
  const updateAnnotation = useEditorStore((s) => s.updateAnnotation);
  const issues = useEditorStore((s) => s.issues);

  const ann = config?.annotations?.find((a) => a.id === selectedId);

  if (!ann) {
    return <p className="muted">选择一条 annotation 以编辑属性</p>;
  }

  const coord = ann.position?.coord ?? '—';
  const editable = coord === 'axes' && (ann.type === 'text' || ann.type === 'rectangle');

  const patch = (p: Partial<Annotation>) => updateAnnotation(ann.id, p);

  return (
    <div className="props">
      <h3>{ann.id}</h3>
      <p className="muted">
        类型 {ann.type} · 坐标系 {String(coord)}
        {!editable && ' · 只读'}
      </p>

      {ann.type === 'text' && (
        <>
          <label className="cs-label">
            文本
            <input
              className="cs-input"
              value={ann.text ?? ''}
              disabled={!editable}
              onChange={(e) => patch({ text: e.target.value })}
            />
          </label>
          <label>
            x
            <input
              type="number"
              step="0.01"
              value={num(ann.position?.x)}
              disabled={!editable}
              onChange={(e) =>
                patch({ position: { ...ann.position!, coord: 'axes', x: num(e.target.value) } })
              }
            />
          </label>
          <label>
            y
            <input
              type="number"
              step="0.01"
              value={num(ann.position?.y)}
              disabled={!editable}
              onChange={(e) =>
                patch({ position: { ...ann.position!, coord: 'axes', y: num(e.target.value) } })
              }
            />
          </label>
          <label>
            font_size
            <input
              type="number"
              value={num(ann.style?.font_size, 10)}
              disabled={!editable}
              onChange={(e) =>
                patch({ style: { ...ann.style, font_size: num(e.target.value, 10) } })
              }
            />
          </label>
          <label>
            color
            <input
              value={ann.style?.color ?? '#333333'}
              disabled={!editable}
              onChange={(e) => patch({ style: { ...ann.style, color: e.target.value } })}
            />
          </label>
          <label>
            ha
            <select
              value={ann.style?.ha ?? 'center'}
              disabled={!editable}
              onChange={(e) => patch({ style: { ...ann.style, ha: e.target.value } })}
            >
              <option value="left">left</option>
              <option value="center">center</option>
              <option value="right">right</option>
            </select>
          </label>
          <label>
            va
            <select
              value={ann.style?.va ?? 'center'}
              disabled={!editable}
              onChange={(e) => patch({ style: { ...ann.style, va: e.target.value } })}
            >
              <option value="bottom">bottom</option>
              <option value="center">center</option>
              <option value="top">top</option>
            </select>
          </label>
        </>
      )}

      {ann.type === 'rectangle' && (
        <>
          <label>
            x
            <input
              type="number"
              step="0.01"
              value={num(ann.position?.x)}
              disabled={!editable}
              onChange={(e) =>
                patch({ position: { ...ann.position!, coord: 'axes', x: num(e.target.value) } })
              }
            />
          </label>
          <label>
            y
            <input
              type="number"
              step="0.01"
              value={num(ann.position?.y)}
              disabled={!editable}
              onChange={(e) =>
                patch({ position: { ...ann.position!, coord: 'axes', y: num(e.target.value) } })
              }
            />
          </label>
          <label>
            width
            <input
              type="number"
              step="0.01"
              value={num(ann.size?.width)}
              disabled={!editable}
              onChange={(e) =>
                patch({ size: { ...ann.size!, width: num(e.target.value) } })
              }
            />
          </label>
          <label>
            height
            <input
              type="number"
              step="0.01"
              value={num(ann.size?.height)}
              disabled={!editable}
              onChange={(e) =>
                patch({ size: { ...ann.size!, height: num(e.target.value) } })
              }
            />
          </label>
          <label>
            edge_color
            <input
              value={ann.style?.edge_color ?? '#333333'}
              disabled={!editable}
              onChange={(e) => patch({ style: { ...ann.style, edge_color: e.target.value } })}
            />
          </label>
          <label>
            line_width
            <input
              type="number"
              step="0.1"
              value={num(ann.style?.line_width, 1)}
              disabled={!editable}
              onChange={(e) =>
                patch({ style: { ...ann.style, line_width: num(e.target.value, 1) } })
              }
            />
          </label>
          <label>
            alpha
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={num(ann.style?.alpha, 1)}
              disabled={!editable}
              onChange={(e) =>
                patch({ style: { ...ann.style, alpha: num(e.target.value, 1) } })
              }
            />
          </label>
          <label>
            fill
            <input
              value={String(ann.style?.fill ?? 'false')}
              disabled={!editable}
              onChange={(e) => {
                const raw = e.target.value;
                const val = raw === 'false' || raw === 'none' ? false : raw;
                patch({ style: { ...ann.style, fill: val } });
              }}
            />
          </label>
        </>
      )}

      {ann.type === 'arrow' && (
        <p className="muted">arrow 第一版只读展示，暂不支持拖端点。</p>
      )}

      {issues.length > 0 && (
        <div className="issues">
          <h4>校验</h4>
          <ul>
            {issues.map((i, idx) => (
              <li key={idx} className={i.level}>
                [{i.level}] {i.field}: {i.message}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

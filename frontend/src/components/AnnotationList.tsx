import { useEditorStore } from '../store';
import type { Annotation } from '../types';

const EMPTY_ANNOTATIONS: Annotation[] = [];

export function AnnotationList() {
  const config = useEditorStore((s) => s.config);
  const annotations = config?.annotations ?? EMPTY_ANNOTATIONS;
  const selectedId = useEditorStore((s) => s.selectedId);
  const selectAnnotation = useEditorStore((s) => s.selectAnnotation);

  if (!annotations.length) {
    return <p className="muted">暂无 annotations，打开项目后在此列出。</p>;
  }

  return (
    <ul className="ann-list">
      {annotations.map((ann: Annotation) => {
        const coord = ann.position?.coord ?? ann.start?.coord ?? '—';
        const editable = coord === 'axes' && (ann.type === 'text' || ann.type === 'rectangle');
        return (
          <li
            key={ann.id}
            className={ann.id === selectedId ? 'selected' : ''}
            onClick={() => selectAnnotation(ann.id)}
          >
            <strong>{ann.id}</strong>
            <span className="tag">{ann.type}</span>
            <span className="coord">{String(coord)}</span>
            {!editable && <span className="tag readonly">只读</span>}
          </li>
        );
      })}
    </ul>
  );
}

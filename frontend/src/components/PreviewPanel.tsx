import { useEditorStore } from '../store';
import type { ChartConfig } from '../types';
import { ChartCanvas } from './ChartCanvas';

function metaLine(config: ChartConfig | null, projectRoot: string, dirty: boolean, templateName?: string) {
  if (!config) return null;
  const figure = (config.figure ?? {}) as { width?: number; height?: number };
  const exportCfg = (config.export ?? {}) as { dpi?: number };
  const w = figure.width ?? 10;
  const h = figure.height ?? 6;
  const dpi = exportCfg.dpi ?? 150;
  const template = templateName ?? String(config.template_id ?? '—');
  const parts = [
    `模板 ${template}`,
    `画布 ${w}×${h} 英寸`,
    `DPI ${dpi}`,
    projectRoot ? `路径 ${projectRoot}` : '',
    `未保存改动 ${dirty ? '是' : '否'}`,
  ].filter(Boolean);
  return parts.join(' · ');
}

export function PreviewPanel() {
  const config = useEditorStore((s) => s.config);
  const projectInfo = useEditorStore((s) => s.projectInfo);
  const dirty = useEditorStore((s) => s.dirty);
  const loading = useEditorStore((s) => s.loading);
  const error = useEditorStore((s) => s.error);
  const status = useEditorStore((s) => s.status);
  const save = useEditorStore((s) => s.save);
  const render = useEditorStore((s) => s.render);
  const check = useEditorStore((s) => s.check);

  const meta = metaLine(config, projectInfo?.root ?? '', dirty, projectInfo?.templateName);

  return (
    <div className="cs-main-inner">
      <header className="cs-page-header">
        <div className="cs-page-header-left">
          <h1 className="cs-page-title">📊 ChartStudio</h1>
          <p className="cs-caption">Annotation 编辑 · 拖动标注并写回 chart_config.yaml</p>
        </div>
        <div className="cs-page-header-right">
          {config ? (
            dirty ? (
              <span className="cs-badge cs-badge-warn">● 有未保存的修改</span>
            ) : (
              <span className="cs-badge cs-badge-ok">● 配置已同步</span>
            )
          ) : (
            <span className="cs-badge cs-badge-muted">欢迎使用</span>
          )}
        </div>
      </header>

      {dirty && config && (
        <div className="cs-alert cs-alert-warn">您有未保存的标注修改，请记得点击「保存当前配置」。</div>
      )}
      {status && <div className="cs-alert cs-alert-info">最近操作：{status}</div>}
      {error && <div className="cs-alert cs-alert-error">{error}</div>}

      <div className="cs-header-line" />

      <h2 className="cs-subheader">图表实时预览</h2>
      {meta && <p className="cs-meta-line">{meta}</p>}

      <div className="cs-preview-card">
        <ChartCanvas />
      </div>

      <h3 className="cs-section-title-main">操作</h3>
      <div className="cs-action-row">
        <button
          type="button"
          className="cs-btn cs-btn-primary"
          disabled={loading || !config}
          onClick={() => save()}
        >
          保存当前配置{dirty ? ' *' : ''}
        </button>
        <button type="button" className="cs-btn cs-btn-secondary" disabled={loading || !config} onClick={() => render()}>
          重新渲染
        </button>
        <button type="button" className="cs-btn cs-btn-secondary" disabled={loading || !config} onClick={() => check()}>
          校验配置
        </button>
      </div>
      <p className="cs-caption">保存前会调用 config_validator；重新渲染使用 Matplotlib 输出 SVG 底图。</p>
    </div>
  );
}

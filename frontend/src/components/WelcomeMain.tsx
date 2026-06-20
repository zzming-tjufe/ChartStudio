import { useEditorStore } from '../store';
import { OpenProjectPathInput } from './OpenProjectPathInput';

export function WelcomeMain() {
  const projectPath = useEditorStore((s) => s.projectPath);
  const setProjectPath = useEditorStore((s) => s.setProjectPath);
  const openConfig = useEditorStore((s) => s.openConfig);
  const loading = useEditorStore((s) => s.loading);

  return (
    <div className="cs-main-inner">
      <header className="cs-page-header">
        <div className="cs-page-header-left">
          <h1 className="cs-page-title">📊 ChartStudio</h1>
        </div>
        <div className="cs-page-header-right">
          <span className="cs-badge cs-badge-muted">欢迎使用</span>
        </div>
      </header>

      <div className="cs-header-line" />

      <h2 className="cs-subheader">开始制作图表</h2>
      <p className="cs-caption cs-welcome-desc">
        选择模板创建新项目，或打开已有项目。进入编辑界面后可调整标注并导出。
      </p>

      <div className="cs-welcome-grid">
        <div className="cs-bordered-card">
          <OpenProjectPathInput
            path={projectPath}
            onPathChange={setProjectPath}
            onOpen={openConfig}
            loading={loading}
          />
        </div>
        <div className="cs-bordered-card cs-bordered-card-muted">
          <p className="cs-open-heading">
            <strong>新建项目</strong>
          </p>
          <p className="cs-caption">选择模板，填写项目名与保存目录</p>
          <p className="muted">
            新建项目功能请使用 <code>streamlit run app.py</code>。React 原型当前专注于 Annotation 编辑与预览。
          </p>
        </div>
      </div>

      <hr className="cs-divider" />
      <p className="cs-caption">Annotation 原型 · 打开项目后可在侧栏编辑标注并写回 chart_config.yaml</p>
    </div>
  );
}

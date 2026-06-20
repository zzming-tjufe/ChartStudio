import { useState } from 'react';
import { useEditorStore } from '../store';
import { AnnotationList } from './AnnotationList';
import { OpenProjectPathInput } from './OpenProjectPathInput';
import { PropertyPanel } from './PropertyPanel';

type SidebarTab = 'open' | 'new';

export function WelcomeSidebar() {
  const projectPath = useEditorStore((s) => s.projectPath);
  const setProjectPath = useEditorStore((s) => s.setProjectPath);
  const openConfig = useEditorStore((s) => s.openConfig);
  const loading = useEditorStore((s) => s.loading);
  const [tab, setTab] = useState<SidebarTab>('open');

  return (
    <div className="cs-sidebar-inner">
      <h3 className="cs-sidebar-title">开始</h3>
      <p className="cs-caption">创建新项目，或打开已有项目</p>

      <div className="cs-tabs">
        <button type="button" className={`cs-tab${tab === 'open' ? ' active' : ''}`} onClick={() => setTab('open')}>
          打开项目
        </button>
        <button type="button" className={`cs-tab${tab === 'new' ? ' active' : ''}`} onClick={() => setTab('new')}>
          新建项目
        </button>
      </div>

      {tab === 'open' ? (
        <OpenProjectPathInput
          compact
          path={projectPath}
          onPathChange={setProjectPath}
          onOpen={openConfig}
          loading={loading}
        />
      ) : (
        <p className="cs-caption">请在主区域选择图表模板并填写项目信息。</p>
      )}
    </div>
  );
}

export function EditorSidebar() {
  const projectPath = useEditorStore((s) => s.projectPath);
  const setProjectPath = useEditorStore((s) => s.setProjectPath);
  const openConfig = useEditorStore((s) => s.openConfig);
  const closeProject = useEditorStore((s) => s.closeProject);
  const loading = useEditorStore((s) => s.loading);
  const projectInfo = useEditorStore((s) => s.projectInfo);
  const dirty = useEditorStore((s) => s.dirty);

  const [projectOpen, setProjectOpen] = useState(false);
  const [switchTab, setSwitchTab] = useState<'open' | 'new'>('open');

  return (
    <div className="cs-sidebar-inner">
      <h3 className="cs-sidebar-title">调整图表样式</h3>
      <p className="cs-caption">左侧调参 · 右侧实时预览</p>

      <section className="cs-expander">
        <button
          type="button"
          className="cs-expander-head"
          onClick={() => setProjectOpen((v) => !v)}
          aria-expanded={projectOpen}
        >
          <span>项目管理</span>
          <span className="cs-expander-chevron">{projectOpen ? '▾' : '▸'}</span>
        </button>
        {projectOpen && projectInfo && (
          <div className="cs-expander-body">
            <p className="cs-project-name">
              <strong>{projectInfo.displayName}</strong>
            </p>
            <p className="cs-caption">模板：{projectInfo.templateName}</p>
            <p className="cs-caption cs-path-hint">
              <code>{projectInfo.root}</code>
            </p>
            {dirty && <p className="cs-caption cs-warn-text">有未保存的标注修改</p>}

            <div className="cs-tabs cs-tabs-compact">
              <button
                type="button"
                className={`cs-tab${switchTab === 'open' ? ' active' : ''}`}
                onClick={() => setSwitchTab('open')}
              >
                打开其他
              </button>
              <button
                type="button"
                className={`cs-tab${switchTab === 'new' ? ' active' : ''}`}
                onClick={() => setSwitchTab('new')}
              >
                新建
              </button>
            </div>

            {switchTab === 'open' ? (
              <OpenProjectPathInput
                compact
                path={projectPath}
                onPathChange={setProjectPath}
                onOpen={openConfig}
                loading={loading}
              />
            ) : (
              <p className="cs-caption">新建项目请使用 Streamlit 主程序，或于欢迎页主区域操作。</p>
            )}

            <button type="button" className="cs-btn cs-btn-secondary cs-btn-block" disabled={loading} onClick={closeProject}>
              关闭项目
            </button>
          </div>
        )}
      </section>

      <hr className="cs-divider" />

      <h4 className="cs-section-title">Annotations 列表</h4>
      <AnnotationList />

      <hr className="cs-divider" />

      <h4 className="cs-section-title">当前标注属性</h4>
      <PropertyPanel />
    </div>
  );
}

export function Sidebar() {
  const config = useEditorStore((s) => s.config);
  return config ? <EditorSidebar /> : <WelcomeSidebar />;
}

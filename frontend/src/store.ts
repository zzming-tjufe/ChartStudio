import { create } from 'zustand';
import * as api from './api';
import type { Annotation, ChartConfig, RenderMeta, ValidationIssue } from './types';

export interface ProjectInfo {
  root: string;
  displayName: string;
  templateName: string;
  templateId: string;
}

interface EditorState {
  projectPath: string;
  configPath: string;
  projectInfo: ProjectInfo | null;
  config: ChartConfig | null;
  meta: RenderMeta | null;
  svg: string;
  selectedId: string | null;
  dirty: boolean;
  loading: boolean;
  error: string;
  status: string;
  issues: ValidationIssue[];

  openConfig: (path: string) => Promise<void>;
  render: () => Promise<void>;
  save: () => Promise<void>;
  check: () => Promise<void>;
  selectAnnotation: (id: string | null) => void;
  updateAnnotation: (id: string, patch: Partial<Annotation>) => void;
  setProjectPath: (path: string) => void;
  closeProject: () => void;
}

function mergeAnnotation(ann: Annotation, patch: Partial<Annotation>): Annotation {
  const next: Annotation = { ...ann, ...patch };
  if (patch.position) {
    next.position = { ...(ann.position ?? { coord: 'axes', x: 0, y: 0 }), ...patch.position };
  }
  if (patch.style) {
    next.style = { ...ann.style, ...patch.style };
  }
  if (patch.size) {
    next.size = { ...(ann.size ?? { width: 0.1, height: 0.1 }), ...patch.size };
  }
  return next;
}

function patchAnnotationList(config: ChartConfig, id: string, patch: Partial<Annotation>): ChartConfig {
  const list = [...(config.annotations || [])];
  const idx = list.findIndex((a) => a.id === id);
  if (idx < 0) return config;
  list[idx] = mergeAnnotation(list[idx], patch);
  return { ...config, annotations: list };
}

export const useEditorStore = create<EditorState>((set, get) => ({
  projectPath: '',
  configPath: '',
  projectInfo: null,
  config: null,
  meta: null,
  svg: '',
  selectedId: null,
  dirty: false,
  loading: false,
  error: '',
  status: '',
  issues: [],

  setProjectPath: (path) => set({ projectPath: path }),

  closeProject: () =>
    set({
      projectInfo: null,
      config: null,
      configPath: '',
      meta: null,
      svg: '',
      selectedId: null,
      dirty: false,
      error: '',
      status: '',
      issues: [],
    }),

  openConfig: async (path) => {
    set({ loading: true, error: '', status: '正在打开项目…' });
    try {
      const opened = await api.openConfig(path);
      const projectInfo: ProjectInfo = {
        root: opened.project_root,
        displayName: opened.project_name,
        templateName: opened.template_name,
        templateId: opened.template_id,
      };
      set({
        projectPath: opened.project_root,
        configPath: opened.config_path,
        projectInfo,
        config: opened.config,
        meta: opened.meta,
        dirty: false,
        selectedId: opened.config.annotations?.[0]?.id ?? null,
      });
      const rendered = await api.renderChart(opened.config, opened.config_path);
      set({
        svg: rendered.svg,
        meta: rendered.meta,
        loading: false,
        status: opened.message,
      });
    } catch (e) {
      set({ loading: false, error: String(e), status: '' });
    }
  },

  render: async () => {
    const { config, configPath } = get();
    if (!config) return;
    set({ loading: true, error: '', status: '正在渲染…' });
    try {
      const rendered = await api.renderChart(config, configPath || undefined);
      set({
        svg: rendered.svg,
        meta: rendered.meta,
        loading: false,
        dirty: false,
        status: '渲染完成',
      });
    } catch (e) {
      set({ loading: false, error: String(e) });
    }
  },

  save: async () => {
    const { config, configPath } = get();
    if (!config || !configPath) return;
    set({ loading: true, error: '', status: '正在保存…' });
    try {
      const result = await api.saveConfig(configPath, config);
      set({
        loading: false,
        dirty: false,
        status: `已保存：${result.saved}`,
        issues: result.issues,
      });
    } catch (e) {
      set({ loading: false, error: String(e) });
    }
  },

  check: async () => {
    const { config } = get();
    if (!config) return;
    try {
      const result = await api.checkConfig(config);
      set({ issues: result.issues, status: result.blocking ? '校验有错误' : '校验通过' });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  selectAnnotation: (id) => set({ selectedId: id }),

  updateAnnotation: (id, patch) => {
    const { config } = get();
    if (!config) return;
    set({
      config: patchAnnotationList(config, id, patch),
      dirty: true,
    });
  },
}));

import type { ChartConfig, RenderMeta, ValidationIssue } from './types';

const BASE = '/api';

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof detail.detail === 'string' ? detail.detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export async function openConfig(configPath: string) {
  return postJson<{
    config: ChartConfig;
    config_path: string;
    project_root: string;
    template_id: string;
    template_name: string;
    project_name: string;
    message: string;
    meta: RenderMeta;
  }>('/open-config', { config_path: configPath });
}

export async function assessOpenPath(path: string) {
  return postJson<{ status: string; message: string }>('/assess-open-path', { path });
}

export async function pickFolder(title?: string) {
  const res = await postJson<{ path: string | null }>('/pick-folder', { title });
  return res.path;
}

export async function pickConfigFile(title?: string) {
  return postJson<{ path: string | null; project_root: string | null }>('/pick-config-file', { title });
}

export async function renderChart(config: ChartConfig, configPath?: string) {
  return postJson<{
    svg: string;
    meta: RenderMeta;
    figure: { width: number; height: number };
  }>('/render', { config, config_path: configPath });
}

export async function saveConfig(configPath: string, config: ChartConfig) {
  return postJson<{ saved: string; migration_notes: string[]; issues: ValidationIssue[] }>(
    '/save-config',
    { config_path: configPath, config },
  );
}

export async function checkConfig(config: ChartConfig, templateId?: string) {
  return postJson<{
    issues: ValidationIssue[];
    migration_notes: string[];
    blocking: boolean;
  }>('/check', { config, template_id: templateId });
}

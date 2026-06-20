/** 与 core/project_path_input.py 保持一致的客户端校验（拖入文件）。 */

const PROJECT_MARKER_NAMES = new Set(['chart_config.yaml', 'chart_project.yaml', 'chart_core.py']);

export type PathStatus = 'idle' | 'ready' | 'warn' | 'error' | 'validating' | 'valid_drop';

export function validateDroppedProjectFile(
  filename: string,
  content: string,
): { ok: boolean; message: string } {
  const name = filename.toLowerCase();
  if (!PROJECT_MARKER_NAMES.has(name)) {
    return {
      ok: false,
      message: `请拖入 chart_config.yaml、chart_project.yaml 或 chart_core.py（当前：${filename}）`,
    };
  }
  if (name.endsWith('.yaml') || name.endsWith('.yml')) {
    if (!content.trim()) {
      return { ok: false, message: 'YAML 文件为空' };
    }
    if (!/^[\s\S]*:\s*[\s\S]+/m.test(content) && !content.includes(':')) {
      return { ok: false, message: '配置文件内容不是有效的键值结构' };
    }
    return { ok: true, message: `已识别有效的配置文件「${filename}」` };
  }
  if (name === 'chart_core.py') {
    if (!content.includes('def draw_chart')) {
      return { ok: false, message: '该 Python 文件不包含 draw_chart 函数，可能不是 ChartStudio 绘图核心' };
    }
    return { ok: true, message: `已识别有效的绘图核心「${filename}」` };
  }
  return { ok: false, message: '不支持的文件类型' };
}

export function pathStatusIcon(status: PathStatus): string {
  switch (status) {
    case 'ready':
    case 'valid_drop':
      return '✅';
    case 'warn':
    case 'validating':
      return '⚠️';
    case 'error':
      return '❌';
    default:
      return '·';
  }
}

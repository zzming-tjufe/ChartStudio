import type { CoordPoint, RenderMeta } from './types';

export interface AxesRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

export function axesRectFromMeta(meta: RenderMeta): AxesRect {
  return {
    left: meta.left,
    top: meta.top,
    width: meta.width,
    height: meta.height,
  };
}

/** axes 坐标 (0~1, 原点在 axes 左下) → 屏幕/SVG 像素坐标 */
export function axesToScreen(xAxes: number, yAxes: number, axes: AxesRect): { x: number; y: number } {
  return {
    x: axes.left + xAxes * axes.width,
    y: axes.top + (1 - yAxes) * axes.height,
  };
}

/** 屏幕/SVG 像素坐标 → axes 坐标 */
export function screenToAxes(screenX: number, screenY: number, axes: AxesRect): { x: number; y: number } {
  const xAxes = (screenX - axes.left) / axes.width;
  const yAxes = 1 - (screenY - axes.top) / axes.height;
  return { x: clamp01(xAxes), y: clamp01(yAxes) };
}

export function pointToScreen(
  point: CoordPoint | undefined,
  meta: RenderMeta,
  axes: AxesRect,
): { x: number; y: number } | null {
  if (!point) return null;
  const coord = point.coord || 'data';
  if (coord === 'axes') {
    return axesToScreen(point.x, point.y, axes);
  }
  if (coord === 'data' && meta.dataBounds) {
    const b = meta.dataBounds;
    const xAxes = (point.x - b.xMin) / (b.xMax - b.xMin);
    const yAxes = (point.y - b.yMin) / (b.yMax - b.yMin);
    return axesToScreen(xAxes, yAxes, axes);
  }
  return null;
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

export function haToAnchor(ha: string | undefined): 'start' | 'middle' | 'end' {
  if (ha === 'left') return 'start';
  if (ha === 'right') return 'end';
  return 'middle';
}

export function vaToBaseline(va: string | undefined): 'auto' | 'middle' | 'text-before-edge' | 'text-after-edge' {
  if (va === 'top') return 'text-before-edge';
  if (va === 'bottom') return 'text-after-edge';
  return 'middle';
}

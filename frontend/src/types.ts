export type CoordType = 'figure' | 'axes' | 'data';

export interface CoordPoint {
  coord: CoordType;
  x: number;
  y: number;
}

export interface AnnotationStyle {
  font_size?: number;
  color?: string;
  ha?: string;
  va?: string;
  edge_color?: string;
  line_width?: number;
  alpha?: number;
  fill?: boolean | string;
}

export interface AnnotationSize {
  width: number;
  height: number;
}

export interface Annotation {
  id: string;
  type: 'text' | 'arrow' | 'rectangle';
  text?: string;
  position?: CoordPoint;
  start?: CoordPoint;
  end?: CoordPoint;
  size?: AnnotationSize;
  style?: AnnotationStyle;
}

export interface RenderMeta {
  left: number;
  top: number;
  width: number;
  height: number;
  canvasWidth: number;
  canvasHeight: number;
  dpi: number;
  layout: {
    left: number;
    right: number;
    bottom: number;
    top: number;
    use_tight_layout: boolean;
  };
  dataBounds?: {
    xMin: number;
    xMax: number;
    yMin: number;
    yMax: number;
  };
}

export interface ChartConfig {
  schema_version?: number;
  template_id?: string;
  chartstudio_version?: string;
  layout?: Record<string, unknown>;
  figure?: { width?: number; height?: number };
  export?: { dpi?: number; transparent?: boolean; bbox?: string };
  font?: Record<string, unknown>;
  axes?: Record<string, unknown>;
  annotations?: Annotation[];
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ValidationIssue {
  level: string;
  field: string;
  message: string;
}

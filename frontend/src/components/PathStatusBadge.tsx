import type { PathStatus } from '../pathValidation';
import { pathStatusIcon } from '../pathValidation';

interface PathStatusBadgeProps {
  status: PathStatus;
  message: string;
}

export function PathStatusBadge({ status, message }: PathStatusBadgeProps) {
  if (status === 'idle' || !message) return null;
  const cssClass =
    status === 'ready' || status === 'valid_drop'
      ? 'cs-path-ok'
      : status === 'error'
        ? 'cs-path-error'
        : 'cs-path-warn';
  return (
    <div className={cssClass}>
      {pathStatusIcon(status)} {message}
    </div>
  );
}

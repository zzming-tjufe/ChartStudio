import { useCallback, useEffect, useRef, useState } from 'react';
import * as api from '../api';
import type { PathStatus } from '../pathValidation';
import { validateDroppedProjectFile } from '../pathValidation';
import { PathStatusBadge } from './PathStatusBadge';

interface OpenProjectPathInputProps {
  path: string;
  onPathChange: (path: string) => void;
  onOpen: (path: string) => void;
  compact?: boolean;
  loading?: boolean;
}

export function OpenProjectPathInput({
  path,
  onPathChange,
  onOpen,
  compact = false,
  loading = false,
}: OpenProjectPathInputProps) {
  const [pathStatus, setPathStatus] = useState<PathStatus>('idle');
  const [pathMessage, setPathMessage] = useState('');
  const [dropStatus, setDropStatus] = useState<PathStatus>('idle');
  const [dropMessage, setDropMessage] = useState('');
  const [dropMarker, setDropMarker] = useState('chart_config.yaml');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const text = path.trim();
    if (!text) {
      setPathStatus('idle');
      setPathMessage('');
      return;
    }
    let cancelled = false;
    setPathStatus('validating');
    const timer = window.setTimeout(() => {
      api
        .assessOpenPath(text)
        .then((res) => {
          if (!cancelled) {
            setPathStatus(res.status as PathStatus);
            setPathMessage(res.message);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setPathStatus('error');
            setPathMessage('路径校验失败');
          }
        });
    }, 300);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [path]);

  const handleDroppedFile = useCallback(async (file: File) => {
    try {
      const content = await file.text();
      const { ok, message } = validateDroppedProjectFile(file.name, content);
      setDropStatus(ok ? 'valid_drop' : 'error');
      setDropMessage(message);
      if (ok) setDropMarker(file.name);
    } catch {
      setDropStatus('error');
      setDropMessage('无法读取拖入的文件');
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) void handleDroppedFile(file);
    },
    [handleDroppedFile],
  );

  const onBrowseFolder = async () => {
    const picked = await api.pickFolder('选择 ChartStudio 项目文件夹');
    if (picked) onPathChange(picked);
  };

  const onBrowseConfigFile = async () => {
    const result = await api.pickConfigFile('选择 chart_config.yaml 以定位项目');
    if (result.project_root) onPathChange(result.project_root);
  };

  const onLocateFromDrop = async (andOpen: boolean) => {
    const result = await api.pickConfigFile(`选择刚才拖入的 ${dropMarker}`);
    if (!result.project_root) return;
    onPathChange(result.project_root);
    setDropStatus('ready');
    setDropMessage(`已定位项目文件夹：${result.project_root}`);
    if (andOpen) onOpen(result.project_root);
  };

  const onOpenClick = () => {
    if (path.trim()) {
      onOpen(path.trim());
    }
  };

  return (
    <div className="cs-open-project">
      {!compact && (
        <>
          <p className="cs-open-heading">
            <strong>打开已有项目</strong>
          </p>
          <p className="cs-caption">输入文件夹路径、点击浏览，或将 chart_config.yaml 拖入下方区域</p>
        </>
      )}

      <div
        className={`cs-dropzone${dragOver ? ' cs-dropzone-active' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click();
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".yaml,.yml,.py"
          className="cs-dropzone-input"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleDroppedFile(file);
            e.target.value = '';
          }}
        />
        <span className="cs-dropzone-label">拖入项目配置文件</span>
        <span className="cs-dropzone-hint">支持 chart_config.yaml、chart_project.yaml、chart_core.py</span>
      </div>

      {dropStatus === 'valid_drop' && dropMessage && (
        <>
          <PathStatusBadge status={dropStatus} message={dropMessage} />
          <div className="cs-btn-row-2">
            <button type="button" className="cs-btn cs-btn-secondary" disabled={loading} onClick={() => void onLocateFromDrop(false)}>
              定位文件夹并填入路径
            </button>
            <button type="button" className="cs-btn cs-btn-primary cs-btn-inline" disabled={loading} onClick={() => void onLocateFromDrop(true)}>
              定位并打开
            </button>
          </div>
        </>
      )}
      {dropStatus === 'error' && dropMessage && <PathStatusBadge status={dropStatus} message={dropMessage} />}

      <label className={`cs-label${compact ? ' cs-label-compact' : ''}`}>
        {!compact && '项目文件夹'}
        <input
          className="cs-input"
          value={path}
          onChange={(e) => onPathChange(e.target.value)}
          placeholder="D:\projects\my_chart"
        />
      </label>

      <PathStatusBadge status={pathStatus} message={pathMessage} />

      <div className="cs-btn-row-3">
        <button type="button" className="cs-btn cs-btn-secondary" disabled={loading} onClick={() => void onBrowseFolder()}>
          浏览文件夹
        </button>
        <button type="button" className="cs-btn cs-btn-secondary" disabled={loading} onClick={() => void onBrowseConfigFile()}>
          选择配置文件
        </button>
        <button type="button" className="cs-btn cs-btn-primary cs-btn-inline" disabled={loading || !path.trim()} onClick={onOpenClick}>
          打开项目
        </button>
      </div>
    </div>
  );
}

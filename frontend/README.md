# ChartStudio Annotation Editor（React 原型）

验证：**前端拖动 annotation → 写回 chart_config.yaml → Matplotlib 重新渲染后位置一致**。

## 启动

### 1. API 后端（项目根目录）

```bash
pip install -r requirements.txt
uvicorn core.api_server:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

### 3. 打开示例配置

在顶部输入框粘贴绝对路径，例如：

```text
D:/zzmin/Desktop/ChartStudio/examples/v2_annotations_acceptance/chart_config.yaml
```

点击 **打开配置** → 拖动 `coord=axes` 的 text / rectangle → **保存** → **重新渲染**。

## 第一版能力

- 编辑：`text`、`rectangle`（仅 `coord=axes`，可拖动）
- 只读展示：`arrow`（含混合坐标）
- Streamlit 主应用（`streamlit run app.py`）不受影响

## 技术栈

React · TypeScript · Vite · Zustand · SVG 底图 + SVG overlay

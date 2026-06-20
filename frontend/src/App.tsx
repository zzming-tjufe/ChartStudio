import { ErrorBoundary } from './components/ErrorBoundary';
import { PreviewPanel } from './components/PreviewPanel';
import { Sidebar } from './components/Sidebar';
import { WelcomeMain } from './components/WelcomeMain';
import { useEditorStore } from './store';
import './App.css';

function MainArea() {
  const config = useEditorStore((s) => s.config);
  return config ? <PreviewPanel /> : <WelcomeMain />;
}

function App() {
  return (
    <ErrorBoundary>
      <div className="cs-app">
        <aside className="cs-sidebar">
          <Sidebar />
        </aside>
        <main className="cs-main">
          <MainArea />
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('PROJECT LASTLINE Uncaught Error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-ink text-bone flex items-center justify-center p-6">
          <div className="max-w-md w-full p-6 bg-basalt border border-brick/40 rounded-lg space-y-4 shadow-xl">
            <div className="flex items-center space-x-3 text-brick">
              <AlertOctagon className="w-6 h-6" />
              <h2 className="text-base font-bold font-mono">OPERATIONAL PERSPECTIVE ERROR</h2>
            </div>
            <p className="text-xs text-text-muted leading-relaxed">
              An unexpected render fault was caught safely by the control-room error boundary.
              Advisory constraints and underlying EPANET digital twin telemetry remain intact.
            </p>
            {this.state.error && (
              <pre className="p-3 bg-ink-muted text-brick text-[11px] font-mono rounded overflow-x-auto border border-brick/20">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReset}
              className="w-full py-2 bg-sage hover:bg-sage/90 text-white rounded font-mono text-xs font-semibold flex items-center justify-center space-x-2 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>RELOAD CONTROL ROOM CONSOLE</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

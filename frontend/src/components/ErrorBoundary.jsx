import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('DocNest UI Error caught by boundary:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#202326] text-[#BFC3C7] flex items-center justify-center p-6">
          <div className="carbon-card max-w-md w-full p-6 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-950/60 border border-rose-500/50 flex items-center justify-center mx-auto text-rose-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-[#E0E3E5]">Application Render Error</h2>
            <p className="text-xs text-[#969DA3] leading-relaxed">
              An unexpected client-side error occurred in DocNest. You can reload the application
              or return to the dashboard.
            </p>
            {this.state.error && (
              <div className="p-3 bg-[#171A1C] border border-[#555C61] rounded text-[11px] font-mono text-rose-300 text-left overflow-x-auto">
                {this.state.error.message || String(this.state.error)}
              </div>
            )}
            <div className="pt-2">
              <button onClick={this.handleReload} className="btn-primary text-xs py-2 px-4 w-full">
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload Application</span>
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

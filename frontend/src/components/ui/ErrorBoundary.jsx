import React from 'react';
import { AlertTriangle, RefreshCw, Copy, Check } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, copied: false };
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

  handleCopyDiagnostics = () => {
    const errorDetails = `DocNest Error Diagnostic:\n${this.state.error?.stack || this.state.error?.message || String(this.state.error)}\nTimestamp: ${new Date().toISOString()}`;
    navigator.clipboard.writeText(errorDetails);
    this.setState({ copied: true });
    setTimeout(() => this.setState({ copied: false }), 2000);
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#212121] text-[#ECECEC] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-[#2A2A2A] border border-[#3A3A3A] rounded-2xl p-6 text-center space-y-4 shadow-2xl">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto text-rose-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-[#ECECEC]">Application Render Error</h2>
            <p className="text-xs text-[#A1A1A1] leading-relaxed">
              DocNest recovered safely from an unexpected client-side exception. You can reload the workspace or copy error diagnostics.
            </p>
            {this.state.error && (
              <div className="p-3 bg-[#212121] border border-[#3A3A3A] rounded-xl text-[11px] font-mono text-rose-300 text-left overflow-x-auto max-h-36">
                {this.state.error.message || String(this.state.error)}
              </div>
            )}
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={this.handleCopyDiagnostics}
                className="flex-1 py-2 px-3 bg-[#171717] hover:bg-[#2F2F2F] border border-[#3A3A3A] text-[#A1A1A1] hover:text-[#ECECEC] text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition"
              >
                {this.state.copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{this.state.copied ? 'Copied' : 'Diagnostics'}</span>
              </button>
              <button
                onClick={this.handleReload}
                className="flex-1 py-2 px-3 bg-[#F0F0F0] hover:bg-[#FFFFFF] text-[#212121] text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition shadow-sm"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload</span>
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

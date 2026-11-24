import React, { useState } from 'react';
import { LogIn, UserPlus, X, Shield, Lock, Mail, Building, User } from 'lucide-react';
import { loginUser, registerUser } from '../../services/api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [workspaceName, setWorkspaceName] = useState('Default Workspace');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        const res = await registerUser({
          email,
          username: username || email.split('@')[0],
          password,
          workspace_name: workspaceName,
        });
        if (onAuthSuccess) onAuthSuccess(res.user);
      } else {
        const res = await loginUser(email, password);
        if (onAuthSuccess) onAuthSuccess(res.user);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-carbon-deep/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md p-6 bg-carbon-surface border border-silver-border rounded-xl shadow-carbon-lg">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 text-silver-secondary hover:text-silver-light rounded-lg hover:bg-carbon-secondary transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-6">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-carbon-secondary border border-silver-border text-signal-yellow">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-silver-light tracking-wide">
              {isRegister ? 'Create Workspace' : 'Sign in to DocNest'}
            </h2>
            <p className="text-xs text-silver-secondary">
              {isRegister
                ? 'Register your local multi-tenant document workspace'
                : 'Access your private RAG repository & sessions'}
            </p>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 mb-4 text-xs text-red-300 bg-red-950/40 border border-red-800/60 rounded-lg">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-silver-primary mb-1">
              Work Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 w-4 h-4 text-silver-secondary" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@company.com"
                className="w-full pl-9 pr-3 py-2 text-sm bg-carbon-primary border border-silver-border rounded-lg text-silver-light placeholder-silver-secondary/50 focus:outline-none focus:border-signal-yellow"
              />
            </div>
          </div>

          {isRegister && (
            <>
              <div>
                <label className="block text-xs font-medium text-silver-primary mb-1">
                  Full Name / Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 w-4 h-4 text-silver-secondary" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Alex Rivera"
                    className="w-full pl-9 pr-3 py-2 text-sm bg-carbon-primary border border-silver-border rounded-lg text-silver-light placeholder-silver-secondary/50 focus:outline-none focus:border-signal-yellow"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-silver-primary mb-1">
                  Workspace Name
                </label>
                <div className="relative">
                  <Building className="absolute left-3 top-2.5 w-4 h-4 text-silver-secondary" />
                  <input
                    type="text"
                    required
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    placeholder="Engineering Intelligence"
                    className="w-full pl-9 pr-3 py-2 text-sm bg-carbon-primary border border-silver-border rounded-lg text-silver-light placeholder-silver-secondary/50 focus:outline-none focus:border-signal-yellow"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-medium text-silver-primary mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-4 h-4 text-silver-secondary" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 text-sm bg-carbon-primary border border-silver-border rounded-lg text-silver-light placeholder-silver-secondary/50 focus:outline-none focus:border-signal-yellow"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-signal-yellow hover:bg-signal-hover text-carbon-deep font-semibold rounded-lg shadow-carbon-sm transition disabled:opacity-50"
          >
            {loading ? (
              <span className="text-xs">Processing...</span>
            ) : isRegister ? (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Create Workspace</span>
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        {/* Toggle Mode */}
        <div className="mt-5 text-center">
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            className="text-xs text-silver-secondary hover:text-signal-yellow transition"
          >
            {isRegister
              ? 'Already have an account? Sign In'
              : "Don't have a workspace? Register new"}
          </button>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { Sliders, Save, Check, RefreshCw, Zap } from 'lucide-react';
import { fetchUserSettings, updateUserSettings } from '../services/api';

export default function PipelineControlPanel({ onSettingsUpdated }) {
  const [settings, setSettings] = useState({
    chunk_size: 512,
    chunk_overlap: 64,
    top_k: 5,
    min_relevance_score: 0.30,
    temperature: 0.1,
    hybrid_enabled: true,
    reranker_enabled: true,
    preset_name: 'balanced',
  });
  const [loading, setLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const PRESETS = {
    strict: {
      preset_name: 'strict',
      top_k: 3,
      min_relevance_score: 0.50,
      temperature: 0.0,
      chunk_size: 384,
      chunk_overlap: 48,
      hybrid_enabled: true,
      reranker_enabled: true,
    },
    balanced: {
      preset_name: 'balanced',
      top_k: 5,
      min_relevance_score: 0.30,
      temperature: 0.1,
      chunk_size: 512,
      chunk_overlap: 64,
      hybrid_enabled: true,
      reranker_enabled: true,
    },
    deep: {
      preset_name: 'deep',
      top_k: 8,
      min_relevance_score: 0.15,
      temperature: 0.3,
      chunk_size: 768,
      chunk_overlap: 96,
      hybrid_enabled: true,
      reranker_enabled: true,
    },
  };

  const applyPreset = (presetKey) => {
    const p = PRESETS[presetKey];
    if (p) {
      setSettings((prev) => ({ ...prev, ...p }));
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setSavedSuccess(false);
    try {
      const updated = await updateUserSettings(settings);
      setSettings(updated);
      setSavedSuccess(true);
      if (onSettingsUpdated) onSettingsUpdated(updated);
      setTimeout(() => setSavedSuccess(false), 2500);
    } catch (err) {
      console.error('Failed to save pipeline settings:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-carbon-surface border border-silver-border rounded-xl p-6 shadow-carbon-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-signal-yellow" />
          <h3 className="font-semibold text-silver-light text-sm">RAG Pipeline Controls</h3>
        </div>
        <button
          onClick={handleSave}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1 bg-signal-yellow hover:bg-signal-hover text-carbon-deep text-xs font-semibold rounded-lg transition disabled:opacity-50"
        >
          {savedSuccess ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-800" />
              <span>Saved</span>
            </>
          ) : loading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Saving...</span>
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5" />
              <span>Apply</span>
            </>
          )}
        </button>
      </div>

      <p className="text-xs text-silver-secondary">
        Real-time pipeline hyperparameters governing retrieval fusion and generation.
      </p>

      {/* Preset Selector */}
      <div className="grid grid-cols-3 gap-1.5 p-1 bg-carbon-primary border border-silver-border rounded-lg">
        <button
          type="button"
          onClick={() => applyPreset('strict')}
          className={`py-1 text-[11px] font-medium rounded-md transition ${
            settings.preset_name === 'strict'
              ? 'bg-signal-yellow text-carbon-deep font-bold shadow-sm'
              : 'text-silver-secondary hover:text-silver-light'
          }`}
        >
          Strict Fact-Check
        </button>
        <button
          type="button"
          onClick={() => applyPreset('balanced')}
          className={`py-1 text-[11px] font-medium rounded-md transition ${
            settings.preset_name === 'balanced'
              ? 'bg-signal-yellow text-carbon-deep font-bold shadow-sm'
              : 'text-silver-secondary hover:text-silver-light'
          }`}
        >
          Balanced
        </button>
        <button
          type="button"
          onClick={() => applyPreset('deep')}
          className={`py-1 text-[11px] font-medium rounded-md transition ${
            settings.preset_name === 'deep'
              ? 'bg-signal-yellow text-carbon-deep font-bold shadow-sm'
              : 'text-silver-secondary hover:text-silver-light'
          }`}
        >
          Deep Synthesis
        </button>
      </div>

      <div className="space-y-3.5 pt-1 text-xs">
        {/* Top-K Slider */}
        <div>
          <div className="flex justify-between font-mono mb-1">
            <span className="text-silver-secondary">Top-K Passages:</span>
            <span className="text-signal-yellow font-bold">{settings.top_k}</span>
          </div>
          <input
            type="range"
            min="2"
            max="10"
            step="1"
            value={settings.top_k}
            onChange={(e) => setSettings({ ...settings, top_k: parseInt(e.target.value) })}
            className="w-full accent-signal-yellow bg-carbon-primary rounded-lg h-1.5 cursor-pointer"
          />
        </div>

        {/* Min Relevance Score Slider */}
        <div>
          <div className="flex justify-between font-mono mb-1">
            <span className="text-silver-secondary">Min Relevance Score (Abstention):</span>
            <span className="text-signal-yellow font-bold">{Number(settings.min_relevance_score).toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.10"
            max="0.80"
            step="0.05"
            value={settings.min_relevance_score}
            onChange={(e) => setSettings({ ...settings, min_relevance_score: parseFloat(e.target.value) })}
            className="w-full accent-signal-yellow bg-carbon-primary rounded-lg h-1.5 cursor-pointer"
          />
        </div>

        {/* Chunk Size & Overlap */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <div>
            <label className="block text-silver-secondary font-mono mb-1">Chunk Size (chars)</label>
            <input
              type="number"
              min="256"
              max="1024"
              step="64"
              value={settings.chunk_size}
              onChange={(e) => setSettings({ ...settings, chunk_size: parseInt(e.target.value) || 512 })}
              className="w-full px-2.5 py-1.5 bg-carbon-primary border border-silver-border rounded-lg text-silver-light font-mono focus:border-signal-yellow focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-silver-secondary font-mono mb-1">Overlap (chars)</label>
            <input
              type="number"
              min="16"
              max="256"
              step="16"
              value={settings.chunk_overlap}
              onChange={(e) => setSettings({ ...settings, chunk_overlap: parseInt(e.target.value) || 64 })}
              className="w-full px-2.5 py-1.5 bg-carbon-primary border border-silver-border rounded-lg text-silver-light font-mono focus:border-signal-yellow focus:outline-none"
            />
          </div>
        </div>

        {/* Toggles */}
        <div className="pt-2 border-t border-silver-border/60 space-y-2">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-silver-primary">BM25 + Dense Hybrid Search</span>
            <input
              type="checkbox"
              checked={settings.hybrid_enabled}
              onChange={(e) => setSettings({ ...settings, hybrid_enabled: e.target.checked })}
              className="accent-signal-yellow rounded"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-silver-primary">Cross-Encoder Reranker</span>
            <input
              type="checkbox"
              checked={settings.reranker_enabled}
              onChange={(e) => setSettings({ ...settings, reranker_enabled: e.target.checked })}
              className="accent-signal-yellow rounded"
            />
          </label>
        </div>
      </div>
    </div>
  );
}

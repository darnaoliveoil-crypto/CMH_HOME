import { useState } from 'react';
import { Eye, EyeOff, Loader2, Zap } from 'lucide-react';

export function AuthBackground({ children }) {
  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#020d0d] font-sans flex items-center justify-center px-4 py-10">
      <div
        className="pointer-events-none absolute -top-32 -left-32 h-[420px] w-[420px] rounded-full opacity-70"
        style={{
          background: 'radial-gradient(circle, #00b4a6 0%, transparent 70%)',
        }}
      />
      <div
        className="pointer-events-none absolute -bottom-40 -right-24 h-[500px] w-[500px] rounded-full opacity-60"
        style={{
          background: 'radial-gradient(circle, #007a8a 0%, transparent 70%)',
        }}
      />
      <div
        className="pointer-events-none absolute top-1/3 -right-20 h-[360px] w-[360px] rounded-full opacity-40"
        style={{
          background: 'radial-gradient(circle, #00b4a6 0%, transparent 65%)',
        }}
      />
      <div
        className="pointer-events-none absolute bottom-1/4 left-1/4 h-[280px] w-[280px] rounded-full opacity-35"
        style={{
          background: 'radial-gradient(circle, #007a8a 0%, transparent 65%)',
        }}
      />
      {children}
    </div>
  );
}

export function GlassCard({ children }) {
  return (
    <div
      className="auth-glass-card relative z-10 w-full max-w-[420px] shrink-0"
      style={{
        padding: '48px 40px',
      }}
    >
      {children}
    </div>
  );
}

export function GlassBrandLogo() {
  return (
    <div className="flex flex-col items-center gap-3 mb-8">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#00c9b1] to-[#0099cc] shadow-lg shadow-[#00ffdc]/20">
        <Zap className="h-6 w-6 text-white" strokeWidth={2.5} />
      </div>
      <span
        className="text-sm font-bold text-white uppercase"
        style={{ letterSpacing: '4px' }}
      >
        Check My Hits
      </span>
    </div>
  );
}

export function GlassField({
  id,
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  required = true,
  showToggle = false,
}) {
  const [visible, setVisible] = useState(false);
  const inputType = showToggle ? (visible ? 'text' : 'password') : type;

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm text-white">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={inputType}
          required={required}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="auth-glass-input w-full rounded-lg border border-[rgba(0,255,220,0.3)] bg-[rgba(0,0,0,0.3)] px-4 py-3 text-sm text-white placeholder:text-white/35 focus:outline-none transition-shadow"
        />
        {showToggle && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors"
            aria-label={visible ? 'Hide password' : 'Show password'}
          >
            {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
    </div>
  );
}

export function GlassButton({ children, loading, type = 'submit' }) {
  return (
    <button
      type={type}
      disabled={loading}
      className="auth-glass-btn w-full rounded-lg py-3.5 text-lg font-bold text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      style={{
        background: 'linear-gradient(to right, #00c9b1, #0099cc)',
      }}
    >
      {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : children}
    </button>
  );
}

export function AuthError({ message }) {
  if (!message) return null;
  return (
    <div className="rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2.5 text-sm text-red-300">
      {message}
    </div>
  );
}

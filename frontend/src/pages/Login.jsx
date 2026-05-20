import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, Loader2, LogIn, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLocale } from '../context/LocaleContext';

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const { t } = useLocale();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/lifecycle';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || t('auth.loginFailed'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1e2327] px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 mb-4">
            <Zap className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[#e2e8f0]">{t('appName')}</h1>
          <p className="text-sm text-[#94a3b8] mt-1">{t('auth.loginTitle')}</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-[#2a2f45] bg-[#1a1d2e] p-8 shadow-xl space-y-5"
        >
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-[#94a3b8]">{t('auth.email')}</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-[#2a2f45] bg-[#0f1117] px-4 py-2.5 text-sm text-[#e2e8f0] focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              placeholder="admin@checkmyhits.io"
            />
          </label>

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-[#94a3b8]">{t('auth.password')}</span>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-[#2a2f45] bg-[#0f1117] px-4 py-2.5 text-sm text-[#e2e8f0] focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            />
          </label>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-medium py-2.5 transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
            {t('auth.signIn')}
          </button>

          <p className="text-center text-sm text-[#94a3b8]">
            {t('auth.noAccount')}{' '}
            <Link to="/register" className="text-blue-400 hover:text-blue-300 font-medium">
              {t('auth.registerLink')}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

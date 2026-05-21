import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLocale } from '../context/LocaleContext';
import {
  AuthBackground,
  AuthError,
  GlassBrandLogo,
  GlassButton,
  GlassCard,
  GlassField,
} from '../components/auth/authUi';

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
    <AuthBackground>
      <GlassCard>
        <GlassBrandLogo />

        <h1 className="text-center text-[28px] font-semibold text-white mb-8">Welcome Back</h1>

        <form onSubmit={handleSubmit} className="space-y-5">
          <AuthError message={error} />

          <GlassField
            id="login-email"
            label="Email address"
            type="email"
            placeholder="example@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <GlassField
            id="login-password"
            label="Password"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            showToggle
          />

          <button
            type="button"
            className="block text-sm text-white hover:text-[#00ffdc] transition-colors"
          >
            Forgot Password?
          </button>

          <GlassButton loading={loading}>Login</GlassButton>
        </form>

        <p className="text-center text-sm text-white mt-8">
          Are You New Member?{' '}
          <Link
            to="/register"
            className="font-bold text-[#00ffdc] hover:text-[#00c9b1] transition-colors"
          >
            Sign Up
          </Link>
        </p>
      </GlassCard>
    </AuthBackground>
  );
}

import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
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

export default function Register() {
  const { register, isAuthenticated } = useAuth();
  const { t } = useLocale();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/lifecycle" replace />;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError(t('auth.passwordMismatch'));
      return;
    }
    if (password.length < 6) {
      setError(t('auth.passwordShort'));
      return;
    }
    setLoading(true);
    try {
      await register(name.trim(), email.trim(), password);
      navigate('/lifecycle', { replace: true });
    } catch (err) {
      setError(err.message || t('auth.registerFailed'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthBackground>
      <GlassCard>
        <GlassBrandLogo />

        <h1 className="text-center text-[28px] font-semibold text-white mb-8">Create Account</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <AuthError message={error} />

          <GlassField
            id="register-name"
            label="Full name"
            placeholder="Jane Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <GlassField
            id="register-email"
            label="Email address"
            type="email"
            placeholder="example@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <GlassField
            id="register-password"
            label="Password"
            placeholder="At least 6 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            showToggle
          />

          <GlassField
            id="register-confirm"
            label="Confirm password"
            placeholder="Repeat password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            showToggle
          />

          <div className="pt-2">
            <GlassButton loading={loading}>Create Account</GlassButton>
          </div>
        </form>

        <p className="text-center text-sm text-white mt-8">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-bold text-[#00ffdc] hover:text-[#00c9b1] transition-colors"
          >
            Sign In
          </Link>
        </p>
      </GlassCard>
    </AuthBackground>
  );
}

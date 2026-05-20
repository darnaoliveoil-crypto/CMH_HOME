import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';

try {
  const theme = localStorage.getItem('cmh-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  const locale = localStorage.getItem('cmh-locale') || 'en';
  document.documentElement.lang = locale;
  document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr';
} catch {
  document.documentElement.setAttribute('data-theme', 'dark');
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

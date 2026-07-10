import React from 'react';
import ReactDOM from 'react-dom/client';
import {BrowserRouter} from 'react-router-dom';
import App from './App';
import {ToastProvider} from './components/ui';
import './styles.css';

// Apply persisted theme before first paint.
document.documentElement.setAttribute('data-theme', localStorage.getItem('autotube_theme') ?? 'dark');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <App />
      </ToastProvider>
    </BrowserRouter>
  </React.StrictMode>
);

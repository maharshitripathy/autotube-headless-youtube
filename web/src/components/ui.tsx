import React, {createContext, useCallback, useContext, useEffect, useState} from 'react';

/* ------------------------------------------------------------------ Toasts */

type ToastKind = 'success' | 'error' | 'info';
interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastCtx {
  push: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastCtx>({push: () => undefined});

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({children}: {children: React.ReactNode}) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((message: string, kind: ToastKind = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, {id, kind, message}]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{push}}>
      {children}
      <div className="toast-stack">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.kind}`} onClick={() => setToasts((x) => x.filter((y) => y.id !== t.id))}>
            <span className="toast-icon">{t.kind === 'success' ? '✓' : t.kind === 'error' ? '✕' : 'ℹ'}</span>
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

/* ----------------------------------------------------------------- Spinner */

export function Spinner({size = 20}: {size?: number}) {
  return <span className="spinner" style={{width: size, height: size}} aria-label="loading" />;
}

export function Loading({label = 'Loading…'}: {label?: string}) {
  return (
    <div className="loading-row">
      <Spinner /> <span className="muted">{label}</span>
    </div>
  );
}

/* ---------------------------------------------------------------- Skeleton */

export function Skeleton({height = 16, width = '100%', style}: {height?: number | string; width?: number | string; style?: React.CSSProperties}) {
  return <div className="skeleton" style={{height, width, ...style}} />;
}

export function SkeletonCards({count = 4}: {count?: number}) {
  return (
    <div className="grid">
      {Array.from({length: count}).map((_, i) => (
        <div className="card" key={i}>
          <Skeleton height={22} width="60%" />
          <div style={{height: 10}} />
          <Skeleton height={14} width="90%" />
          <div style={{height: 8}} />
          <Skeleton height={14} width="40%" />
        </div>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------- EmptyState */

export function EmptyState({icon = '📭', title, hint, action}: {icon?: string; title: string; hint?: string; action?: React.ReactNode}) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      {hint && <p className="muted">{hint}</p>}
      {action && <div style={{marginTop: 14}}>{action}</div>}
    </div>
  );
}

/* ------------------------------------------------------------- PageHeader */

export function PageHeader({title, subtitle, actions}: {title: string; subtitle?: string; actions?: React.ReactNode}) {
  return (
    <div className="page-header">
      <div>
        <h2>{title}</h2>
        {subtitle && <p className="muted" style={{margin: '2px 0 0'}}>{subtitle}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </div>
  );
}

/* -------------------------------------------------------------------- Stat */

export function Stat({label, value, tone}: {label: string; value: React.ReactNode; tone?: 'good' | 'bad'}) {
  return (
    <div className="card stat-card">
      <div className="stat" style={{color: tone === 'good' ? 'var(--good)' : tone === 'bad' ? 'var(--bad)' : undefined}}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

/* ------------------------------------------------------------------- Modal */

export function Modal({open, title, onClose, children, width = 520}: {open: boolean; title?: string; onClose: () => void; children: React.ReactNode; width?: number}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" style={{width}} onClick={(e) => e.stopPropagation()}>
        {title && (
          <div className="modal-head">
            <strong>{title}</strong>
            <button className="icon-btn" onClick={onClose}>✕</button>
          </div>
        )}
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ Drawer */

export function Drawer({open, title, onClose, children, width = 480}: {open: boolean; title?: string; onClose: () => void; children: React.ReactNode; width?: number}) {
  return (
    <div className={`drawer-root ${open ? 'open' : ''}`} onClick={onClose}>
      <div className="drawer" style={{width}} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <strong>{title}</strong>
          <button className="icon-btn" onClick={onClose}>✕</button>
        </div>
        <div className="drawer-body">{children}</div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------- StatusBadge */

const STATUS_TONE: Record<string, string> = {
  completed: 'ok', published: 'ok', ready: 'ok', approved: 'ok', posted: 'ok',
  awaiting_approval: 'warn', running: 'info', scheduled: 'info', pending: '',
  failed: 'bad', rejected: 'bad',
};

export function StatusBadge({status}: {status: string}) {
  return <span className={`badge ${STATUS_TONE[status] ?? ''}`}>{status.replace(/_/g, ' ')}</span>;
}

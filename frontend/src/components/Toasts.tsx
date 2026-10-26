import { AnimatePresence, LazyMotion, domAnimation, m } from "motion/react";
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { Icon } from "./Icon";

interface Toast {
  id: number;
  title: string;
  description?: string;
}

type Notify = (title: string, description?: string) => void;

const ToastContext = createContext<Notify>(() => {});

const VISIBLE_MS = 4_000;

/** Короткие подтверждения успешных команд. Ошибки остаются в блоке, где они произошли. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const notify = useCallback<Notify>(
    (title, description) => {
      const id = nextId.current++;
      setToasts((current) => [...current.slice(-2), { id, title, description }]);
      window.setTimeout(() => dismiss(id), VISIBLE_MS);
    },
    [dismiss],
  );

  const value = useMemo(() => notify, [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <LazyMotion features={domAnimation} strict>
        <div className="toast-region" role="status" aria-live="polite">
          <AnimatePresence initial={false}>
            {toasts.map((toast) => (
              <m.div
                key={toast.id}
                className="toast"
                initial={{ opacity: 0, y: 16, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, transition: { duration: 0.15 } }}
                transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                onClick={() => dismiss(toast.id)}
              >
                <Icon name="check" />
                <span className="toast-text">
                  <strong>{toast.title}</strong>
                  {toast.description ? <span className="small">{toast.description}</span> : null}
                </span>
              </m.div>
            ))}
          </AnimatePresence>
        </div>
      </LazyMotion>
    </ToastContext.Provider>
  );
}

export function useToast(): Notify {
  return useContext(ToastContext);
}

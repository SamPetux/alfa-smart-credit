import { useEffect, useRef, type FormEvent, type ReactNode } from "react";
import { Button } from "./Button";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  /** Что произойдёт после подтверждения — словами, без двусмысленности. */
  description: ReactNode;
  confirmLabel: string;
  busy?: boolean;
  tone?: "primary" | "danger";
  confirmDisabled?: boolean;
  error?: ReactNode;
  children?: ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Подтверждение необратимого действия на нативном <dialog>: фокус и Esc из коробки. */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  busy = false,
  tone = "primary",
  confirmDisabled = false,
  error,
  children,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }
    if (!open && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
    }
  }, [open]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!busy && !confirmDisabled) onConfirm();
  }

  return (
    <dialog
      ref={ref}
      className="dialog"
      aria-labelledby="confirm-dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onCancel();
      }}
    >
      {open ? (
        <form className="dialog-body stack" onSubmit={submit}>
          <h2 id="confirm-dialog-title">{title}</h2>
          <div className="muted">{description}</div>
          {children}
          {error ? <div role="alert">{error}</div> : null}
          <div className="dialog-actions">
            <Button onClick={onCancel} disabled={busy}>
              Отмена
            </Button>
            <Button type="submit" variant={tone} busy={busy} disabled={confirmDisabled}>
              {confirmLabel}
            </Button>
          </div>
        </form>
      ) : null}
    </dialog>
  );
}

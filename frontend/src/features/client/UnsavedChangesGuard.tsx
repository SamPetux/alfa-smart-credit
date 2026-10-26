import { useEffect } from "react";
import { useBlocker } from "react-router";
import { ConfirmDialog } from "../../components/ConfirmDialog";

/** Предупреждение при уходе с несохранёнными правками: внутри приложения и при закрытии вкладки. */
export function UnsavedChangesGuard({ when }: { when: boolean }) {
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) => when && currentLocation.pathname !== nextLocation.pathname,
  );

  useEffect(() => {
    if (!when) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [when]);

  return (
    <ConfirmDialog
      open={blocker.state === "blocked"}
      title="Уйти без сохранения?"
      description="Изменения не отправлены на сервер и будут потеряны."
      confirmLabel="Уйти без сохранения"
      tone="danger"
      onConfirm={() => blocker.proceed?.()}
      onCancel={() => blocker.reset?.()}
    />
  );
}

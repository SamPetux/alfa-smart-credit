import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link, type LinkProps } from "react-router";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  /** Команда выполняется: кнопка недоступна, текст сообщает о процессе. */
  busy?: boolean;
  busyLabel?: string;
  children: ReactNode;
}

export function Button({
  variant = "secondary",
  busy = false,
  busyLabel,
  disabled,
  children,
  type = "button",
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={["btn", `btn-${variant}`, className].filter(Boolean).join(" ")}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      {...rest}
    >
      {busy ? (busyLabel ?? "Выполняется…") : children}
    </button>
  );
}

export function ButtonLink({ variant = "secondary", className, ...rest }: LinkProps & { variant?: Variant }) {
  return <Link className={["btn", `btn-${variant}`, className].filter(Boolean).join(" ")} {...rest} />;
}

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link, type LinkProps } from "react-router";

type Variant = "primary" | "secondary" | "dark" | "ghost" | "danger" | "on-dark" | "outline-dark";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  /** Команда выполняется: кнопка недоступна, текст сообщает о процессе. */
  busy?: boolean;
  busyLabel?: string;
  size?: "regular" | "large";
  children: ReactNode;
}

export function Button({
  variant = "secondary",
  busy = false,
  busyLabel,
  size = "regular",
  disabled,
  children,
  type = "button",
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={["btn", `btn-${variant}`, size === "large" ? "btn-large" : null, className].filter(Boolean).join(" ")}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      {...rest}
    >
      {busy ? (busyLabel ?? "Выполняется…") : children}
    </button>
  );
}

export function ButtonLink({
  variant = "secondary",
  size = "regular",
  className,
  ...rest
}: LinkProps & { variant?: Variant; size?: "regular" | "large" }) {
  return (
    <Link
      className={["btn", `btn-${variant}`, size === "large" ? "btn-large" : null, className].filter(Boolean).join(" ")}
      {...rest}
    />
  );
}

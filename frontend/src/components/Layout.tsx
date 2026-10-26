import type { ReactNode } from "react";
import { Link } from "react-router";
import { Icon } from "./Icon";

export function PageHeader({
  title,
  backTo,
  backLabel,
  meta,
  actions,
}: {
  title: ReactNode;
  backTo?: string;
  backLabel?: string;
  meta?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      {backTo ? (
        <Link to={backTo} className="back-link small">
          <Icon name="back" /> {backLabel ?? "Назад"}
        </Link>
      ) : null}
      <div className="page-header-row">
        <div className="stack-tight">
          <h1>{title}</h1>
          {meta ? <div className="page-meta small muted">{meta}</div> : null}
        </div>
        {actions ? <div className="page-actions">{actions}</div> : null}
      </div>
    </header>
  );
}

export function Panel({
  title,
  aside,
  children,
  id,
}: {
  title?: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  id?: string;
}) {
  const headingId = id ? `${id}-title` : undefined;
  return (
    <section className="panel" aria-labelledby={headingId} id={id}>
      {title ? (
        <div className="panel-head">
          <h2 id={headingId}>{title}</h2>
          {aside}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export interface KeyValueItem {
  label: ReactNode;
  value: ReactNode;
  numeric?: boolean;
  note?: ReactNode;
}

/** Пары «подпись — значение»; числа выровнены по правому краю табличными цифрами. */
export function KeyValueList({ items }: { items: KeyValueItem[] }) {
  return (
    <dl className="kv">
      {items.map((item, index) => (
        <div className="kv-row" key={index}>
          <dt>{item.label}</dt>
          <dd className={item.numeric ? "num kv-num" : undefined}>
            {item.value}
            {item.note ? <span className="kv-note small muted">{item.note}</span> : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}

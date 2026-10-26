import { Icon } from "./Icon";

/**
 * Демонстрационный документ для ознакомления. Текст выводится как есть (без HTML),
 * hash показан, чтобы клиент подтверждал именно эту версию.
 */
export function DocumentView({ title, text, contentHash }: { title: string; text: string; contentHash: string }) {
  return (
    <figure className="document">
      <figcaption className="document-head">
        <Icon name="file" />
        <span>{title}</span>
        <span className="document-stamp small">Имитация, не юридический документ</span>
      </figcaption>
      <pre className="document-body" tabIndex={0} aria-label={`Текст документа: ${title}`}>
        {text}
      </pre>
      <p className="document-hash small muted">
        Контрольная сумма SHA-256: <code className="hash">{contentHash}</code>
      </p>
    </figure>
  );
}

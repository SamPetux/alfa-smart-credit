/** Небольшой авторский набор контурных иконок 16px, обводка 1.5px. */
const PATHS = {
  alert: "M8 1.75 14.5 13.5H1.5L8 1.75ZM8 6v3.5M8 11.25v.01",
  check: "m3 8.5 3.25 3L13 4.5",
  info: "M8 14.25A6.25 6.25 0 1 0 8 1.75a6.25 6.25 0 0 0 0 12.5ZM8 7.25v4M8 4.75v.01",
  back: "M10 3 5 8l5 5",
  chevron: "m6 3 5 5-5 5",
  file: "M4 1.75h5L12.5 5.25v9H4v-12.5ZM9 1.75v3.5h3.5",
  clock: "M8 14.25A6.25 6.25 0 1 0 8 1.75a6.25 6.25 0 0 0 0 12.5ZM8 4.5V8l2.5 1.5",
  refresh: "M13.25 8A5.25 5.25 0 1 1 11.7 4.3M13.25 2.5v2.75H10.5",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, label }: { name: IconName; label?: string }) {
  return (
    <svg
      className="icon"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}

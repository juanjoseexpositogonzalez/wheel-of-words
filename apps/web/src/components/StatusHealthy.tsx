import type { JSX } from "react";

interface StatusHealthyProps {
  service: string;
  version: string;
  timestamp: string;
}

export function StatusHealthy({ service, version, timestamp }: StatusHealthyProps): JSX.Element {
  return (
    <section aria-live="polite">
      <p>Backend disponible</p>
      <p>{`${service} · ${version}`}</p>
      <time dateTime={timestamp}>{timestamp}</time>
    </section>
  );
}

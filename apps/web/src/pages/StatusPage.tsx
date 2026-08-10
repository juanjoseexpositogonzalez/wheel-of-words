import { useEffect, useState, type JSX } from "react";
import { fetchHealth } from "../api/client";
import { StatusError } from "../components/StatusError";
import { StatusHealthy } from "../components/StatusHealthy";
import { StatusLoading } from "../components/StatusLoading";
import type { HealthResponse } from "../types/health";

type Status =
  | { kind: "loading" }
  | { kind: "healthy"; health: HealthResponse }
  | { kind: "error"; message: string };

export function StatusPage(): JSX.Element {
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let active = true;
    void fetchHealth().then(
      (health) => active && setStatus({ kind: "healthy", health }),
      (error: unknown) =>
        active && setStatus({ kind: "error", message: error instanceof Error ? error.message : "Unknown error" }),
    );
    return () => {
      active = false;
    };
  }, [retryCount]);

  if (status.kind === "healthy") {
    return <StatusHealthy {...status.health} />;
  }
  if (status.kind === "error") {
    return <StatusError message={status.message} onRetry={() => setRetryCount((count) => count + 1)} />;
  }
  return <StatusLoading />;
}

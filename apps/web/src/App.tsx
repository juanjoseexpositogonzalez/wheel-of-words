import React from "react";
import { ImportPage } from "./pages/ImportPage";
import { StatusPage } from "./pages/StatusPage";

export default function App(): React.JSX.Element {
  return (
    <main className="status-page">
      <h1>Wheel Vocabulary</h1>
      <StatusPage />
      <ImportPage />
    </main>
  );
}

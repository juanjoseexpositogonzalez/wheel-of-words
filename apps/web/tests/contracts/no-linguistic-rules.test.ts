import { describe, expect, it } from "vitest";

/**
 * AC-002-19 / design §11 — the frontend duplicates no linguistic rules.
 *
 * A repo-wide search over `apps/web/src/` would false-positive the day someone
 * sorts an unrelated dropdown. This pinned, cut-scoped manifest is the
 * mechanism that keeps the search scoped to import/frequency-table code
 * without abandoning the flat `pages/components/api/types` layout.
 *
 * The manifest is cut-scoped: it lists the modules that exist in the current
 * cut. Cut 3 (T309) appends `DeleteImportButton.tsx` here — see design §11's
 * "cut-scoped manifest" reading.
 *
 * Uses `import.meta.glob` rather than `node:fs` so this file needs no
 * `@types/node`, matching this project's existing minimal-dependency
 * convention (see the manual `declare const process` in `vitest.config.ts`
 * and `playwright.config.ts`).
 */
const IMPORT_FEATURE_MODULES = [
  "src/pages/ImportPage.tsx",
  "src/components/ImportForm.tsx",
  "src/components/FrequencyTable.tsx",
  "src/components/DeleteImportButton.tsx",
  "src/api/imports.ts",
  "src/types/imports.ts",
] as const;

const FEATURE_NAME_PATTERN = /[Ii]mport|[Ff]requenc/;
const FORBIDDEN_PATTERN = /\.sort\(|toLowerCase\(|localeCompare\(|normalize\(|NFC|NFD|NFKC|NFKD/;

// Eagerly loaded raw source text for every TS/TSX file in `src/`, keyed by a
// glob-relative path such as "../../src/pages/ImportPage.tsx".
const rawSourceModules: Record<string, string> = import.meta.glob("../../src/**/*.{ts,tsx}", {
  query: "?raw",
  import: "default",
  eager: true,
});

function toManifestPath(globKey: string): string {
  const marker = "src/";
  return globKey.slice(globKey.indexOf(marker));
}

const onDiskManifestPaths = Object.keys(rawSourceModules).map(toManifestPath);

describe("IMPORT_FEATURE_MODULES manifest (design §11)", () => {
  it("is non-empty and every entry exists on disk", () => {
    expect(IMPORT_FEATURE_MODULES.length).toBeGreaterThan(0);

    const missing = IMPORT_FEATURE_MODULES.filter(
      (path) => !onDiskManifestPaths.includes(path),
    );

    expect(missing).toEqual([]);
  });

  it("contains every feature-named file under apps/web/src/", () => {
    const featureNamed = onDiskManifestPaths.filter((path) => FEATURE_NAME_PATTERN.test(path));

    const unlisted = featureNamed.filter(
      (path) => !(IMPORT_FEATURE_MODULES as readonly string[]).includes(path),
    );

    expect(unlisted).toEqual([]);
  });
});

describe("no client-side linguistic rules", () => {
  it("test_import_modules_have_no_linguistic_rules", () => {
    const violations = IMPORT_FEATURE_MODULES.filter((manifestPath) => {
      const entry = Object.entries(rawSourceModules).find(
        ([globKey]) => toManifestPath(globKey) === manifestPath,
      );
      if (!entry) {
        // Caught separately by the manifest existence assertion above.
        return false;
      }
      const [, source] = entry;
      return FORBIDDEN_PATTERN.test(source);
    });

    expect(violations).toEqual([]);
  });
});

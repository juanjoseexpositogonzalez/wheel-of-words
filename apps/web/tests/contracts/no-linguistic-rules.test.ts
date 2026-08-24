import ts from "typescript";
import { describe, expect, it } from "vitest";

/**
 * AC-002-19 / design §11 — the frontend duplicates no linguistic rules.
 * REQ-003-018 / task 5.8 — extended to the annotation view: zero
 * lemmatize/tag/normalize/precedence-resolution matches there either.
 *
 * A repo-wide search over `apps/web/src/` would false-positive the day someone
 * sorts an unrelated dropdown. This pinned, cut-scoped manifest is the
 * mechanism that keeps the search scoped to import/frequency-table and
 * annotation code without abandoning the flat `pages/components/api/types`
 * layout.
 *
 * The manifest is cut-scoped: it lists the modules that exist in the current
 * cut. Cut 3 (T309) appended `DeleteImportButton.tsx`; SPEC-003 slice 5
 * (task 5.8) appends `AnnotationTable.tsx`, `api/annotation.ts`, and
 * `types/annotation.ts` — see design §11's "cut-scoped manifest" reading.
 * Renamed from `IMPORT_FEATURE_MODULES` to `FRONTEND_FEATURE_MODULES`
 * since it now covers two features, not one; the rename is contained to
 * this file.
 *
 * Uses `import.meta.glob` rather than `node:fs` so this file needs no
 * `@types/node`, matching this project's existing minimal-dependency
 * convention (see the manual `declare const process` in `vitest.config.ts`
 * and `playwright.config.ts`).
 */
const FRONTEND_FEATURE_MODULES = [
  "src/pages/ImportPage.tsx",
  "src/components/ImportForm.tsx",
  "src/components/FrequencyTable.tsx",
  "src/components/DeleteImportButton.tsx",
  "src/components/AnnotationTable.tsx",
  "src/api/imports.ts",
  "src/api/annotation.ts",
  "src/types/imports.ts",
  "src/types/annotation.ts",
] as const;

const FEATURE_NAME_PATTERN = /[Ii]mport|[Ff]requenc|[Aa]nnotat/;
const FORBIDDEN_METHODS = new Set(["localeCompare", "normalize", "reverse", "sort", "toLowerCase", "toSorted"]);
const FORBIDDEN_NORMALIZATION_FORMS = new Set(["NFC", "NFD", "NFKC", "NFKD"]);

// REQ-003-018 (task 5.8): the annotation-specific linguistic operations no
// built-in method name covers — lemmatization, tagging, tokenization, and
// correction-precedence resolution are all bespoke logic, so they can only
// leak in as an IDENTIFIER (a function/variable name), never a method call
// on a built-in. Scoped narrowly to avoid false-positiving on ordinary
// English words: "tag" alone is excluded (too common, e.g. a future `<Tag>`
// UI element) — REQ-003-022's "no PROPN special case" is covered separately
// by the structural absence of the literal `PROPN` in this view's sources,
// not by this pattern.
const FORBIDDEN_IDENTIFIER_PATTERN = /lemmatiz|tokeniz|resolveEffective|correctionPrecedence/i;

interface LinguisticRuleViolation {
  readonly file: string;
  readonly line: number;
  readonly kind: string;
  readonly text: string;
}

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

function scriptKindFor(path: string): ts.ScriptKind {
  return path.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
}

export function findLinguisticRuleViolations(
  path: string,
  source: string,
): LinguisticRuleViolation[] {
  const sourceFile = ts.createSourceFile(
    path,
    source,
    ts.ScriptTarget.Latest,
    /* setParentNodes */ true,
    scriptKindFor(path),
  );
  const violations: LinguisticRuleViolation[] = [];

  function report(node: ts.Node, kind: string, text: string): void {
    const { line } = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
    violations.push({ file: path, line: line + 1, kind, text });
  }

  function visit(node: ts.Node): void {
    if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
      const expression = node.expression;
      if (expression.expression.getText(sourceFile) === "Intl" && expression.name.text === "Collator") {
        report(expression.name, "function call", "Intl.Collator");
      }
      const method = expression.name.text;
      if (FORBIDDEN_METHODS.has(method)) {
        report(expression.name, "method call", method);
      }
    } else if (ts.isNewExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
      const expression = node.expression;
      if (expression.expression.getText(sourceFile) === "Intl" && expression.name.text === "Collator") {
        report(expression.name, "constructor", "Intl.Collator");
      }
    } else if (
      ts.isStringLiteral(node) &&
      FORBIDDEN_NORMALIZATION_FORMS.has(node.text)
    ) {
      report(node, "normalization form literal", node.text);
    } else if (
      (ts.isIdentifier(node) || ts.isPrivateIdentifier(node)) &&
      FORBIDDEN_IDENTIFIER_PATTERN.test(node.text)
    ) {
      report(node, "identifier", node.text);
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return violations;
}

function sourceForManifestPath(manifestPath: string): string | undefined {
  const entry = Object.entries(rawSourceModules).find(
    ([globKey]) => toManifestPath(globKey) === manifestPath,
  );
  return entry?.[1];
}

function formatViolations(violations: readonly LinguisticRuleViolation[]): string {
  return (
    "client-side linguistic rules leaked into import frontend sources:\n" +
    violations.map((v) => `${v.file}:${v.line} ${v.kind} ${JSON.stringify(v.text)}`).join("\n")
  );
}

const onDiskManifestPaths = Object.keys(rawSourceModules).map(toManifestPath);

describe("FRONTEND_FEATURE_MODULES manifest (design §11)", () => {
  it("is non-empty and every entry exists on disk", () => {
    expect(FRONTEND_FEATURE_MODULES.length).toBeGreaterThan(0);

    const missing = FRONTEND_FEATURE_MODULES.filter(
      (path) => !onDiskManifestPaths.includes(path),
    );

    expect(missing).toEqual([]);
  });

  it("contains every feature-named file under apps/web/src/", () => {
    const featureNamed = onDiskManifestPaths.filter((path) => FEATURE_NAME_PATTERN.test(path));

    const unlisted = featureNamed.filter(
      (path) => !(FRONTEND_FEATURE_MODULES as readonly string[]).includes(path),
    );

    expect(unlisted).toEqual([]);
  });
});

describe("no client-side linguistic rules", () => {
  it("test_import_and_annotation_modules_have_no_linguistic_rules", () => {
    const violations = FRONTEND_FEATURE_MODULES.flatMap((manifestPath) => {
      const source = sourceForManifestPath(manifestPath);
      if (source === undefined) {
        // Caught separately by the manifest existence assertion above.
        return [];
      }
      return findLinguisticRuleViolations(manifestPath, source);
    });

    expect(violations, formatViolations(violations)).toEqual([]);
  });
});

describe("findLinguisticRuleViolations", () => {
  it("ignores comments that explain forbidden frontend transformations", () => {
    const source = [
      "export function render(): void {",
      "  // Do not call rows.toSorted(), row.name.localeCompare(), or text.normalize(\"NFC\") here.",
      "  return;",
      "}",
    ].join("\n");

    expect(findLinguisticRuleViolations("synthetic.ts", source)).toEqual([]);
  });

  it("reports mutating and immutable client-side sort calls", () => {
    const source = [
      "export function render(rows: string[]): void {",
      "  rows.sort();",
      "  rows.toSorted();",
      "}",
    ].join("\n");

    const violations = findLinguisticRuleViolations("synthetic.ts", source);

    expect(violations).toEqual([
      { file: "synthetic.ts", line: 2, kind: "method call", text: "sort" },
      { file: "synthetic.ts", line: 3, kind: "method call", text: "toSorted" },
    ]);
  });

  it("reports reverse and locale-aware comparison calls", () => {
    const source = [
      "export function render(rows: string[]): void {",
      "  rows.reverse();",
      "  rows[0].localeCompare(rows[1]);",
      "  new Intl.Collator('es').compare(rows[0], rows[1]);",
      "  Intl.Collator('en').compare(rows[0], rows[1]);",
      "}",
    ].join("\n");

    const violations = findLinguisticRuleViolations("synthetic.ts", source);

    expect(violations).toEqual([
      { file: "synthetic.ts", line: 2, kind: "method call", text: "reverse" },
      { file: "synthetic.ts", line: 3, kind: "method call", text: "localeCompare" },
      { file: "synthetic.ts", line: 4, kind: "constructor", text: "Intl.Collator" },
      { file: "synthetic.ts", line: 5, kind: "function call", text: "Intl.Collator" },
    ]);
  });

  it("reports case folding and Unicode normalization calls", () => {
    const source = [
      "export function render(text: string): string {",
      "  return text.toLowerCase().normalize('NFC');",
      "}",
    ].join("\n");

    const violations = findLinguisticRuleViolations("synthetic.ts", source);

    expect(violations).toEqual([
      { file: "synthetic.ts", line: 2, kind: "method call", text: "normalize" },
      { file: "synthetic.ts", line: 2, kind: "method call", text: "toLowerCase" },
      { file: "synthetic.ts", line: 2, kind: "normalization form literal", text: "NFC" },
    ]);
  });

  // REQ-003-018 (task 5.8): a bespoke lemmatizer, tokenizer, or
  // correction-precedence resolver has no built-in method name to catch —
  // it can only leak in as an identifier.
  it("reports an identifier naming a bespoke lemmatizer, tokenizer, or precedence resolver", () => {
    const source = [
      "export function annotate(tokens: string[]): void {",
      "  lemmatizeToken(tokens[0]);",
      "  tokenizeText(tokens[0]);",
      "  resolveEffective(tokens[0], null);",
      "  correctionPrecedence(tokens[0]);",
      "}",
    ].join("\n");

    const violations = findLinguisticRuleViolations("synthetic.ts", source);

    expect(violations).toEqual([
      { file: "synthetic.ts", line: 2, kind: "identifier", text: "lemmatizeToken" },
      { file: "synthetic.ts", line: 3, kind: "identifier", text: "tokenizeText" },
      { file: "synthetic.ts", line: 4, kind: "identifier", text: "resolveEffective" },
      { file: "synthetic.ts", line: 5, kind: "identifier", text: "correctionPrecedence" },
    ]);
  });

  it("does not flag the ordinary word 'tag' alone, scoped narrowly to avoid false positives", () => {
    const source = [
      "export function render(tag: string): string {",
      "  return tag;",
      "}",
    ].join("\n");

    expect(findLinguisticRuleViolations("synthetic.ts", source)).toEqual([]);
  });
});

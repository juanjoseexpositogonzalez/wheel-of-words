import ts from "typescript";
import { describe, expect, it } from "vitest";

/**
 * AC-002-10 / REQ-002-007 — frontend leg (T1C14).
 *
 * Structural, not textual — mirrors the backend Python AST guard in
 * `apps/api/tests/unit/test_no_lemma_naming.py`. Naming that "lemma"/"lexeme"
 * is forbidden requires writing the word somewhere; a plain text search over
 * source files forbids the word inside the very sentence explaining why it
 * is forbidden. That is exactly the pathology cut 1b converted the backend
 * leg away from (grep → AST): see the AC-002-10 rationale in
 * `openspec/changes/text-import/specs/002-text-import/spec.md`.
 *
 * What is checked, and what is not:
 * - Identifiers: variables, functions, parameters, classes, properties,
 *   JSX tag names, import/export specifiers.
 * - Non-comment string literals: plain string literals, template literals
 *   (including every interpolated part), and JSX text.
 * - `//` and block comments never reach the TypeScript AST produced by
 *   `ts.createSourceFile` — a plain node walk cannot see them, by
 *   construction. That is the same mechanism Python's `ast` module gives the
 *   backend leg for free, and it is the entire reason this leg moved off a
 *   plain text search: a real code comment explaining the prohibition (e.g.
 *   "a form is not a lemma") must stay green here.
 *
 * Uses the TypeScript compiler API (the `typescript` package, already an
 * `apps/web` devDependency — it is what powers `tsc --noEmit`/`pnpm run
 * typecheck`). No new dependency was added for this guard.
 *
 * Reads sources via `import.meta.glob` rather than `node:fs`, matching this
 * project's existing no-`@types/node` convention (see the manual
 * `declare const process` in `vitest.config.ts`/`playwright.config.ts` and
 * `no-linguistic-rules.test.ts`, which uses the same glob pattern).
 */

const FORBIDDEN_PATTERN = /lemma|lemas|lexeme|lexema/i;

interface Violation {
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

// Files that make the frontend scan meaningful, mirroring the backend leg's
// `_EXPECTED_FILES`. If the glob walk ever stopped reaching these, the guard
// below would pass on every run without checking anything — this is the
// mutation-resistance check for non-vacuity.
const FRONTEND_EXPECTED_FILES = [
  "src/pages/ImportPage.tsx",
  "src/components/ImportForm.tsx",
  "src/components/FrequencyTable.tsx",
  "src/api/imports.ts",
  "src/types/imports.ts",
] as const;

function toRelativePath(globKey: string): string {
  const marker = "src/";
  return globKey.slice(globKey.indexOf(marker));
}

function scriptKindFor(path: string): ts.ScriptKind {
  return path.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
}

export function findViolations(path: string, source: string): Violation[] {
  const sourceFile = ts.createSourceFile(
    path,
    source,
    ts.ScriptTarget.Latest,
    /* setParentNodes */ true,
    scriptKindFor(path),
  );
  const violations: Violation[] = [];

  function report(node: ts.Node, kind: string, text: string): void {
    if (!FORBIDDEN_PATTERN.test(text)) {
      return;
    }
    const { line } = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
    violations.push({ file: path, line: line + 1, kind, text });
  }

  function visit(node: ts.Node): void {
    if (ts.isIdentifier(node) || ts.isPrivateIdentifier(node)) {
      report(node, "identifier", node.text);
    } else if (ts.isStringLiteral(node) || ts.isTemplateLiteralToken(node)) {
      report(node, "string literal", node.text);
    } else if (ts.isJsxText(node)) {
      report(node, "JSX text", node.text);
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return violations;
}

function violationsAcrossFrontendSources(): Violation[] {
  return Object.entries(rawSourceModules).flatMap(([globKey, source]) =>
    findViolations(toRelativePath(globKey), source),
  );
}

function formatViolations(violations: readonly Violation[]): string {
  return (
    "lemma naming leaked into the frontend sources:\n" +
    violations.map((v) => `${v.file}:${v.line} ${v.kind} ${JSON.stringify(v.text)}`).join("\n")
  );
}

describe("frontend lemma-naming guard (AC-002-10, T1C14)", () => {
  it("test_the_scan_reaches_the_shipped_frontend_sources", () => {
    // Non-vacuity / mutation-resistance: if the glob ever resolved to zero
    // files (or stopped reaching these specific ones), this assertion fails
    // — it does not silently pass. Without it, the guard below would be
    // trivially true over an empty walk.
    const scanned = Object.keys(rawSourceModules).map(toRelativePath);

    for (const expected of FRONTEND_EXPECTED_FILES) {
      expect(scanned).toContain(expected);
    }
  });

  it("test_frontend_sources_contain_no_lemma_naming", () => {
    /**
     * MUTATION CHECK — this is an absence assertion. It passes on its first
     * run over correct UI copy, which proves nothing on its own. Verified
     * the T1A10 way: temporarily set a `FrequencyTable.tsx` column header to
     * `Lemma`, confirmed an `AssertionError` naming the file, line, and
     * matched token, then reverted and confirmed green again. Also verified
     * the negative leg that is the entire point of this guard: adding a real
     * code comment such as `// a form is not a lemma and not a lexeme` to
     * `FrequencyTable.tsx` stays green here — see T1C14 in
     * `openspec/changes/text-import/tasks.md` for both observed outputs.
     */
    const violations = violationsAcrossFrontendSources();

    expect(violations, formatViolations(violations)).toEqual([]);
  });
});

/**
 * Remediation work unit — pins `findViolations` itself against inline source
 * strings, in BOTH directions, mirroring the backend guard's
 * `test_docstrings_and_comments_may_name_the_concept_they_rule_out`,
 * `test_a_field_identifier_named_lemma_still_fails`, and
 * `test_a_response_key_string_literal_named_lemma_still_fails` in
 * `apps/api/tests/unit/test_no_lemma_naming.py`.
 *
 * The two tests above prove the guard over the *shipped* frontend sources.
 * They say nothing about the comment exemption itself — that property was
 * only ever proven once, by a manual mutation described in a code comment
 * (lines 136-145 above), and is otherwise pinned by nothing: a later change
 * to the walk (e.g. switching to `sourceFile.getFullText()` or
 * `ts.getLeadingCommentRanges`) could make comments visible again and CI
 * would stay green. These tests close that gap.
 *
 * Ordinary assertions, not absence assertions: each one calls `findViolations`
 * directly with a real input and asserts a specific, non-trivial expected
 * output (kind, matched text, and line number) that only holds if the walk's
 * production logic is correct.
 */
describe("findViolations (remediation — pins the comment exemption directly)", () => {
  it("a // line comment naming the forbidden concept produces zero violations", () => {
    const source = [
      "function noop(): void {",
      "  // a form is not a lemma and not a lexeme",
      "  return;",
      "}",
    ].join("\n");

    expect(findViolations("synthetic.ts", source)).toEqual([]);
  });

  it("a block comment naming the forbidden concept produces zero violations", () => {
    const source = [
      "function noop(): void {",
      "  /* a form is not a lemma and not a lexeme */",
      "  return;",
      "}",
    ].join("\n");

    expect(findViolations("synthetic.ts", source)).toEqual([]);
  });

  it("an identifier naming the forbidden concept is reported as one identifier violation at the right line", () => {
    const source = [
      "function noop(): void {",
      "  // filler line so the violation is not on line 1",
      "  const lemmaCount = 0;",
      "  return;",
      "}",
    ].join("\n");

    const violations = findViolations("synthetic.ts", source);

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({ kind: "identifier", text: "lemmaCount", line: 3 });
  });

  it("a string literal naming the forbidden concept is reported as one string-literal violation at the right line", () => {
    const source = [
      "function noop(): string {",
      "  // filler line so the violation is not on line 1",
      '  const key = "lemma_form";',
      "  return key;",
      "}",
    ].join("\n");

    const violations = findViolations("synthetic.ts", source);

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({ kind: "string literal", text: "lemma_form", line: 3 });
  });

  it("a template literal naming the forbidden concept is reported as one string-literal violation at the right line", () => {
    const source = [
      "function label(): string {",
      "  // filler line so the violation is not on line 1",
      "  const msg = `lemma`;",
      "  return msg;",
      "}",
    ].join("\n");

    const violations = findViolations("synthetic.ts", source);

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({ kind: "string literal", text: "lemma", line: 3 });
  });

  it("JSX text naming the forbidden concept is reported as one JSX-text violation at the right line, and requires a .tsx path", () => {
    const source = [
      "function Header(): JSX.Element {",
      "  return (",
      "    <table>",
      "      <thead>",
      "        <tr>",
      "          <th>Lemma</th>",
      "        </tr>",
      "      </thead>",
      "    </table>",
      "  );",
      "}",
    ].join("\n");

    const violations = findViolations("synthetic.tsx", source);

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({ kind: "JSX text", text: "Lemma", line: 6 });
  });
});

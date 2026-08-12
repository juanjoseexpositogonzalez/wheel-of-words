/**
 * Response types for POST /api/v1/imports and GET/DELETE /api/v1/imports/{id},
 * mirroring `types/health.ts`.
 *
 * `id` was added here in cut 3 (T309), completing the widening the backend
 * DTO already made in cut 2 (T212, `api/dtos/imports.py::ImportResultResponse`):
 * the backend has returned a real `id` on every response since cut 2, but no
 * cut-2 task touched this frontend file (cut 2 was backend-only per design
 * §12.4's cut split), so the type stayed stale relative to the shipped
 * contract until `DeleteImportButton` (T309) needed the id to call
 * `DELETE /api/v1/imports/{id}`. Required, not optional — matching the
 * backend's `id: int`, always populated from cut 2 onward. Cut 1b's original
 * omission (T1B13 resolution: no `id` member at all, never `id: number |
 * null`) is superseded, not weakened: the field was always meant to arrive
 * additively once a `Book` row existed, and one always does now.
 */

export interface FormFrequency {
  normalized_form: string;
  display_form: string;
  frequency: number;
}

export interface ImportResult {
  id: number;
  import_status: "succeeded";
  distinct_form_count: number;
  total_token_count: number;
  forms: FormFrequency[];
}

/**
 * Response types for POST /api/v1/imports, mirroring `types/health.ts`.
 *
 * This cut writes no `Book` row, so `ImportResult` declares **no** `id` member
 * at all — not `id: number | null` (T1B13 resolution, binding on this cut).
 * Cut 2 widens the type additively once persistence exists.
 */

export interface FormFrequency {
  normalized_form: string;
  display_form: string;
  frequency: number;
}

export interface ImportResult {
  import_status: "succeeded";
  distinct_form_count: number;
  total_token_count: number;
  forms: FormFrequency[];
}

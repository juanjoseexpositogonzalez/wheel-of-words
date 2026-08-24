/**
 * Response types for POST/GET /api/v1/imports/{id}/annotation, mirroring
 * `api/dtos/annotation.py`. A contract distinct from `types/imports.ts`
 * (REQ-003-017): grouped by occurrence, not by normalized form.
 */

export interface AnnotationProvenance {
  source: string;
  model_name: string;
  model_version: string;
  language: string;
  processed_at: string;
}

export interface AnnotatedOccurrence {
  position: number;
  raw_text: string;
  pos: string | null;
  pos_origin: "automatic" | "manual";
  automatic_pos: string | null;
  pos_confidence: number | null;
  lemma: string | null;
  lemma_origin: "automatic" | "manual";
  automatic_lemma: string | null;
  lemma_confidence: number | null;
}

export interface AnnotationResult {
  id: number;
  provenance: AnnotationProvenance | null;
  occurrences: AnnotatedOccurrence[];
}

export interface VocabularyGroup {
  lemma: string | null;
  pos: string | null;
  occurrence_count: number;
}

export interface VocabularyResult {
  id: number;
  group_count: number;
  total_occurrence_count: number;
  groups: VocabularyGroup[];
}

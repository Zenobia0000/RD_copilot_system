export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.4"
  }
  public: {
    Tables: {
      action_items: {
        Row: {
          id: string
          project_id: string
          decision_id: string | null
          description: string
          assignee: string | null
          due_date: string | null
        }
        Insert: {
          id?: string
          project_id: string
          decision_id?: string | null
          description: string
          assignee?: string | null
          due_date?: string | null
        }
        Update: {
          id?: string
          project_id?: string
          decision_id?: string | null
          description?: string
          assignee?: string | null
          due_date?: string | null
        }
        Relationships: []
      }
      alternatives: {
        Row: {
          id: string
          project_id: string
          name: string
          mechanism: string | null
          source: string | null
          key_assumption_ids: string[] | null
          must_scores: Json | null
          interface_contract: Json | null
          pre_cad_scores: Json | null
          overall_pass: boolean | null
          cad_status: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          name: string
          mechanism?: string | null
          source?: string | null
          key_assumption_ids?: string[] | null
          must_scores?: Json | null
          interface_contract?: Json | null
          pre_cad_scores?: Json | null
          overall_pass?: boolean | null
          cad_status?: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          name?: string
          mechanism?: string | null
          source?: string | null
          key_assumption_ids?: string[] | null
          must_scores?: Json | null
          interface_contract?: Json | null
          pre_cad_scores?: Json | null
          overall_pass?: boolean | null
          cad_status?: string
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      /** @deprecated v3.0: Anti-Anchor retired, de-anchoring merged into TRIZ L1 */
      anti_anchor_routes: {
        Row: {
          id: string
          project_id: string
          name: string
          description: string | null
          is_non_typical: boolean
          source: string | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          name: string
          description?: string | null
          is_non_typical?: boolean
          source?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          name?: string
          description?: string | null
          is_non_typical?: boolean
          source?: string | null
          created_at?: string
        }
        Relationships: []
      }
      assumptions: {
        Row: {
          id: string
          project_id: string
          code: string
          content: string
          source: string | null
          source_type: string | null
          worst_consequence: string | null
          worst_severity: string | null
          min_validation: string | null
          validation_cost: string | null
          validation_method: string | null
          estimated_days: number | null
          status: string
          verification_stage: string
          impact_scope: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          code: string
          content: string
          source?: string | null
          source_type?: string | null
          worst_consequence?: string | null
          worst_severity?: string | null
          min_validation?: string | null
          validation_cost?: string | null
          validation_method?: string | null
          estimated_days?: number | null
          status?: string
          verification_stage?: string
          impact_scope?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          code?: string
          content?: string
          source?: string | null
          source_type?: string | null
          worst_consequence?: string | null
          worst_severity?: string | null
          min_validation?: string | null
          validation_cost?: string | null
          validation_method?: string | null
          estimated_days?: number | null
          status?: string
          verification_stage?: string
          impact_scope?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      adverse_consequences: {
        Row: {
          id: string
          project_id: string
          alternative_id: string | null
          description: string
          probability: string | null
          severity: string | null
          level: string | null
          mitigation: string | null
          risk_artifact_id: string | null
        }
        Insert: {
          id?: string
          project_id: string
          alternative_id?: string | null
          description: string
          probability?: string | null
          severity?: string | null
          level?: string | null
          mitigation?: string | null
          risk_artifact_id?: string | null
        }
        Update: {
          id?: string
          project_id?: string
          alternative_id?: string | null
          description?: string
          probability?: string | null
          severity?: string | null
          level?: string | null
          mitigation?: string | null
          risk_artifact_id?: string | null
        }
        Relationships: []
      }
      briefs: {
        Row: {
          id: string
          project_id: string
          mission: string | null
          task_definition_5w1h: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          mission?: string | null
          task_definition_5w1h?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          mission?: string | null
          task_definition_5w1h?: Json | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      cld_edges: {
        Row: {
          id: string
          project_id: string
          from_node: string
          to_node: string
          polarity: string
        }
        Insert: {
          id?: string
          project_id: string
          from_node: string
          to_node: string
          polarity?: string
        }
        Update: {
          id?: string
          project_id?: string
          from_node?: string
          to_node?: string
          polarity?: string
        }
        Relationships: []
      }
      cld_nodes: {
        Row: {
          id: string
          project_id: string
          label: string
          x: number
          y: number
          node_type: string
          assumption_id: string | null
          is_leverage: boolean
        }
        Insert: {
          id?: string
          project_id: string
          label: string
          x?: number
          y?: number
          node_type?: string
          assumption_id?: string | null
          is_leverage?: boolean
        }
        Update: {
          id?: string
          project_id?: string
          label?: string
          x?: number
          y?: number
          node_type?: string
          assumption_id?: string | null
          is_leverage?: boolean
        }
        Relationships: []
      }
      compatibility_pairs: {
        Row: {
          id: string
          project_id: string
          solution_a_id: string
          solution_b_id: string
          result: string
          adoption_type: string | null
          reason: string | null
        }
        Insert: {
          id?: string
          project_id: string
          solution_a_id: string
          solution_b_id: string
          result: string
          adoption_type?: string | null
          reason?: string | null
        }
        Update: {
          id?: string
          project_id?: string
          solution_a_id?: string
          solution_b_id?: string
          result?: string
          adoption_type?: string | null
          reason?: string | null
        }
        Relationships: []
      }
      concept_routes: {
        Row: {
          id: string
          project_id: string
          route_type: string
          composition: Json | null
          composition_rationale: string | null
          anti_pattern_warnings: string[] | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          route_type?: string
          composition?: Json | null
          composition_rationale?: string | null
          anti_pattern_warnings?: string[] | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          route_type?: string
          composition?: Json | null
          composition_rationale?: string | null
          anti_pattern_warnings?: string[] | null
          created_at?: string
        }
        Relationships: []
      }
      constraints: {
        Row: {
          id: string
          project_id: string
          constraint_code: string
          description: string
          source: string | null
          type: string
          feasibility: string | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          constraint_code: string
          description: string
          source?: string | null
          type?: string
          feasibility?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          constraint_code?: string
          description?: string
          source?: string | null
          type?: string
          feasibility?: string | null
          created_at?: string
        }
        Relationships: []
      }
      contradictions: {
        Row: {
          id: string
          project_id: string
          natural_description: string | null
          improving_param: number | null
          worsening_param: number | null
          engineering_statement: string | null
          physical_contradiction: string | null
          type: string | null
          severity: string
          resolved: boolean
          source_question_id: string | null
          source_type: string | null
          sf_substance_1: string | null
          sf_substance_2: string | null
          sf_field: string | null
          sf_interaction: string | null
          sf_completeness: string | null
          // Added by migration 009: PC Decomposition
          parent_contradiction_id: string | null
          derived_parameter: string | null
          subsystem_hint: string | null
          separation_principle_id: string | null
          separation_category: string | null
          separation_rationale: string | null
          pc_attribute_a: string | null
          pc_attribute_not_a: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          natural_description?: string | null
          improving_param?: number | null
          worsening_param?: number | null
          engineering_statement?: string | null
          physical_contradiction?: string | null
          type?: string | null
          severity?: string
          resolved?: boolean
          source_question_id?: string | null
          source_type?: string | null
          sf_substance_1?: string | null
          sf_substance_2?: string | null
          sf_field?: string | null
          sf_interaction?: string | null
          sf_completeness?: string | null
          // Added by migration 009: PC Decomposition
          parent_contradiction_id?: string | null
          derived_parameter?: string | null
          subsystem_hint?: string | null
          separation_principle_id?: string | null
          separation_category?: string | null
          separation_rationale?: string | null
          pc_attribute_a?: string | null
          pc_attribute_not_a?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          natural_description?: string | null
          improving_param?: number | null
          worsening_param?: number | null
          engineering_statement?: string | null
          physical_contradiction?: string | null
          type?: string | null
          severity?: string
          resolved?: boolean
          source_question_id?: string | null
          source_type?: string | null
          sf_substance_1?: string | null
          sf_substance_2?: string | null
          sf_field?: string | null
          sf_interaction?: string | null
          sf_completeness?: string | null
          // Added by migration 009: PC Decomposition
          parent_contradiction_id?: string | null
          derived_parameter?: string | null
          subsystem_hint?: string | null
          separation_principle_id?: string | null
          separation_category?: string | null
          separation_rationale?: string | null
          pc_attribute_a?: string | null
          pc_attribute_not_a?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      decisions: {
        Row: {
          id: string
          project_id: string
          selected_alternative_id: string | null
          selected_alternative_name: string | null
          rationale: string | null
          risk_acceptance: string | null
          decision_date: string | null
          status: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          selected_alternative_id?: string | null
          selected_alternative_name?: string | null
          rationale?: string | null
          risk_acceptance?: string | null
          decision_date?: string | null
          status?: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          selected_alternative_id?: string | null
          selected_alternative_name?: string | null
          rationale?: string | null
          risk_acceptance?: string | null
          decision_date?: string | null
          status?: string
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      evidence_matrix: {
        Row: {
          id: string
          project_id: string
          assumption_code: string
          summary: string | null
          current_level: string
          is_north_star: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          assumption_code: string
          summary?: string | null
          current_level?: string
          is_north_star?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          assumption_code?: string
          summary?: string | null
          current_level?: string
          is_north_star?: boolean
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      experiments: {
        Row: {
          assumption_code: string
          created_at: string
          evidence_level: string | null
          id: string
          linked_assumptions: string[] | null
          method: string | null
          name: string
          project_id: string
          result: string | null
          status: string
          success_criteria: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          assumption_code: string
          created_at?: string
          evidence_level?: string | null
          id?: string
          linked_assumptions?: string[] | null
          method?: string | null
          name: string
          project_id: string
          result?: string | null
          status?: string
          success_criteria?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          assumption_code?: string
          created_at?: string
          evidence_level?: string | null
          id?: string
          linked_assumptions?: string[] | null
          method?: string | null
          name?: string
          project_id?: string
          result?: string | null
          status?: string
          success_criteria?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      profiles: {
        Row: {
          avatar_url: string | null
          created_at: string
          display_name: string
          id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          avatar_url?: string | null
          created_at?: string
          display_name?: string
          id?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          avatar_url?: string | null
          created_at?: string
          display_name?: string
          id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      review_attachments: {
        Row: {
          assumption_code: string | null
          content_type: string | null
          created_at: string
          description: string | null
          file_name: string
          file_path: string
          file_size: number
          id: string
          project_id: string
          user_id: string
        }
        Insert: {
          assumption_code?: string | null
          content_type?: string | null
          created_at?: string
          description?: string | null
          file_name: string
          file_path: string
          file_size?: number
          id?: string
          project_id: string
          user_id: string
        }
        Update: {
          assumption_code?: string | null
          content_type?: string | null
          created_at?: string
          description?: string | null
          file_name?: string
          file_path?: string
          file_size?: number
          id?: string
          project_id?: string
          user_id?: string
        }
        Relationships: []
      }
      kpis: {
        Row: {
          id: string
          project_id: string
          kpi_name: string
          target_value: string | null
          unit: string | null
          measurement_method: string | null
          current_value: string | null
          current_status: string | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          kpi_name: string
          target_value?: string | null
          unit?: string | null
          measurement_method?: string | null
          current_value?: string | null
          current_status?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          kpi_name?: string
          target_value?: string | null
          unit?: string | null
          measurement_method?: string | null
          current_value?: string | null
          current_status?: string | null
          created_at?: string
        }
        Relationships: []
      }
      evidence_entries: {
        Row: {
          id: string
          project_id: string
          user_id: string
          title: string
          measured_value: string
          unit: string | null
          evidence_level: string
          method: string | null
          notes: string | null
          measured_at: string
          kpi_id: string | null
          experiment_id: string | null
          linked_assumption_codes: string[] | null
          linked_must_ids: string[] | null
          attachment_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          user_id: string
          title: string
          measured_value: string
          unit?: string | null
          evidence_level?: string
          method?: string | null
          notes?: string | null
          measured_at?: string
          kpi_id?: string | null
          experiment_id?: string | null
          linked_assumption_codes?: string[] | null
          linked_must_ids?: string[] | null
          attachment_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          user_id?: string
          title?: string
          measured_value?: string
          unit?: string | null
          evidence_level?: string
          method?: string | null
          notes?: string | null
          measured_at?: string
          kpi_id?: string | null
          experiment_id?: string | null
          linked_assumption_codes?: string[] | null
          linked_must_ids?: string[] | null
          attachment_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      unknown_factors: {
        Row: {
          id: string
          project_id: string
          unknown_code: string
          description: string
          impact: string
          status: string
          note: string | null
          linked_assumption_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          unknown_code: string
          description: string
          impact?: string
          status?: string
          note?: string | null
          linked_assumption_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          unknown_code?: string
          description?: string
          impact?: string
          status?: string
          note?: string | null
          linked_assumption_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      knowledge_articles: {
        Row: {
          id: string
          slug: string
          title: string
          description: string | null
          category: string
          tags: string[] | null
          author: string | null
          published_at: string
          content: string | null
          related_links: Json | null
          created_at: string
        }
        Insert: {
          id?: string
          slug: string
          title: string
          description?: string | null
          category: string
          tags?: string[] | null
          author?: string | null
          published_at?: string
          content?: string | null
          related_links?: Json | null
          created_at?: string
        }
        Update: {
          id?: string
          slug?: string
          title?: string
          description?: string | null
          category?: string
          tags?: string[] | null
          author?: string | null
          published_at?: string
          content?: string | null
          related_links?: Json | null
          created_at?: string
        }
        Relationships: []
      }
      knowledge_entries: {
        Row: {
          id: string
          project_id: string
          asset_type: string
          title: string
          content: string | null
          reviewed: boolean
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          asset_type: string
          title: string
          content?: string | null
          reviewed?: boolean
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          asset_type?: string
          title?: string
          content?: string | null
          reviewed?: boolean
          created_at?: string
        }
        Relationships: []
      }
      projects: {
        Row: {
          id: string
          name: string
          description: string | null
          status: string
          phase: string
          progress: number
          mission: string | null
          phase_progress: Json | null
          quick_stats: Json | null
          must_criteria_config: Json | null
          gates_passed: number
          gates_total: number
          created_by: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          description?: string | null
          status?: string
          phase?: string
          progress?: number
          mission?: string | null
          phase_progress?: Json | null
          quick_stats?: Json | null
          must_criteria_config?: Json | null
          gates_passed?: number
          gates_total?: number
          created_by?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          description?: string | null
          status?: string
          phase?: string
          progress?: number
          mission?: string | null
          phase_progress?: Json | null
          quick_stats?: Json | null
          must_criteria_config?: Json | null
          gates_passed?: number
          gates_total?: number
          created_by?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      risks: {
        Row: {
          id: string
          project_id: string
          description: string
          failure_mode: string | null
          probability: number
          severity: number
          mitigation: string | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          description: string
          failure_mode?: string | null
          probability?: number
          severity?: number
          mitigation?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          description?: string
          failure_mode?: string | null
          probability?: number
          severity?: number
          mitigation?: string | null
          created_at?: string
        }
        Relationships: []
      }
      scamper_variants: {
        Row: {
          id: string
          project_id: string
          subsystem_id: string | null
          action: string
          description: string | null
          adopted: boolean
          new_contradictions: Json | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          subsystem_id?: string | null
          action: string
          description?: string | null
          adopted?: boolean
          new_contradictions?: Json | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          subsystem_id?: string | null
          action?: string
          description?: string | null
          adopted?: boolean
          new_contradictions?: Json | null
          created_at?: string
        }
        Relationships: []
      }
      signatures: {
        Row: {
          id: string
          project_id: string
          decision_id: string | null
          name: string
          role: string | null
          status: string
          signed_at: string | null
          note: string | null
        }
        Insert: {
          id?: string
          project_id: string
          decision_id?: string | null
          name: string
          role?: string | null
          status?: string
          signed_at?: string | null
          note?: string | null
        }
        Update: {
          id?: string
          project_id?: string
          decision_id?: string | null
          name?: string
          role?: string | null
          status?: string
          signed_at?: string | null
          note?: string | null
        }
        Relationships: []
      }
      socratic_questions: {
        Row: {
          id: string
          project_id: string
          category: string
          text: string
          answer: string | null
          tagged_as_assumption: boolean
          tagged_as_contradiction: boolean
          ai_suggested_tag: string | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          category: string
          text: string
          answer?: string | null
          tagged_as_assumption?: boolean
          tagged_as_contradiction?: boolean
          ai_suggested_tag?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          category?: string
          text?: string
          answer?: string | null
          tagged_as_assumption?: boolean
          tagged_as_contradiction?: boolean
          ai_suggested_tag?: string | null
          created_at?: string
        }
        Relationships: []
      }
      subsystems: {
        Row: {
          id: string
          project_id: string
          name: string
          reason: string | null
          related_contradictions: string[] | null
          confirmed: boolean
          parent_id: string | null
          interfaces: string | null
          source: string
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          name: string
          reason?: string | null
          related_contradictions?: string[] | null
          confirmed?: boolean
          parent_id?: string | null
          interfaces?: string | null
          source?: string
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          name?: string
          reason?: string | null
          related_contradictions?: string[] | null
          confirmed?: boolean
          parent_id?: string | null
          interfaces?: string | null
          source?: string
          created_at?: string
        }
        Relationships: []
      }
      triz_solutions: {
        Row: {
          id: string
          project_id: string
          contradiction_id: string | null
          path: string
          principle_number: number | null
          principle_name: string | null
          suggestion: string | null
          status: string
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          contradiction_id?: string | null
          path: string
          principle_number?: number | null
          principle_name?: string | null
          suggestion?: string | null
          status?: string
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          contradiction_id?: string | null
          path?: string
          principle_number?: number | null
          principle_name?: string | null
          suggestion?: string | null
          status?: string
          created_at?: string
        }
        Relationships: []
      }
      want_criteria: {
        Row: {
          id: string
          project_id: string
          name: string
          weight: number
          description: string | null
          anchors: string | null
        }
        Insert: {
          id?: string
          project_id: string
          name: string
          weight?: number
          description?: string | null
          anchors?: string | null
        }
        Update: {
          id?: string
          project_id?: string
          name?: string
          weight?: number
          description?: string | null
          anchors?: string | null
        }
        Relationships: []
      }
      want_scores: {
        Row: {
          id: string
          project_id: string
          criterion_id: string | null
          alternative_id: string | null
          score: number
          evidence: string | null
          weighted_total: number
        }
        Insert: {
          id?: string
          project_id: string
          criterion_id?: string | null
          alternative_id?: string | null
          score?: number
          evidence?: string | null
          weighted_total?: number
        }
        Update: {
          id?: string
          project_id?: string
          criterion_id?: string | null
          alternative_id?: string | null
          score?: number
          evidence?: string | null
          weighted_total?: number
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const

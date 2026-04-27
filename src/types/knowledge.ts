/** Knowledge reference from RAG or Web search */
export interface KnowledgeRef {
  id: string;
  type: 'rag' | 'web';
  title: string;
  source: string;
  relevance: 'High' | 'Medium' | 'Low';
  summary: string;
  url?: string;
}

export interface KnowledgeArticle {
  id: string;
  slug: string;
  title: string;
  description: string;
  category: "playbook" | "case-study" | "template" | "convergence-pattern";
  tags: string[];
  author: string;
  publishedAt: string;
  content: string;
  relatedLinks: { label: string; url: string }[];
}

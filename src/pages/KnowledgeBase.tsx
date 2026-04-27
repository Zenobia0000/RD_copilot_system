import { useState, useMemo, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Search, BookOpen, FileText, Lightbulb, Calendar, User, GitBranch, ChevronLeft, ChevronRight } from "lucide-react";
import { useKnowledgeArticles, useKnowledgeArticle } from "@/hooks/api/useKnowledge";

const CATEGORY_MAP: Record<string, { label: string; icon: React.ReactNode }> = {
  playbook: { label: "Playbook", icon: <BookOpen className="h-3.5 w-3.5" /> },
  "case-study": { label: "案例", icon: <Lightbulb className="h-3.5 w-3.5" /> },
  template: { label: "模板", icon: <FileText className="h-3.5 w-3.5" /> },
  "convergence-pattern": { label: "收斂模式", icon: <GitBranch className="h-3.5 w-3.5" /> },
};

const CATEGORIES = ["all", "playbook", "case-study", "template", "convergence-pattern"] as const;
const PAGE_SIZE = 6;

const KnowledgeBase = () => {
  const navigate = useNavigate();
  const { slug } = useParams<{ slug: string }>();

  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [page, setPage] = useState(1);

  const { data: articles, isLoading: articlesLoading } = useKnowledgeArticles();

  // Fetch single article by slug from Supabase
  const { data: liveArticle, isLoading: articleLoading } = useKnowledgeArticle(slug);

  const filtered = useMemo(() => {
    return articles.filter((a) => {
      const matchCategory = activeCategory === "all" || a.category === activeCategory;
      const matchSearch =
        !search ||
        a.title.toLowerCase().includes(search.toLowerCase()) ||
        a.description.toLowerCase().includes(search.toLowerCase()) ||
        a.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));
      return matchCategory && matchSearch;
    });
  }, [search, activeCategory, articles]);

  // Reset to page 1 whenever filter criteria change
  useEffect(() => {
    setPage(1);
  }, [search, activeCategory, articles]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const selectedArticle = slug
    ? (liveArticle ?? articles.find((a) => a.slug === slug) ?? null)
    : null;

  // Loading state for list view
  if (!slug && articlesLoading) {
    return (
      <div className="page-shell-kb">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      </div>
    );
  }

  // Loading state for detail view
  if (slug && articleLoading && !selectedArticle) {
    return (
      <div className="page-shell-kb">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  // ── Detail view ──
  if (selectedArticle) {
    return (
      <div className="page-shell-kb">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/knowledge-base")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <Badge variant="secondary" className="text-xs">
                {CATEGORY_MAP[selectedArticle.category]?.icon}
                <span className="ml-1">{CATEGORY_MAP[selectedArticle.category]?.label}</span>
              </Badge>
              {selectedArticle.tags.map((t) => (
                <Badge key={t} variant="outline" className="text-xs">{t}</Badge>
              ))}
            </div>
            <h1 className="text-2xl font-bold tracking-tight">
              {selectedArticle.title}
            </h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground flex-wrap">
              <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" />{selectedArticle.author}</span>
              <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{selectedArticle.publishedAt}</span>
            </div>
          </div>
        </div>

        <Card>
          <CardContent className="p-6 prose prose-sm max-w-none">
            {selectedArticle.content.split("\n").map((line, i) => {
              if (line.startsWith("## ")) return <h2 key={i} className="text-lg font-semibold mt-6 mb-2">{line.slice(3)}</h2>;
              if (line.startsWith("### ")) return <h3 key={i} className="text-base font-semibold mt-4 mb-1">{line.slice(4)}</h3>;
              if (line.startsWith("- ")) return <li key={i} className="text-sm ml-4 list-disc">{line.slice(2)}</li>;
              if (line.startsWith("| ")) return <p key={i} className="text-sm font-mono text-muted-foreground">{line}</p>;
              if (line.trim() === "") return <br key={i} />;
              if (/^\d+\.\s/.test(line))
                return <li key={i} className="text-sm ml-4 list-decimal">{line.replace(/^\d+\.\s/, '')}</li>;
              return <p key={i} className="text-sm leading-relaxed">{line}</p>;
            })}
          </CardContent>
        </Card>

        {selectedArticle.relatedLinks.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold mb-2">相關文檔</h3>
              <div className="flex flex-wrap gap-2">
                {selectedArticle.relatedLinks.map((link, i) => (
                  <Badge
                    key={i}
                    variant="outline"
                    className="text-xs cursor-pointer hover:bg-accent transition-colors"
                    onClick={() => {
                      if (link.url && link.url !== "#") {
                        navigate(link.url);
                      }
                    }}
                  >
                    {link.label}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // ── List view ──
  return (
    <div className="page-shell-kb">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">知識庫</h1>
        <p className="text-sm text-muted-foreground">瀏覽 Playbook、歷史案例、決策模板與矛盾收斂模式</p>
      </div>

      {/* Search & filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜尋知識庫..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            maxLength={100}
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {CATEGORIES.map((cat) => (
            <Button
              key={cat}
              variant={activeCategory === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveCategory(cat)}
            >
              {cat === "all" ? "全部" : CATEGORY_MAP[cat]?.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Article grid */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <p className="font-medium">沒有找到相關知識</p>
            <p className="text-sm mt-1">請嘗試調整搜尋條件或分類篩選。</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {paged.map((article) => (
              <Card
                key={article.id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => navigate(`/knowledge-base/${article.slug}`)}
              >
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">
                      {CATEGORY_MAP[article.category]?.icon}
                      <span className="ml-1">{CATEGORY_MAP[article.category]?.label}</span>
                    </Badge>
                  </div>
                  <h3 className="font-semibold text-sm line-clamp-2">{article.title}</h3>
                  <p className="text-sm text-muted-foreground line-clamp-2">{article.description}</p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{article.author}</span>
                    <span>{article.publishedAt}</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {article.tags.slice(0, 3).map((t) => (
                      <Badge key={t} variant="outline" className="text-xs">{t}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default KnowledgeBase;

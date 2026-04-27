import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { AlertTriangle, ArrowLeft, ShieldAlert } from 'lucide-react';
import type { HealthStatus } from '@/types/solution';

interface Props {
  health: HealthStatus;
  onGoBack: () => void;
  onForceContinue: () => void;
}

const messages: Record<string, { title: string; desc: string }> = {
  critical: {
    title: '架構健康度：危險',
    desc: '矛盾收斂圖節點數超過 5，這通常表示架構層級的根本性問題，無法透過 TRIZ 局部求解。建議返回問題定義 (D1) 重新界定架構方向。',
  },
  circular: {
    title: '偵測到循環矛盾',
    desc: '矛盾收斂圖中存在循環依賴 (A→B→C→A)，這表示架構內在矛盾，TRIZ 無法解決。需要從根本重新設計架構。',
  },
};

export function ArchitectureHaltOverlay({ health, onGoBack, onForceContinue }: Props) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const msg = messages[health] ?? messages.critical;

  if (health !== 'critical' && health !== 'circular') return null;

  return (
    <>
      <div className="relative rounded-xl border-2 border-red-500 bg-red-50/90 dark:bg-red-950/90 p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-full bg-red-100 dark:bg-red-900">
            {health === 'circular' ? (
              <ShieldAlert className="h-6 w-6 text-red-600" />
            ) : (
              <AlertTriangle className="h-6 w-6 text-red-600" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-bold text-red-700 dark:text-red-400">{msg.title}</h3>
            <p className="text-sm text-red-600/80 dark:text-red-400/80 mt-1 leading-relaxed">
              {msg.desc}
            </p>
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <Button variant="destructive" onClick={onGoBack}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            返回問題定義 (D1)
          </Button>
          <Button
            variant="outline"
            className="border-red-300 text-red-700 hover:bg-red-100 dark:border-red-700 dark:text-red-400"
            onClick={() => setConfirmOpen(true)}
          >
            我理解風險，強制繼續
          </Button>
        </div>
      </div>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              確認強制繼續
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            強制繼續可能導致後續方案存在無法解決的根本性矛盾，增加專案風險。是否確定？
          </p>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>取消</Button>
            <Button
              variant="destructive"
              onClick={() => {
                setConfirmOpen(false);
                onForceContinue();
              }}
            >
              確認繼續
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

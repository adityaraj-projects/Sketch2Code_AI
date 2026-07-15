import { Sidebar } from "@/components/dashboard/Sidebar";
import type { LucideIcon } from "lucide-react";

export function ComingSoonPage({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />
      <main className="flex flex-1 items-center justify-center p-8">
        <div className="max-w-sm text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-500/15">
            <Icon size={24} className="text-violet-400" />
          </div>
          <h2 className="font-display text-lg font-semibold text-paper-100">{title}</h2>
          <p className="mt-2 text-sm text-paper-500">{description}</p>
          <span className="label-eyebrow mt-4 inline-block">Shipping in Phase 2</span>
        </div>
      </main>
    </div>
  );
}

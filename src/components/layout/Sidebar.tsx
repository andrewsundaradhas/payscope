"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";

const NAV = [
  { href: "/dashboard/reports", label: "Reports" },
  { href: "/dashboard/insights", label: "Insights" },
  { href: "/dashboard/chat", label: "AI Chat" },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-[260px] flex-col border-r bg-[var(--ps-panel)]">
      <div className="flex items-start justify-between px-5 pt-5 pb-4">
        <div>
          <div className="text-base font-semibold tracking-tight text-[color:var(--ps-fg)]">
            PayScope
          </div>
          <div className="text-xs text-[color:var(--ps-subtle)]">Reporting Intelligence</div>
        </div>
        <Badge tone="gold" className="mt-0.5">
          Visa Hackathon (Mock)
        </Badge>
      </div>

      <nav className="px-3">
        <div className="space-y-1">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex h-10 items-center rounded-md px-3 text-sm font-semibold transition",
                  active
                    ? "bg-black/[0.04] text-[color:var(--ps-fg)]"
                    : "text-[color:var(--ps-muted)] hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="mt-auto border-t px-5 py-4">
        <div className="text-xs text-[color:var(--ps-subtle)]">Mock Auth</div>
        <div className="mt-1 text-sm font-semibold text-[color:var(--ps-fg)]">
          Demo Analyst
        </div>
        <div className="text-xs text-[color:var(--ps-subtle)]">Visa Internal Analytics</div>
      </div>
    </aside>
  );
}



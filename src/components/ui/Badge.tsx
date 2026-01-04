import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

type Tone = "blue" | "gold" | "neutral";

export function Badge({
  className,
  tone = "neutral",
  ...props
}: ComponentProps<"div"> & { tone?: Tone }) {
  return (
    <div
      {...props}
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold text-[color:var(--ps-fg)]",
        tone === "neutral" && "bg-black/[0.03] text-[color:var(--ps-muted)]",
        tone === "blue" && "bg-[rgba(20,52,203,0.10)] text-[color:var(--ps-fg)]",
        tone === "gold" && "bg-[rgba(247,182,0,0.14)] text-[color:var(--ps-fg)]",
        className,
      )}
    />
  );
}



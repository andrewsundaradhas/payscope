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
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold",
        tone === "neutral" && "border-white/10 bg-white/5 text-white/80",
        tone === "blue" && "border-white/10 bg-[rgba(20,52,203,0.22)] text-white",
        tone === "gold" && "border-white/10 bg-[rgba(247,182,0,0.18)] text-white",
        className,
      )}
    />
  );
}



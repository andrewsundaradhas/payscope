import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

type Tone = "blue" | "gold" | "neutral" | "green";

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
        tone === "neutral" && "bg-[#F5F5F5] text-[#1C2B1C]/70 border-[#E8E8E8]",
        tone === "blue" && "bg-[#1C2B1C] text-white border-[#1C2B1C]",
        tone === "gold" && "bg-[#bef264] text-[#1C2B1C] border-[#84cc16]",
        tone === "green" && "bg-[#bef264]/20 text-[#1C2B1C] border-[#bef264]",
        className,
      )}
    />
  );
}

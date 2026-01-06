import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Select({ className, ...props }: ComponentProps<"select">) {
  return (
    <select
      {...props}
      className={cn(
        "h-9 rounded-lg border border-[#E8E8E8] bg-white px-3 text-sm text-[#1C2B1C] outline-none transition focus-visible:ring-2 focus-visible:ring-[#bef264] focus-visible:border-[#bef264]",
        className,
      )}
    />
  );
}

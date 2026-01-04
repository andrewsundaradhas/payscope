import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Select({ className, ...props }: ComponentProps<"select">) {
  return (
    <select
      {...props}
      className={cn(
        "h-9 rounded-md border border-white/10 bg-white/5 px-3 text-sm text-white/90 outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--ps-gold)]",
        className,
      )}
    />
  );
}



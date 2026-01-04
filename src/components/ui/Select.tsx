import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Select({ className, ...props }: ComponentProps<"select">) {
  return (
    <select
      {...props}
      className={cn(
        "h-9 rounded-md border bg-[var(--ps-panel)] px-3 text-sm text-[color:var(--ps-fg)] outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--ps-gold)]",
        className,
      )}
    />
  );
}



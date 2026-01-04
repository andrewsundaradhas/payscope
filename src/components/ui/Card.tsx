import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      {...props}
      className={cn(
        "rounded-xl border bg-[var(--ps-panel)] shadow-[var(--ps-shadow)]",
        className,
      )}
    />
  );
}

export function CardHeader({ className, ...props }: ComponentProps<"div">) {
  return <div {...props} className={cn("p-4", className)} />;
}

export function CardTitle({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      {...props}
      className={cn(
        "text-sm font-semibold tracking-tight text-[color:var(--ps-fg)]",
        className,
      )}
    />
  );
}

export function CardContent({ className, ...props }: ComponentProps<"div">) {
  return <div {...props} className={cn("p-4 pt-0", className)} />;
}



import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      {...props}
      className={cn(
        "rounded-2xl border border-[#E8E8E8] bg-white shadow-sm",
        className,
      )}
    />
  );
}

export function CardHeader({ className, ...props }: ComponentProps<"div">) {
  return <div {...props} className={cn("p-5 pb-0", className)} />;
}

export function CardTitle({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      {...props}
      className={cn(
        "text-base font-semibold tracking-tight text-[#1C2B1C]",
        className,
      )}
    />
  );
}

export function CardContent({ className, ...props }: ComponentProps<"div">) {
  return <div {...props} className={cn("p-5", className)} />;
}

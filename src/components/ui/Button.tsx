import Link from "next/link";
import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost";

type Props = ComponentProps<"button"> & {
  variant?: Variant;
};

export function Button({ className, variant = "primary", ...props }: Props) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ps-gold)] disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary" &&
          "bg-[var(--ps-blue)] text-white hover:bg-[var(--ps-blue-2)]",
        variant === "secondary" &&
          "border bg-[var(--ps-panel)] text-[color:var(--ps-fg)] hover:bg-black/[0.03]",
        variant === "ghost" &&
          "text-[color:var(--ps-muted)] hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]",
        className,
      )}
    />
  );
}

type LinkButtonProps = ComponentProps<typeof Link> & {
  variant?: Variant;
  className?: string;
};

export function LinkButton({
  className,
  variant = "primary",
  ...props
}: LinkButtonProps) {
  return (
    <Link
      {...props}
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ps-gold)]",
        variant === "primary" &&
          "bg-[var(--ps-blue)] text-white hover:bg-[var(--ps-blue-2)]",
        variant === "secondary" &&
          "border bg-[var(--ps-panel)] text-[color:var(--ps-fg)] hover:bg-black/[0.03]",
        variant === "ghost" &&
          "text-[color:var(--ps-muted)] hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]",
        className,
      )}
    />
  );
}



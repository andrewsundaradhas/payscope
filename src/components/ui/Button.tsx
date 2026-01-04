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
          "border border-white/10 bg-white/5 text-white hover:bg-white/8",
        variant === "ghost" && "text-white/80 hover:bg-white/5 hover:text-white",
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
          "border border-white/10 bg-white/5 text-white hover:bg-white/8",
        variant === "ghost" && "text-white/80 hover:bg-white/5 hover:text-white",
        className,
      )}
    />
  );
}



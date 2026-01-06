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
        "inline-flex h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[#bef264] disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary" &&
          "bg-[#1C2B1C] text-white hover:bg-[#2a3d2a]",
        variant === "secondary" &&
          "border border-[#E8E8E8] bg-white text-[#1C2B1C] hover:bg-[#F5F5F5]",
        variant === "ghost" &&
          "text-[#1C2B1C]/70 hover:bg-[#F5F5F5] hover:text-[#1C2B1C]",
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
        "inline-flex h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[#bef264]",
        variant === "primary" &&
          "bg-[#1C2B1C] text-white hover:bg-[#2a3d2a]",
        variant === "secondary" &&
          "border border-[#E8E8E8] bg-white text-[#1C2B1C] hover:bg-[#F5F5F5]",
        variant === "ghost" &&
          "text-[#1C2B1C]/70 hover:bg-[#F5F5F5] hover:text-[#1C2B1C]",
        className,
      )}
    />
  );
}

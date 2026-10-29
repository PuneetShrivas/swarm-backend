"use client";

import React from "react";
import { ArrowRight } from "lucide-react";

interface InteractiveHoverButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  text?: string;
  icon?: React.ReactNode;
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
}

export function InteractiveHoverButton({
  text = "Continue",
  icon,
  className = "",
  variant = "primary",
  size = "md",
  children,
  ...props
}: InteractiveHoverButtonProps) {
  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-xs gap-2",
    lg: "px-5 py-2.5 text-sm gap-2.5",
  }[size];

  const variantClasses = {
    primary:
      "bg-linear-primary hover:bg-linear-hover text-white shadow-sm hover:shadow-glow",
    secondary:
      "bg-surface-2 hover:bg-surface-3 text-ink border border-hairline hover:border-hairline-strong",
    outline:
      "bg-transparent hover:bg-surface-1 text-ink border border-hairline hover:border-hairline-strong",
    ghost: "bg-transparent hover:bg-surface-1 text-ink-subtle hover:text-ink",
  }[variant];

  return (
    <button
      className={`relative inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] select-none group cursor-pointer ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      <span>{children || text}</span>
      <span className="inline-flex items-center transition-transform duration-200 group-hover:translate-x-0.5">
        {icon || <ArrowRight size={13} className="text-current opacity-80 group-hover:opacity-100" />}
      </span>
    </button>
  );
}

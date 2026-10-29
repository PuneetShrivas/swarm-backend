import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  asChild?: boolean;
}

const variantStyles: Record<string, string> = {
  default:
    "bg-linear-primary text-white shadow-sm hover:bg-linear-hover focus-visible:ring-linear-focus",
  destructive:
    "bg-destructive text-white shadow-sm hover:bg-destructive/90 focus-visible:ring-destructive",
  outline:
    "border border-hairline bg-surface-1 hover:bg-surface-2 hover:border-hairline-strong text-ink shadow-sm",
  secondary:
    "bg-surface-2 text-ink hover:bg-surface-3 border border-hairline",
  ghost:
    "text-ink-subtle hover:text-ink hover:bg-surface-1",
  link:
    "text-linear-primary underline-offset-4 hover:underline p-0 h-auto",
};

const sizeStyles: Record<string, string> = {
  default: "h-9 px-4 py-2 text-sm",
  sm: "h-8 rounded-md px-3 text-xs",
  lg: "h-10 rounded-md px-6 text-base",
  icon: "h-9 w-9 p-0",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "default",
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:pointer-events-none disabled:opacity-50 select-none",
          variantStyles[variant] || variantStyles.default,
          sizeStyles[size] || sizeStyles.default,
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

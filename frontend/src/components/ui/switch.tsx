"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface SwitchProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export function Switch({
  checked = false,
  onCheckedChange,
  disabled = false,
  className,
  id,
}: SwitchProps) {
  const [internalChecked, setInternalChecked] = React.useState(checked);

  React.useEffect(() => {
    setInternalChecked(checked);
  }, [checked]);

  const toggle = () => {
    if (disabled) return;
    const next = !internalChecked;
    setInternalChecked(next);
    onCheckedChange?.(next);
  };

  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={internalChecked}
      disabled={disabled}
      onClick={toggle}
      className={cn(
        "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border border-hairline transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-linear-focus focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        internalChecked ? "bg-linear-primary border-linear-primary" : "bg-surface-2",
        className
      )}
    >
      <span
        className={cn(
          "pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm ring-0 transition-transform",
          internalChecked ? "translate-x-4" : "translate-x-0.5"
        )}
      />
    </button>
  );
}

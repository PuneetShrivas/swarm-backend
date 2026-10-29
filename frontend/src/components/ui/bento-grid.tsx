import React from "react";
import { cn } from "@/lib/utils";

export const BentoGrid = ({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) => {
  return (
    <div
      className={cn(
        "mx-auto grid max-w-7xl grid-cols-1 md:grid-cols-3 gap-4 md:auto-rows-[19rem]",
        className
      )}
    >
      {children}
    </div>
  );
};

export const BentoGridItem = ({
  className,
  title,
  description,
  header,
  icon,
}: {
  className?: string;
  title?: string | React.ReactNode;
  description?: string | React.ReactNode;
  header?: React.ReactNode;
  icon?: React.ReactNode;
}) => {
  return (
    <div
      className={cn(
        "group/bento row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-hairline bg-surface-1 p-5 transition-all duration-300 hover:border-hairline-strong hover:bg-surface-2 shadow-sm overflow-hidden",
        className
      )}
    >
      {header}
      <div className="transition duration-200 group-hover/bento:translate-x-1">
        <div className="flex items-center gap-2 mb-2">
          {icon}
          <div className="font-semibold text-sm tracking-tight text-ink">
            {title}
          </div>
        </div>
        <div className="text-xs text-ink-subtle leading-relaxed">
          {description}
        </div>
      </div>
    </div>
  );
};

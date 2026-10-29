"use client";

import React, { useState } from "react";
import Image from "next/image";

interface BrandLogoProps {
  size?: number;
  className?: string;
  showWordmark?: boolean;
  versionBadge?: string;
  wordmarkClassName?: string;
}

export default function BrandLogo({
  size = 24,
  className = "",
  showWordmark = false,
  versionBadge,
  wordmarkClassName = "",
}: BrandLogoProps) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Brand Icon Mark */}
      <div
        className="relative flex items-center justify-center shrink-0 rounded-md border border-hairline bg-surface-1 overflow-hidden shadow-xs transition-transform group-hover:scale-105"
        style={{ width: size, height: size }}
      >
        {!imgError ? (
          <Image
            src="/swarm-logo.png"
            alt="Swarm"
            width={size}
            height={size}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
            priority
          />
        ) : (
          /* High-tech vector fallback if image fails to load */
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="w-4/5 h-4/5 text-linear-primary"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2L20.6603 7V17L12 22L3.33975 17V7L12 2Z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
            <circle cx="12" cy="12" r="3" fill="currentColor" />
            <path d="M12 2V9M12 15V22M3.5 7L9.5 10.5M14.5 13.5L20.5 17M3.5 17L9.5 13.5M14.5 10.5L20.5 7" stroke="currentColor" strokeWidth="1" strokeOpacity="0.6"/>
          </svg>
        )}
      </div>

      {/* Optional Brand Wordmark */}
      {showWordmark && (
        <div className="flex items-center gap-1.5 select-none">
          <span
            className={`font-semibold text-xs tracking-tight text-ink ${wordmarkClassName}`}
          >
            Swarm
          </span>
          {versionBadge && (
            <span className="text-[9px] font-mono px-1 py-0.2 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
              {versionBadge}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

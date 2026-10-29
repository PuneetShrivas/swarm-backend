"use client";

import React, { useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { IconMenu2, IconX } from "@tabler/icons-react";
import {
  motion,
  AnimatePresence,
  useScroll,
  useMotionValueEvent,
} from "framer-motion";
import Link from "next/link";
import BrandLogo from "@/components/BrandLogo";

interface NavbarProps {
  children: React.ReactNode;
  className?: string;
}

interface NavBodyProps {
  children: React.ReactNode;
  className?: string;
  visible?: boolean;
}

interface NavItemsProps {
  items: {
    name: string;
    link: string;
  }[];
  className?: string;
  onItemClick?: () => void;
}

interface MobileNavProps {
  children: React.ReactNode;
  className?: string;
  visible?: boolean;
}

interface MobileNavHeaderProps {
  children: React.ReactNode;
  className?: string;
}

interface MobileNavMenuProps {
  children: React.ReactNode;
  className?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const Navbar = ({ children, className }: NavbarProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll();
  const [visible, setVisible] = useState<boolean>(false);

  useMotionValueEvent(scrollY, "change", (latest) => {
    if (latest > 60) {
      setVisible(true);
    } else {
      setVisible(false);
    }
  });

  return (
    <motion.div
      ref={ref}
      className={cn("sticky inset-x-0 top-3 z-40 w-full px-4 sm:px-6", className)}
    >
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(
              child as React.ReactElement<{ visible?: boolean }>,
              { visible }
            )
          : child
      )}
    </motion.div>
  );
};

export const NavBody = ({ children, className, visible }: NavBodyProps) => {
  return (
    <motion.div
      animate={{
        backdropFilter: visible ? "blur(12px)" : "blur(4px)",
        boxShadow: visible
          ? "0 0 0 1px rgba(255, 255, 255, 0.08), 0 12px 36px rgba(0, 0, 0, 0.4)"
          : "0 0 0 1px rgba(255, 255, 255, 0.04)",
        width: visible ? "68%" : "100%",
        y: visible ? 4 : 0,
      }}
      transition={{
        type: "spring",
        stiffness: 240,
        damping: 30,
      }}
      className={cn(
        "relative z-[60] mx-auto hidden w-full max-w-6xl flex-row items-center justify-between self-start rounded-full border border-hairline/60 bg-surface-1/80 px-4 py-2 transition-colors lg:flex",
        visible && "bg-surface-1/90 border-hairline-strong",
        className
      )}
    >
      {children}
    </motion.div>
  );
};

export const NavItems = ({ items, className, onItemClick }: NavItemsProps) => {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <div
      onMouseLeave={() => setHovered(null)}
      className={cn(
        "hidden flex-1 flex-row items-center justify-center space-x-1 text-xs font-medium text-ink-subtle lg:flex",
        className
      )}
    >
      {items.map((item, idx) => (
        <a
          onMouseEnter={() => setHovered(idx)}
          onClick={onItemClick}
          className="relative px-3.5 py-1.5 text-xs text-ink-subtle hover:text-ink transition-colors rounded-full"
          key={`nav-link-${idx}`}
          href={item.link}
        >
          {hovered === idx && (
            <motion.div
              layoutId="nav-hover"
              className="absolute inset-0 h-full w-full rounded-full bg-surface-2"
              transition={{ type: "spring", bounce: 0.2, duration: 0.3 }}
            />
          )}
          <span className="relative z-20">{item.name}</span>
        </a>
      ))}
    </div>
  );
};

export const MobileNav = ({ children, className, visible }: MobileNavProps) => {
  return (
    <motion.div
      animate={{
        backdropFilter: visible ? "blur(12px)" : "blur(4px)",
        boxShadow: visible
          ? "0 0 0 1px rgba(255, 255, 255, 0.08), 0 8px 24px rgba(0, 0, 0, 0.4)"
          : "none",
        width: "100%",
      }}
      transition={{
        type: "spring",
        stiffness: 240,
        damping: 30,
      }}
      className={cn(
        "relative z-50 mx-auto flex w-full flex-col items-center justify-between rounded-xl border border-hairline bg-surface-1/90 px-3 py-2 lg:hidden",
        className
      )}
    >
      {children}
    </motion.div>
  );
};

export const MobileNavHeader = ({
  children,
  className,
}: MobileNavHeaderProps) => {
  return (
    <div
      className={cn(
        "flex w-full flex-row items-center justify-between",
        className
      )}
    >
      {children}
    </div>
  );
};

export const MobileNavMenu = ({
  children,
  className,
  isOpen,
}: MobileNavMenuProps) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
          className={cn(
            "mt-3 flex w-full flex-col items-start justify-start gap-3 border-t border-hairline pt-4",
            className
          )}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export const MobileNavToggle = ({
  isOpen,
  onClick,
}: {
  isOpen: boolean;
  onClick: () => void;
}) => {
  return (
    <button
      onClick={onClick}
      className="p-1 rounded-md text-ink-subtle hover:text-ink focus:outline-none"
      aria-label="Toggle navigation"
    >
      {isOpen ? <IconX size={18} /> : <IconMenu2 size={18} />}
    </button>
  );
};

export const NavbarLogo = ({ href = "/" }: { href?: string }) => {
  return (
    <Link
      href={href}
      className="relative z-20 flex items-center gap-2 px-1 text-ink group"
    >
      <BrandLogo size={24} showWordmark={true} versionBadge="v2.0" wordmarkClassName="text-sm" />
    </Link>
  );
};

export const NavbarButton = ({
  children,
  className,
  variant = "primary",
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  variant?: "primary" | "secondary" | "outline" | "empty";
  onClick?: () => void;
}) => {
  const variantMap = {
    primary:
      "bg-linear-primary hover:bg-linear-hover text-white text-xs font-medium px-3.5 py-1.5 rounded-full shadow-sm transition-colors",
    secondary:
      "bg-surface-2 hover:bg-surface-3 text-ink text-xs font-medium px-3.5 py-1.5 rounded-full border border-hairline transition-colors",
    outline:
      "border border-hairline hover:border-hairline-strong text-ink-subtle hover:text-ink text-xs font-medium px-3.5 py-1.5 rounded-full transition-colors",
    empty: "p-0 bg-transparent",
  };

  return (
    <div onClick={onClick} className={cn(variantMap[variant], className)}>
      {children}
    </div>
  );
};

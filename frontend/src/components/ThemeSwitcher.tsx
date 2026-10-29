"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Moon, Monitor, Palette, Check, Sparkles, Square, CircleDot, Grid3x3 } from "lucide-react";
import { useAppTheme, PALETTES, ThemeMode, WorkspaceBackground } from "./ThemeProvider";

interface ThemeSwitcherProps {
  align?: "left" | "right";
  compact?: boolean;
}

export function ThemeSwitcher({ align = "right", compact = false }: ThemeSwitcherProps) {
  const { mode, setMode, palette, setPalette, backgroundPattern, setBackgroundPattern, resolvedTheme, mounted } = useAppTheme();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="w-9 h-9 rounded-lg border border-border/60 bg-card/50 animate-pulse" />
    );
  }

  const activePalette = PALETTES.find((p) => p.id === palette) || PALETTES[0];

  const modes: { id: ThemeMode; label: string; icon: React.ReactNode }[] = [
    { id: "light", label: "Light", icon: <Sun className="w-3.5 h-3.5" /> },
    { id: "dark", label: "Dark", icon: <Moon className="w-3.5 h-3.5" /> },
    { id: "system", label: "System", icon: <Monitor className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle theme and color palette"
        className={`flex items-center gap-2 rounded-lg border border-border/80 bg-card/80 hover:bg-accent/80 hover:border-border text-foreground px-2.5 py-1.5 text-xs font-medium backdrop-blur-md transition-all shadow-subtle ${
          isOpen ? "ring-2 ring-primary/40 border-primary/50" : ""
        }`}
      >
        <span className="relative flex items-center justify-center">
          {resolvedTheme === "dark" ? (
            <Moon className="w-4 h-4 text-primary" />
          ) : (
            <Sun className="w-4 h-4 text-amber-500" />
          )}
          <span
            className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ring-1 ring-background"
            style={{ backgroundColor: activePalette.color }}
          />
        </span>

        {!compact && (
          <span className="hidden sm:inline-flex items-center gap-1.5 text-muted-foreground font-normal">
            <span className="font-medium text-foreground">{activePalette.name.split(" ")[1]}</span>
            <span className="text-[10px] uppercase tracking-wider px-1 py-0.5 rounded bg-muted/80 text-muted-foreground">
              {mode}
            </span>
          </span>
        )}

        <Palette className="w-3.5 h-3.5 text-muted-foreground ml-0.5" />
      </button>

      {/* Popover Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 4 }}
            transition={{ duration: 0.16, ease: "easeOut" }}
            className={`absolute mt-2 w-72 rounded-xl border border-border/80 bg-card p-3 shadow-card backdrop-blur-xl z-50 ${
              align === "right" ? "right-0" : "left-0"
            }`}
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-border/60">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                <span className="text-xs font-semibold text-foreground tracking-tight">
                  Interface Theme
                </span>
              </div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">
                5 Palettes
              </span>
            </div>

            {/* Mode Selector */}
            <div className="mb-3">
              <span className="text-[11px] font-medium text-muted-foreground block mb-1.5 px-0.5">
                Appearance Mode
              </span>
              <div className="grid grid-cols-3 gap-1 bg-muted/60 p-1 rounded-lg border border-border/40">
                {modes.map((m) => {
                  const isActive = mode === m.id;
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMode(m.id)}
                      className={`relative flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-md text-xs font-medium transition-all ${
                        isActive
                          ? "bg-card text-foreground shadow-sm font-semibold"
                          : "text-muted-foreground hover:text-foreground hover:bg-card/40"
                      }`}
                    >
                      {m.icon}
                      <span>{m.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Background Pattern Selector */}
            <div className="mb-3">
              <span className="text-[11px] font-medium text-muted-foreground block mb-1.5 px-0.5">
                Workspace Canvas
              </span>
              <div className="grid grid-cols-3 gap-1 bg-muted/60 p-1 rounded-lg border border-border/40">
                {[
                  { id: "plain", label: "Plain", icon: <Square className="w-3 h-3" /> },
                  { id: "dots", label: "Dots", icon: <CircleDot className="w-3 h-3" /> },
                  { id: "grid", label: "Grid", icon: <Grid3x3 className="w-3 h-3" /> },
                ].map((bg) => {
                  const isActive = backgroundPattern === bg.id;
                  return (
                    <button
                      key={bg.id}
                      type="button"
                      onClick={() => setBackgroundPattern(bg.id as WorkspaceBackground)}
                      className={`relative flex items-center justify-center gap-1.5 py-1 px-2 rounded-md text-[11px] font-medium transition-all ${
                        isActive
                          ? "bg-card text-foreground shadow-sm font-semibold"
                          : "text-muted-foreground hover:text-foreground hover:bg-card/40"
                      }`}
                    >
                      {bg.icon}
                      <span>{bg.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Palette Selector */}
            <div>
              <span className="text-[11px] font-medium text-muted-foreground block mb-1.5 px-0.5">
                Color Palette
              </span>
              <div className="space-y-1">
                {PALETTES.map((p) => {
                  const isSelected = palette === p.id;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setPalette(p.id)}
                      className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-left transition-all ${
                        isSelected
                          ? "bg-primary/10 border border-primary/30 text-foreground"
                          : "hover:bg-accent/60 border border-transparent text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className="w-3.5 h-3.5 rounded-full flex-shrink-0 transition-transform shadow-sm"
                          style={{
                            backgroundColor: p.color,
                            boxShadow: isSelected ? `0 0 10px ${p.color}` : "none",
                          }}
                        />
                        <div className="leading-tight">
                          <div className="text-xs font-medium text-foreground">{p.name}</div>
                          <div className="text-[10px] text-muted-foreground line-clamp-1">
                            {p.description}
                          </div>
                        </div>
                      </div>
                      {isSelected && (
                        <Check className="w-3.5 h-3.5 text-primary flex-shrink-0 ml-2" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

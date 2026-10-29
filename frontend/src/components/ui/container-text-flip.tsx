"use client";

import React, { useState, useEffect, useId } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export interface ContainerTextFlipProps {
  words?: string[];
  interval?: number;
  className?: string;
  textClassName?: string;
}

export function ContainerTextFlip({
  words = ["Gemini 3.8 Flash", "Gemini 4 Argon", "Sonar Deep Research", "Claude 3.7 Sonnet", "GPT-4o"],
  interval = 2800,
  className,
  textClassName,
}: ContainerTextFlipProps) {
  const id = useId();
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % words.length);
    }, interval);
    return () => clearInterval(timer);
  }, [words.length, interval]);

  return (
    <span
      className={cn(
        "relative inline-flex items-center justify-center overflow-hidden align-middle px-3 py-1 rounded-md bg-surface-2 border border-hairline-strong text-linear-primary font-semibold text-sm sm:text-base md:text-lg lg:text-2xl shadow-inner",
        className
      )}
    >
      <AnimatePresence mode="wait">
        <motion.span
          key={`flip-word-${index}-${id}`}
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -20, opacity: 0 }}
          transition={{ duration: 0.35, ease: "easeInOut" }}
          className={cn("whitespace-nowrap flex items-center gap-2", textClassName)}
        >
          <span className="w-2 h-2 rounded-full bg-linear-primary animate-pulse" />
          <span>{words[index]}</span>
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

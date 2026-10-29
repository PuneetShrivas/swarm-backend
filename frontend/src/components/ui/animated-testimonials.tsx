/* eslint-disable @next/next/no-img-element */
"use client";

import React, { useEffect, useState, useCallback } from "react";
import { IconArrowLeft, IconArrowRight } from "@tabler/icons-react";
import { motion, AnimatePresence } from "framer-motion";

export type Testimonial = {
  quote: string;
  name: string;
  designation: string;
  src: string;
};

export const AnimatedTestimonials = ({
  testimonials,
  autoplay = false,
}: {
  testimonials: Testimonial[];
  autoplay?: boolean;
}) => {
  const [active, setActive] = useState(0);

  const handleNext = useCallback(() => {
    setActive((prev) => (prev + 1) % testimonials.length);
  }, [testimonials.length]);

  const handlePrev = useCallback(() => {
    setActive((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  }, [testimonials.length]);

  const isActive = (index: number) => {
    return index === active;
  };

  useEffect(() => {
    if (autoplay) {
      const interval = setInterval(handleNext, 6000);
      return () => clearInterval(interval);
    }
  }, [autoplay, handleNext]);

  return (
    <div className="mx-auto max-w-sm px-4 py-16 font-sans antialiased md:max-w-4xl md:px-8">
      <div className="relative grid grid-cols-1 gap-12 md:grid-cols-2 items-center">
        <div>
          <div className="relative h-72 w-full">
            <AnimatePresence>
              {testimonials.map((testimonial, index) => (
                <motion.div
                  key={testimonial.src}
                  initial={{
                    opacity: 0,
                    scale: 0.9,
                    rotate: (index % 2 === 0 ? 3 : -3),
                  }}
                  animate={{
                    opacity: isActive(index) ? 1 : 0.4,
                    scale: isActive(index) ? 1 : 0.94,
                    rotate: isActive(index) ? 0 : (index % 2 === 0 ? 4 : -4),
                    zIndex: isActive(index) ? 30 : testimonials.length - index,
                  }}
                  exit={{
                    opacity: 0,
                    scale: 0.9,
                  }}
                  transition={{
                    duration: 0.4,
                    ease: "easeInOut",
                  }}
                  className="absolute inset-0 origin-bottom"
                >
                  <img
                    src={testimonial.src}
                    alt={testimonial.name}
                    draggable={false}
                    className="h-full w-full rounded-2xl object-cover object-center border border-hairline shadow-md"
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

        <div className="flex flex-col justify-between py-2">
          <motion.div
            key={active}
            initial={{ y: 16, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -16, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
          >
            <h3 className="text-xl sm:text-2xl font-semibold text-ink tracking-tight">
              {testimonials[active].name}
            </h3>
            <p className="text-xs text-linear-primary font-mono mt-1">
              {testimonials[active].designation}
            </p>
            <div className="mt-6 text-sm text-ink-muted leading-relaxed font-sans">
              &quot;{testimonials[active].quote}&quot;
            </div>
          </motion.div>

          <div className="flex gap-3 pt-8">
            <button
              onClick={handlePrev}
              aria-label="Previous testimonial"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-2 border border-hairline hover:bg-surface-3 hover:border-hairline-strong text-ink transition-colors"
            >
              <IconArrowLeft size={16} />
            </button>
            <button
              onClick={handleNext}
              aria-label="Next testimonial"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-2 border border-hairline hover:bg-surface-3 hover:border-hairline-strong text-ink transition-colors"
            >
              <IconArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

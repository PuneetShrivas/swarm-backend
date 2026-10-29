"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  useScroll,
  useTransform,
  motion,
} from "framer-motion";

export interface TimelineEntry {
  title: string;
  content: React.ReactNode;
}

export const Timeline = ({ data }: { data: TimelineEntry[] }) => {
  const ref = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      setHeight(rect.height);
    }
  }, [ref, data]);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start 20%", "end 70%"],
  });

  const heightTransform = useTransform(scrollYProgress, [0, 1], [0, height]);
  const opacityTransform = useTransform(scrollYProgress, [0, 0.1], [0, 1]);

  return (
    <div className="w-full bg-transparent font-sans px-4 sm:px-6 md:px-10" ref={containerRef}>
      <div ref={ref} className="relative max-w-5xl mx-auto pb-16">
        {data.map((item, index) => (
          <div
            key={index}
            className="flex justify-start pb-12 md:pb-24 md:gap-8"
          >
            <div className="sticky flex flex-col md:flex-row z-30 items-center top-28 self-start max-w-xs md:w-64">
              <div className="h-8 absolute left-2 md:left-2 w-8 rounded-full bg-surface-1 border border-hairline flex items-center justify-center">
                <div className="h-2.5 w-2.5 rounded-full bg-linear-primary" />
              </div>
              <h3 className="hidden md:block text-xl md:pl-16 font-bold text-ink">
                {item.title}
              </h3>
            </div>

            <div className="relative pl-14 pr-2 md:pl-4 w-full">
              <h3 className="md:hidden block text-base font-bold text-ink mb-2">
                {item.title}
              </h3>
              {item.content}
            </div>
          </div>
        ))}

        <div
          style={{ height: height + "px" }}
          className="absolute left-6 md:left-6 top-0 overflow-hidden w-[2px] bg-hairline [mask-image:linear-gradient(to_bottom,transparent_0%,black_10%,black_90%,transparent_100%)]"
        >
          <motion.div
            style={{
              height: heightTransform,
              opacity: opacityTransform,
            }}
            className="absolute inset-x-0 top-0 w-[2px] bg-gradient-to-b from-linear-primary via-linear-hover to-transparent rounded-full"
          />
        </div>
      </div>
    </div>
  );
};

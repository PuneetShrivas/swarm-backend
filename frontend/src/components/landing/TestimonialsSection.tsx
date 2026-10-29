"use client";

import React from "react";
import {
  AnimatedTestimonials,
  Testimonial,
} from "@/components/ui/animated-testimonials";
import { motion } from "framer-motion";
import { Highlight } from "@/components/ui/hero-highlight";

export default function TestimonialsSection() {
  const testimonials: Testimonial[] = [
    {
      quote:
        "Swarm's DAG workflow engine replaced thousands of lines of fragile glue code. We now orchestrate multi-step code generation and security audits with 100% deterministic reliability.",
      name: "Alex Rivera",
      designation: "Lead AI Platform Engineer • CloudScale",
      src: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=600&auto=format&fit=crop",
    },
    {
      quote:
        "The ability to branch conversation trees and compare agent responses side-by-side without polluting prompt history is unmatched. It cut our LLM debugging cycle in half.",
      name: "Marcus Vance",
      designation: "VP of Engineering • Nexus Intelligence",
      src: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=600&auto=format&fit=crop",
    },
    {
      quote:
        "Having sandboxed Python execution running directly in the pipeline alongside Gemini 3.8 and Perplexity Sonar citations gave us an enterprise-ready analytical workflow in days.",
      name: "Elena Rostova",
      designation: "Principal ML Architect • Synthetix",
      src: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=600&auto=format&fit=crop",
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <div className="text-center mb-6">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
        >
          Trusted by <Highlight>Autonomous Systems Engineers</Highlight>
        </motion.h2>
        <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-md mx-auto">
          Hear how engineering teams deploy production agent swarms with Swarm 2.0.
        </p>
      </div>

      <AnimatedTestimonials testimonials={testimonials} autoplay={true} />
    </div>
  );
}

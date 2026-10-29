"use client";

import React, { useState } from "react";
import { Check, ArrowRight } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { Highlight } from "@/components/ui/hero-highlight";
import Link from "next/link";

export default function PricingSection() {
  const [isYearly, setIsYearly] = useState(false);

  const plans = [
    {
      name: "Community",
      description: "For individual researchers, developers, and local prototyping.",
      price: "$0",
      period: "forever",
      features: [
        "Self-hosted FastAPI core",
        "4 Built-in Swarm Core Agents",
        "Unlimited local workflow DAGs",
        "Deterministic mock unit tests",
        "Community Discord support",
      ],
      buttonText: "Launch Open Source",
      buttonHref: "/chat",
      popular: false,
    },
    {
      name: "Cloud Pro",
      description: "For power engineers building autonomous production pipelines.",
      price: isYearly ? "$24" : "$29",
      period: isYearly ? "per month, billed annually" : "per month",
      features: [
        "Everything in Community",
        "Supabase cloud state persistence",
        "Gemini 3.8 Flash & Argon integration",
        "Perplexity Sonar citations engine",
        "Sandboxed Python code executor",
        "Live token & cost telemetry",
        "Non-linear branching dialogue tree",
      ],
      buttonText: "Start Cloud Pro",
      buttonHref: "/login",
      popular: true,
    },
    {
      name: "Enterprise",
      description: "For organizations demanding dedicated VPC clusters and compliance.",
      price: "Custom",
      period: "tailored SLAs",
      features: [
        "Everything in Cloud Pro",
        "Dedicated VPC agent clusters",
        "Custom model fine-tuning & connectors",
        "SOC2 & HIPAA compliant auditing",
        "Custom SSO & SAML authentication",
        "24/7 dedicated engineering support",
      ],
      buttonText: "Contact Sales",
      buttonHref: "mailto:enterprise@swarm.ai",
      popular: false,
    },
  ];

  return (
    <div id="pricing" className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <div className="text-center mb-10">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
        >
          Predictable, <Highlight>Developer-First Plans</Highlight>
        </motion.h2>
        <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-md mx-auto">
          Deploy locally for free or scale your agent swarm in the cloud with zero lock-in.
        </p>

        {/* Billing Switch */}
        <div className="flex items-center justify-center gap-3 mt-6">
          <span
            className={`text-xs ${
              !isYearly ? "text-ink font-semibold" : "text-ink-subtle"
            }`}
          >
            Monthly
          </span>
          <Switch
            checked={isYearly}
            onCheckedChange={setIsYearly}
            id="billing-switch"
          />
          <span
            className={`text-xs flex items-center gap-1.5 ${
              isYearly ? "text-ink font-semibold" : "text-ink-subtle"
            }`}
          >
            <span>Annual</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-semantic-success/20 text-semantic-success border border-semantic-success/30">
              Save 20%
            </span>
          </span>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan, idx) => (
          <div
            key={idx}
            className={`rounded-xl border p-6 flex flex-col justify-between transition-all ${
              plan.popular
                ? "border-linear-primary bg-surface-1 shadow-[0_0_32px_rgba(94,106,210,0.15)] relative"
                : "border-hairline bg-surface-1 hover:border-hairline-strong"
            }`}
          >
            {plan.popular && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] font-mono uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full bg-linear-primary text-white shadow-sm">
                Most Popular
              </span>
            )}

            <div>
              <div className="mb-4">
                <h3 className="text-base font-bold text-ink">{plan.name}</h3>
                <p className="text-xs text-ink-subtle mt-1">
                  {plan.description}
                </p>
              </div>

              <div className="mb-6 pb-6 border-b border-hairline">
                <span className="text-3xl font-bold font-mono text-ink">
                  {plan.price}
                </span>
                <span className="text-xs text-ink-subtle ml-1.5">
                  / {plan.period}
                </span>
              </div>

              <ul className="space-y-2.5 text-xs text-ink-muted mb-8">
                {plan.features.map((feature, fIdx) => (
                  <li key={fIdx} className="flex items-start gap-2">
                    <Check
                      size={14}
                      className="text-linear-primary shrink-0 mt-0.5"
                    />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            <Link href={plan.buttonHref} className="w-full">
              <Button
                variant={plan.popular ? "default" : "outline"}
                className="w-full flex items-center justify-center gap-1.5 text-xs"
              >
                <span>{plan.buttonText}</span>
                <ArrowRight size={13} />
              </Button>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

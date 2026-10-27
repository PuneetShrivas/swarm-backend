'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-slate-950 text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none"></div>

      <div className="z-10 max-w-5xl w-full items-center justify-between font-sans text-sm flex flex-col text-center relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex flex-col items-center"
        >
          <div className="inline-flex items-center rounded-full border border-slate-800 bg-slate-900/50 px-3 py-1 text-sm font-medium text-slate-300 mb-8 backdrop-blur-sm">
            <span className="flex h-2 w-2 rounded-full bg-blue-500 mr-2 animate-pulse"></span>
            Agent Swarm v1.0 is Live
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
            Intelligent Agents <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-600">at Your Command</span>
          </h1>

          <p className="text-xl md:text-2xl mb-12 text-slate-400 max-w-2xl font-light">
            Deploy, orchestrate, and interact with a swarm of highly specialized AI agents in a unified, modern interface.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 mb-24">
            <Link href="/login">
              <button className="px-8 py-4 rounded-full bg-white text-slate-950 font-semibold hover:bg-slate-200 transition shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)]">
                Get Started
              </button>
            </Link>
            <Link href="/chat">
              <button className="px-8 py-4 rounded-full bg-slate-900 border border-slate-800 text-white font-semibold hover:bg-slate-800 transition">
                Live Demo
              </button>
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full"
        >
          {[
            { title: "Swarm Orchestration", desc: "Seamlessly manage multiple agents working together on complex tasks." },
            { title: "Rich Data Schemas", desc: "Advanced metadata and tool calling capabilities baked into every interaction." },
            { title: "Real-time Sync", desc: "Powered by Supabase for instantaneous state updates and secure authentication." }
          ].map((feature, i) => (
            <div key={i} className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 text-left backdrop-blur-sm hover:bg-slate-800/50 transition duration-300">
              <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4">
                <div className="w-6 h-6 rounded-full border-2 border-blue-500"></div>
              </div>
              <h3 className="text-lg font-semibold text-slate-200 mb-2">{feature.title}</h3>
              <p className="text-slate-400 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </main>
  );
}
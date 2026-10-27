import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50 text-gray-900">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm flex flex-col text-center">
        <h1 className="text-4xl font-bold mb-8">Welcome to Agent Swarm</h1>
        <p className="text-xl mb-12">
          Create, manage, and interact with a swarm of highly specialized agents.
        </p>

        <div className="flex gap-4">
          <Link href="/login">
            <button className="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition">
              Login to Console
            </button>
          </Link>
          <Link href="/chat">
            <button className="px-6 py-3 rounded-lg bg-white border border-gray-300 text-gray-800 font-semibold hover:bg-gray-100 transition">
              Try Chatbot
            </button>
          </Link>
        </div>
      </div>
    </main>
  );
}
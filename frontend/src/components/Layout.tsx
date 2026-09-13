import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/", label: "Évaluation", end: true },
  { to: "/scans", label: "Scans" },
  { to: "/trends", label: "Tendances" },
];

export function Layout() {
  return (
    <div className="min-h-screen bg-[#070b14] text-zinc-100">
      <header className="sticky top-0 z-20 border-b border-zinc-800/80 bg-[#070b14]/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-emerald-400/90">
              SentinelAI · Phase 3 mesurée
            </p>
            <h1 className="text-lg font-semibold tracking-tight text-zinc-50">
              Retrieval &amp; correctifs, chiffres d’abord
            </h1>
          </div>
          <nav className="flex gap-1 rounded-full border border-zinc-800 bg-zinc-900/70 p-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `rounded-full px-4 py-1.5 text-sm transition ${
                    isActive
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "text-zinc-400 hover:text-zinc-100"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

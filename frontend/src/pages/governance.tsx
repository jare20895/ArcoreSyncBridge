import React from 'react';
import Link from 'next/link';
import { ArrowRight, ShieldCheck, Activity, Settings2 } from 'lucide-react';

const GOVERNANCE_LINKS = [
  {
    title: 'Run History',
    description: 'Review sync outcomes, failures, and operational activity.',
    href: '/runs',
    icon: Activity,
  },
  {
    title: 'Sync Definitions',
    description: 'Inspect mapping configuration, schedules, and cursor resets.',
    href: '/sync-definitions',
    icon: Settings2,
  },
  {
    title: 'Security Settings',
    description: 'Rotate secrets and review integration-level configuration.',
    href: '/settings',
    icon: ShieldCheck,
  },
];

export default function GovernancePage() {
  return (
    <div className="space-y-6">
      <div className="max-w-3xl">
        <h1 className="text-3xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">
          Governance
        </h1>
        <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
          This workspace is the governance entry point for audit-oriented workflows while the deeper approval and policy screens are still being built.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {GOVERNANCE_LINKS.map((item) => (
          <Link
            key={item.title}
            href={item.href}
            className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-light-primary/40 hover:shadow-md dark:border-gray-800 dark:bg-dark-surface"
          >
            <div className="flex items-start justify-between">
              <div className="rounded-lg bg-light-primary/10 p-2 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary">
                <item.icon size={18} />
              </div>
              <ArrowRight size={16} className="text-light-text-secondary dark:text-dark-text-secondary" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-light-text-primary dark:text-dark-text-primary">
              {item.title}
            </h2>
            <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
              {item.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

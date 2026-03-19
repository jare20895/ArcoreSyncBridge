import React from 'react';
import Link from 'next/link';
import { ArrowRight, BookOpen, Database, GitBranch, Target } from 'lucide-react';

const DOC_SECTIONS = [
  {
    title: 'Connection Inventory',
    description: 'Register databases, instances, and SharePoint connections before creating syncs.',
    href: '/database-instances',
    icon: Database,
  },
  {
    title: 'Source And Target Discovery',
    description: 'Extract source schemas and SharePoint metadata for provisioning and mapping.',
    href: '/data-sources',
    icon: Target,
  },
  {
    title: 'Sync Definitions',
    description: 'Configure mappings, schedules, CDC, and operational controls for each sync.',
    href: '/sync-definitions',
    icon: GitBranch,
  },
];

export default function DocsPage() {
  return (
    <div className="space-y-6">
      <div className="max-w-3xl">
        <div className="inline-flex items-center gap-2 rounded-full bg-light-primary/10 px-3 py-1 text-sm font-medium text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary">
          <BookOpen size={16} />
          Documentation Hub
        </div>
        <h1 className="mt-4 text-3xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">
          Product documentation is still repo-first.
        </h1>
        <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
          This route now provides a stable in-app destination instead of a 404. Use it as a lightweight help hub until the repo docs are surfaced directly in the UI.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {DOC_SECTIONS.map((section) => (
          <Link
            key={section.title}
            href={section.href}
            className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-light-primary/40 hover:shadow-md dark:border-gray-800 dark:bg-dark-surface"
          >
            <div className="flex items-start justify-between">
              <div className="rounded-lg bg-light-primary/10 p-2 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary">
                <section.icon size={18} />
              </div>
              <ArrowRight size={16} className="text-light-text-secondary dark:text-dark-text-secondary" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-light-text-primary dark:text-dark-text-primary">
              {section.title}
            </h2>
            <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
              {section.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

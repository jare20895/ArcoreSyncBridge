import React, { ReactNode, useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { cn } from '../lib/utils';
import { getCurrentUser } from '../services/api';
import { 
  LayoutDashboard, 
  Database, 
  Table,
  Target,
  RefreshCw, 
  Activity, 
  ShieldCheck, 
  BookOpen, 
  Settings, 
  Moon, 
  Sun,
  User 
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

const TABS = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Connections', href: '/database-instances', icon: Database },
  { name: 'Data Sources', href: '/data-sources', icon: Table },
  { name: 'Data Targets', href: '/data-targets', icon: Target },
  { name: 'Sync Definitions', href: '/sync-definitions', icon: RefreshCw },
  { name: 'Runs & Ledger', href: '/runs', icon: Activity },
  { name: 'Governance', href: '/governance', icon: ShieldCheck },
  { name: 'Docs', href: '/docs', icon: BookOpen },
];

export default function Layout({ children }: LayoutProps) {
  const router = useRouter();

  // Define connection-related routes
  const connectionRoutes = ['/database-instances', '/applications', '/databases', '/sharepoint-connections'];
  const isConnectionRoute = connectionRoutes.some(route => router.pathname.startsWith(route));

  const activeTab = TABS.find(tab => {
    // Special handling for Connections tab
    if (tab.name === 'Connections' && isConnectionRoute) {
      return true;
    }
    // Normal handling for other tabs
    return tab.href === '/' ? router.pathname === '/' : router.pathname.startsWith(tab.href);
  });

  const [isDarkMode, setIsDarkMode] = useState(false);
  const [principal, setPrincipal] = useState<{ email: string; role: string; auth_mode: string } | null>(null);

  useEffect(() => {
    // Check local storage or system preference
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    } else {
      setIsDarkMode(false);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  useEffect(() => {
    getCurrentUser()
      .then(setPrincipal)
      .catch(() => setPrincipal(null));
  }, []);

  const toggleDarkMode = () => {
    if (isDarkMode) {
      document.documentElement.classList.remove('dark');
      localStorage.theme = 'light';
      setIsDarkMode(false);
    } else {
      document.documentElement.classList.add('dark');
      localStorage.theme = 'dark';
      setIsDarkMode(true);
    }
  };

  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg text-light-text-primary dark:text-dark-text-primary font-sans transition-colors duration-200">
      {/* Top Banner (Fixed) */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-light-surface dark:bg-dark-surface border-b border-gray-200 dark:border-gray-800 z-50 flex items-center justify-between px-4 shadow-sm transition-colors duration-200">
        {/* Left: Logo */}
        <div className="flex items-center space-x-3 w-64">
          <div className="w-8 h-8 bg-light-primary dark:bg-dark-primary rounded flex items-center justify-center text-white font-bold">
            A
          </div>
          <span className="font-secondary font-bold text-lg tracking-tight text-light-primary dark:text-dark-primary">
            Arcore SyncBridge
          </span>
        </div>

        {/* Center: Tabs */}
        <nav className="flex items-center space-x-1">
          {TABS.map((tab) => {
            const isActive = activeTab?.name === tab.name;
            const Icon = tab.icon;
            return (
              <Link
                key={tab.name}
                href={tab.href}
                className={cn(
                  "flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-light-primary/10 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary" 
                    : "text-light-text-secondary hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-400"
                )}
              >
                <Icon size={16} />
                <span>{tab.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right: Utilities */}
        <div className="flex items-center space-x-4 w-64 justify-end">
          {principal && (
            <div
              className="hidden lg:flex flex-col items-end rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-1.5 text-right"
              title={`${principal.email} (${principal.auth_mode})`}
            >
              <span className="text-[11px] uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">
                {principal.role}
              </span>
              <span className="max-w-[140px] truncate text-xs text-light-text-primary dark:text-dark-text-primary">
                {principal.email}
              </span>
            </div>
          )}
          <button 
            onClick={toggleDarkMode}
            className="p-2 text-light-text-secondary hover:text-light-primary dark:text-gray-400 dark:hover:text-white transition-colors"
            title="Toggle Dark Mode"
          >
            {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          
          <Link href="/settings" className="p-2 text-light-text-secondary hover:text-light-primary dark:text-gray-400 dark:hover:text-white transition-colors" title="Settings">
            <Settings size={20} />
          </Link>
          
          <Link href="/settings?tab=profile" className="h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center text-xs hover:ring-2 ring-light-primary transition-all" title="Profile">
            <User size={16} className="text-gray-600 dark:text-gray-300" />
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <div className="pt-16 flex min-h-screen">
        {/* Left Sidebar (Contextual) */}
        <aside className="fixed left-0 top-16 bottom-0 w-64 bg-light-surface dark:bg-dark-surface border-r border-gray-200 dark:border-gray-800 overflow-y-auto hidden md:block">
           {/* Contextual Sidebar Content based on Active Tab */}
           <div className="p-4">
             <h3 className="text-xs font-bold text-light-text-secondary uppercase tracking-wider mb-4">
               {activeTab?.name}
             </h3>
             <ul className="space-y-1">
                {activeTab?.name === 'Dashboard' && (
                    <>
                        <li><Link href="/#overview" className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary">Overview</Link></li>
                        <li><Link href="/#diagrams" className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary">Sync Diagrams</Link></li>
                        <li><Link href="/#cdc" className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary">CDC Management</Link></li>
                        <li><Link href="/#metrics" className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary">System Metrics</Link></li>
                    </>
                )}
                {activeTab?.name === 'Sync Definitions' && (
                    <>
                        <li><Link href="/sync-definitions" className="block px-3 py-2 rounded bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium">All Definitions</Link></li>
                        <li><Link href="/sync-definitions/new" className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800">Create New</Link></li>
                    </>
                )}
                {activeTab?.name === 'Data Sources' && (
                    <>
                        <li><Link href="/data-sources" className="block px-3 py-2 rounded bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium">Inventory</Link></li>
                        <li><span className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300">Schema Extraction</span></li>
                        <li><span className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300">Provisioning</span></li>
                    </>
                )}
                {activeTab?.name === 'Data Targets' && (
                    <>
                        <li><Link href="/data-targets" className="block px-3 py-2 rounded bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium">Sites</Link></li>
                        <li><span className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300">Lists</span></li>
                        <li><span className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300">Columns</span></li>
                    </>
                )}
                {activeTab?.name === 'Connections' && (
                    <>
                        <li>
                          <Link
                            href="/applications"
                            className={cn(
                              "block px-3 py-2 rounded transition-colors",
                              router.pathname.startsWith('/applications')
                                ? "bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium"
                                : "text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary"
                            )}
                          >
                            Applications
                          </Link>
                        </li>
                        <li>
                          <Link
                            href="/databases"
                            className={cn(
                              "block px-3 py-2 rounded transition-colors",
                              router.pathname.startsWith('/databases')
                                ? "bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium"
                                : "text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary"
                            )}
                          >
                            Databases
                          </Link>
                        </li>
                        <li>
                          <Link
                            href="/database-instances"
                            className={cn(
                              "block px-3 py-2 rounded transition-colors",
                              router.pathname.startsWith('/database-instances')
                                ? "bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium"
                                : "text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary"
                            )}
                          >
                            Database Instances
                          </Link>
                        </li>
                        <li>
                          <Link
                            href="/sharepoint-connections"
                            className={cn(
                              "block px-3 py-2 rounded transition-colors",
                              router.pathname.startsWith('/sharepoint-connections')
                                ? "bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium"
                                : "text-light-text-secondary dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-primary dark:hover:text-dark-primary"
                            )}
                          >
                            SharePoint Connections
                          </Link>
                        </li>
                    </>
                )}
                {activeTab?.name === 'Runs & Ledger' && (
                    <>
                        <li><Link href="/runs" className="block px-3 py-2 rounded bg-light-primary/5 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary font-medium">Run History</Link></li>
                        <li><span className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300">Sync Ledger</span></li>
                        <li><span className="block px-3 py-2 rounded text-light-text-secondary dark:text-gray-300">Scheduled Jobs</span></li>
                    </>
                )}
                 {/* Fallback for other tabs */}
                 {!['Dashboard', 'Sync Definitions', 'Data Sources', 'Data Targets', 'Connections', 'Runs & Ledger'].includes(activeTab?.name || '') && (
                     <li className="text-sm text-gray-400 italic px-3">No tools available</li>
                 )}
             </ul>
           </div>
        </aside>

        {/* Main Workspace */}
        <main className="flex-1 md:ml-64 p-8 bg-light-bg dark:bg-dark-bg">
          {children}
        </main>
      </div>
    </div>
  );
}

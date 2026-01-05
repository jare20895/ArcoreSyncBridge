import React from 'react';
import MermaidDiagram from './MermaidDiagram';
import { generateSyncFlowMermaid } from '../../lib/generateSyncMermaid';
import { useRouter } from 'next/router';

interface AllSyncsGridViewProps {
  syncDefinitions: any[];
}

export default function AllSyncsGridView({ syncDefinitions }: AllSyncsGridViewProps) {
  const router = useRouter();

  if (!syncDefinitions || syncDefinitions.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">No sync definitions found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {syncDefinitions.map((def) => (
        <div
          key={def.id}
          onClick={() => router.push(`/sync-definitions/${def.id}`)}
          className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
        >
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-bold text-light-text-primary dark:text-dark-text-primary truncate" title={def.name}>
              {def.name}
            </h3>
            <div className="flex items-center space-x-2 mt-2">
              {def.cdc_enabled && (
                <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded">
                  CDC
                </span>
              )}
              {def.schedule_enabled && (
                <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                  Scheduled
                </span>
              )}
              <span className={`text-xs px-2 py-0.5 rounded ${
                def.sync_mode === 'TWO_WAY'
                  ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                  : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
              }`}>
                {def.sync_mode === 'TWO_WAY' ? 'Two-Way' : 'Push'}
              </span>
            </div>
          </div>
          <div className="p-4">
            <MermaidDiagram
              chart={generateSyncFlowMermaid(def)}
              className="h-64"
            />
          </div>
        </div>
      ))}
    </div>
  );
}

import React from 'react';

type ListPaginationProps = {
  offset?: number;
  total?: number;
  count: number;
  hasPrevious: boolean;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
  className?: string;
};

export function ListPagination({
  offset = 0,
  total,
  count,
  hasPrevious,
  hasNext,
  onPrevious,
  onNext,
  className = '',
}: ListPaginationProps) {
  return (
    <div className={`flex items-center justify-between px-6 py-4 text-sm ${className}`.trim()}>
      <div className="text-light-text-secondary dark:text-dark-text-secondary">
        Showing {offset + (count > 0 ? 1 : 0)}-{offset + count} of {total ?? count}
      </div>
      <div className="flex gap-2">
        <button
          onClick={onPrevious}
          disabled={!hasPrevious}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
        >
          Previous
        </button>
        <button
          onClick={onNext}
          disabled={!hasNext}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
        >
          Next
        </button>
      </div>
    </div>
  );
}

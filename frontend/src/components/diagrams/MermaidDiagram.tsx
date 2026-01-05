import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { initializeMermaid } from '../../lib/mermaidConfig';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
}

export default function MermaidDiagram({ chart, className = '' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const isDarkMode = document.documentElement.classList.contains('dark');
    initializeMermaid(isDarkMode);
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    const renderDiagram = async () => {
      try {
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to render diagram');
        console.error('Mermaid rendering error:', err);
      }
    };

    renderDiagram();
  }, [chart]);

  // Listen for dark mode changes
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const isDarkMode = document.documentElement.classList.contains('dark');
      initializeMermaid(isDarkMode);

      // Re-render diagram on theme change
      if (containerRef.current && chart) {
        const renderDiagram = async () => {
          try {
            const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
            const { svg } = await mermaid.render(id, chart);
            if (containerRef.current) {
              containerRef.current.innerHTML = svg;
            }
          } catch (err) {
            console.error('Mermaid re-rendering error:', err);
          }
        };
        renderDiagram();
      }
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    return () => observer.disconnect();
  }, [chart]);

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded">
        <p className="text-sm text-red-700 dark:text-red-300">Failed to render diagram: {error}</p>
      </div>
    );
  }

  return <div ref={containerRef} className={`mermaid-container ${className}`} />;
}

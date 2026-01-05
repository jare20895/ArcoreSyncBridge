import React, { useCallback, useMemo, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useRouter } from 'next/router';

interface InteractiveFlowDiagramProps {
  syncDefinitions: any[];
}

export default function InteractiveFlowDiagram({ syncDefinitions }: InteractiveFlowDiagramProps) {
  const router = useRouter();
  const [filters, setFilters] = useState({
    cdcEnabled: false,
    scheduled: false,
    syncMode: 'all' as 'all' | 'ONE_WAY_PUSH' | 'TWO_WAY'
  });
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [expandedTargets, setExpandedTargets] = useState<Set<string>>(new Set());

  // Generate nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Filter sync definitions
    let filtered = syncDefinitions || [];
    if (filters.cdcEnabled) filtered = filtered.filter(d => d.cdc_enabled);
    if (filters.scheduled) filtered = filtered.filter(d => d.schedule_enabled);
    if (filters.syncMode !== 'all') filtered = filtered.filter(d => d.sync_mode === filters.syncMode);

    if (filtered.length === 0) {
      nodes.push({
        id: 'empty',
        data: { label: 'No sync definitions match the selected filters' },
        position: { x: 400, y: 300 },
        style: {
          background: '#f3f4f6',
          color: '#6b7280',
          border: '2px dashed #d1d5db',
          borderRadius: '8px',
          padding: '20px',
        }
      });
      return { nodes, edges };
    }

    // Group by source - use source_table_name_resolved if source_table_name is not set
    const sources = new Set(filtered.map(d => d.source_table_name || d.source_table_name_resolved || 'Unknown'));
    const targets = new Set(filtered.map(d => d.target_list_name || 'Unknown'));

    let yOffset = 0;

    // Create source nodes (left side)
    sources.forEach((source, idx) => {
      nodes.push({
        id: `source-${source}`,
        type: 'input',
        data: { label: `📊 ${source}` },
        position: { x: 0, y: yOffset },
        style: {
          background: '#7FB3D5',
          color: '#fff',
          border: '2px solid #1B4F72',
          borderRadius: '8px',
          padding: '10px',
          fontSize: '14px',
          fontWeight: 'bold'
        }
      });
      yOffset += 100;
    });

    yOffset = 0;

    // Create target nodes (right side)
    targets.forEach((target, idx) => {
      const targetId = `target-${target}`;
      const isExpanded = expandedTargets.has(targetId);

      // Find all sync definitions pointing to this target
      const connectedSyncs = filtered.filter(def =>
        (def.target_list_name || 'Unknown') === target
      );

      const resolveSourceName = (def: any) => def.source_table_name || def.source_table_name_resolved || 'Unknown';

      nodes.push({
        id: targetId,
        type: 'output',
        data: {
          label: (
            <div style={{ textAlign: 'center', minWidth: isExpanded ? '250px' : '150px' }}>
              <div style={{ fontWeight: 'bold' }}>📋 {target}</div>
              <div style={{ fontSize: '10px', marginTop: '4px' }}>
                {connectedSyncs.length} sync{connectedSyncs.length !== 1 ? 's' : ''} {isExpanded ? '▼' : '▶'}
              </div>

              {/* Connected Syncs - shown when expanded */}
              {isExpanded && connectedSyncs.length > 0 && (
                <div style={{
                  textAlign: 'left',
                  fontSize: '10px',
                  marginTop: '8px',
                  paddingTop: '8px',
                  borderTop: '1px solid rgba(47,133,90,0.5)',
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}>
                  {connectedSyncs.map((sync: any, sIdx: number) => {
                    const modeIcon = sync.sync_mode === 'TWO_WAY' ? '↔' : '→';
                    const badges = [];
                    if (sync.cdc_enabled) badges.push('⚡');
                    if (sync.schedule_enabled) badges.push('⏰');

                    return (
                      <div key={sIdx} style={{
                        padding: '3px 0',
                        borderBottom: sIdx < connectedSyncs.length - 1 ? '1px solid rgba(47,133,90,0.2)' : 'none'
                      }}>
                        <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
                          {modeIcon} {sync.name}
                        </div>
                        <div style={{ fontSize: '9px', opacity: 0.8 }}>
                          {badges.join(' ')} {sync.field_mappings?.length || 0} fields from {resolveSourceName(sync)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )
        },
        position: { x: 800, y: yOffset },
        style: {
          background: '#6EE7B7',
          color: '#000',
          border: '2px solid #2F855A',
          borderRadius: '8px',
          padding: '10px',
          fontSize: '14px',
          fontWeight: 'bold',
          minWidth: isExpanded ? '250px' : '150px',
          cursor: 'pointer'
        }
      });
      yOffset += 100;
    });

    // Create sync definition nodes and edges (middle)
    filtered.forEach((def, idx) => {
      const syncNodeId = `sync-${def.id}`;
      const badges = [];
      if (def.cdc_enabled) badges.push('⚡');
      if (def.schedule_enabled) badges.push('⏰');

      const fieldCount = def.field_mappings?.length || 0;
      const isExpanded = expandedNodes.has(syncNodeId);

      // Build field mappings list
      const fieldMappings = def.field_mappings || [];
      const mappingsToShow = isExpanded ? fieldMappings : [];

      nodes.push({
        id: syncNodeId,
        data: {
          def,
          isExpanded,
          label: (
            <div style={{ textAlign: 'center', minWidth: isExpanded ? '300px' : '150px' }}>
              <div style={{ fontSize: '12px', marginBottom: '4px' }}>
                {badges.join(' ')}
              </div>
              <div style={{ fontWeight: 'bold' }}>{def.name}</div>
              <div style={{ fontSize: '10px', marginTop: '4px', marginBottom: isExpanded ? '8px' : '0' }}>
                {fieldCount} field{fieldCount !== 1 ? 's' : ''} {isExpanded ? '▼' : '▶'}
              </div>

              {/* Field Mappings - shown when expanded */}
              {isExpanded && mappingsToShow.length > 0 && (
                <div style={{
                  textAlign: 'left',
                  fontSize: '10px',
                  marginTop: '8px',
                  paddingTop: '8px',
                  borderTop: '1px solid rgba(255,255,255,0.3)',
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}>
                  {mappingsToShow.slice(0, 10).map((mapping: any, mIdx: number) => {
                    const arrow = mapping.sync_direction === 'BIDIRECTIONAL' ? '↔' :
                                  mapping.sync_direction === 'PUSH_ONLY' ? '→' : '←';
                    return (
                      <div key={mIdx} style={{
                        padding: '2px 0',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        {mapping.is_key && <span style={{ fontSize: '8px' }}>🔑</span>}
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {mapping.source_column_name}
                        </span>
                        <span>{arrow}</span>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {mapping.target_column_name}
                        </span>
                      </div>
                    );
                  })}
                  {mappingsToShow.length > 10 && (
                    <div style={{ padding: '4px 0', fontStyle: 'italic', opacity: 0.7 }}>
                      ... {mappingsToShow.length - 10} more
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        },
        position: { x: 400, y: idx * 120 },
        style: {
          background: def.sync_mode === 'TWO_WAY' ? '#A78BFA' : '#60A5FA',
          color: '#fff',
          border: '2px solid #4B5563',
          borderRadius: '8px',
          padding: '10px',
          minWidth: isExpanded ? '300px' : '150px',
          cursor: 'pointer'
        }
      });

      // Add edges
      const sourceName = def.source_table_name || def.source_table_name_resolved || 'Unknown';
      const targetName = def.target_list_name || 'Unknown';

      edges.push({
        id: `edge-source-${def.id}`,
        source: `source-${sourceName}`,
        target: syncNodeId,
        animated: def.cdc_enabled,
        style: { stroke: '#7FB3D5', strokeWidth: 2 }
      });

      edges.push({
        id: `edge-target-${def.id}`,
        source: syncNodeId,
        target: `target-${targetName}`,
        animated: def.cdc_enabled,
        style: { stroke: '#6EE7B7', strokeWidth: 2 },
        label: def.sync_mode === 'TWO_WAY' ? '↔' : '→',
        labelStyle: { fill: '#4B5563', fontWeight: 700 }
      });
    });

    return { nodes, edges };
  }, [syncDefinitions, filters, expandedNodes, expandedTargets]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes and edges when filters or expandedNodes change
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (node.id.startsWith('sync-')) {
      // Toggle expansion for sync nodes
      setExpandedNodes(prev => {
        const newSet = new Set(prev);
        if (newSet.has(node.id)) {
          newSet.delete(node.id);
        } else {
          newSet.add(node.id);
        }
        return newSet;
      });
    } else if (node.id.startsWith('target-')) {
      // Toggle expansion for target nodes
      setExpandedTargets(prev => {
        const newSet = new Set(prev);
        if (newSet.has(node.id)) {
          newSet.delete(node.id);
        } else {
          newSet.add(node.id);
        }
        return newSet;
      });
    }
  }, []);

  const onNodeDoubleClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (node.id.startsWith('sync-')) {
      const syncId = node.id.replace('sync-', '');
      router.push(`/sync-definitions/${syncId}`);
    }
  }, [router]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white dark:bg-dark-surface p-4 rounded border border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-6">
          <span className="font-medium text-sm text-light-text-primary dark:text-dark-text-primary">
            Filters:
          </span>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.cdcEnabled}
              onChange={(e) => setFilters({ ...filters, cdcEnabled: e.target.checked })}
              className="rounded"
            />
            <span className="text-sm text-light-text-primary dark:text-dark-text-primary">CDC Enabled</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.scheduled}
              onChange={(e) => setFilters({ ...filters, scheduled: e.target.checked })}
              className="rounded"
            />
            <span className="text-sm text-light-text-primary dark:text-dark-text-primary">Scheduled</span>
          </label>
          <select
            value={filters.syncMode}
            onChange={(e) => setFilters({ ...filters, syncMode: e.target.value as any })}
            className="text-sm border border-gray-300 dark:border-gray-600 rounded px-3 py-1 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
          >
            <option value="all">All Modes</option>
            <option value="ONE_WAY_PUSH">Push Only</option>
            <option value="TWO_WAY">Two-Way</option>
          </select>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="bg-white dark:bg-dark-surface rounded border border-gray-200 dark:border-gray-700 shadow-sm" style={{ height: '600px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          connectionMode={ConnectionMode.Loose}
          fitView
          className="dark:bg-gray-900"
        >
          <Background className="dark:bg-gray-900" />
          <Controls className="dark:bg-gray-800 dark:border-gray-700" />
          <MiniMap
            className="dark:bg-gray-800 dark:border-gray-700"
            nodeColor={(node) => {
              if (node.type === 'input') return '#7FB3D5';
              if (node.type === 'output') return '#6EE7B7';
              return '#60A5FA';
            }}
          />
        </ReactFlow>
      </div>

      <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
        💡 Tip: <strong>Click</strong> on sync nodes (purple/blue) to expand/collapse field mappings, or click on target nodes (green) to see connected syncs. <strong>Double-click</strong> sync nodes to navigate to detail page. Use mouse wheel to zoom, drag to pan.
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Save, X, ArrowRight, ArrowLeft, ArrowRightLeft, Shield } from 'lucide-react';

interface FieldMapping {
  id?: string;
  source_column_id: string;
  target_column_id: string;
  source_column_name: string;
  target_column_name: string;
  target_type: string;
  transform_rule?: string;
  is_key: boolean;
  is_readonly: boolean;
  sync_direction: string;
  is_system_field: boolean;
}

interface Column {
  id: string;
  name: string;
  data_type: string;
  is_readonly?: boolean;
  is_required?: boolean;
}

interface FieldMappingEditorProps {
  mappings: FieldMapping[];
  sourceColumns: Column[];
  targetColumns: Column[];
  onSave: (mappings: FieldMapping[]) => Promise<void>;
  readonly?: boolean;
}

const SYNC_DIRECTIONS = [
  { value: 'BIDIRECTIONAL', label: 'Bi-directional', icon: ArrowRightLeft, color: 'purple' },
  { value: 'PUSH_ONLY', label: 'Push Only', icon: ArrowRight, color: 'blue' },
  { value: 'PULL_ONLY', label: 'Pull Only', icon: ArrowLeft, color: 'green' },
];

const TARGET_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'number', label: 'Number' },
  { value: 'boolean', label: 'Boolean' },
  { value: 'dateTime', label: 'Date/Time' },
  { value: 'choice', label: 'Choice' },
  { value: 'lookup', label: 'Lookup' },
  { value: 'person', label: 'Person' },
];

const TRANSFORM_RULES = [
  { value: '', label: 'None' },
  { value: 'UPPER', label: 'Uppercase' },
  { value: 'LOWER', label: 'Lowercase' },
  { value: 'TRIM', label: 'Trim Whitespace' },
  { value: 'REGEX', label: 'Regex (Custom)' },
];

export default function FieldMappingEditor({
  mappings: initialMappings,
  sourceColumns,
  targetColumns,
  onSave,
  readonly = false
}: FieldMappingEditorProps) {
  const [mappings, setMappings] = useState<FieldMapping[]>(initialMappings);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const [newMapping, setNewMapping] = useState<Partial<FieldMapping>>({
    source_column_name: '',
    target_column_name: '',
    target_type: 'text',
    is_key: false,
    is_readonly: false,
    sync_direction: 'BIDIRECTIONAL',
    is_system_field: false,
  });

  useEffect(() => {
    setMappings(initialMappings);
    setHasChanges(false);
  }, [initialMappings]);

  const handleAdd = () => {
    if (!newMapping.source_column_name || !newMapping.target_column_name) {
      alert('Please select both source and target columns');
      return;
    }

    const sourceCol = sourceColumns.find(c => c.name === newMapping.source_column_name);
    const targetCol = targetColumns.find(c => c.name === newMapping.target_column_name);

    const mapping: FieldMapping = {
      id: `temp-${Date.now()}`,
      source_column_id: sourceCol?.id || '',
      target_column_id: targetCol?.id || '',
      source_column_name: newMapping.source_column_name!,
      target_column_name: newMapping.target_column_name!,
      target_type: newMapping.target_type || 'text',
      transform_rule: newMapping.transform_rule,
      is_key: newMapping.is_key || false,
      is_readonly: newMapping.is_readonly || false,
      sync_direction: newMapping.sync_direction || 'BIDIRECTIONAL',
      is_system_field: newMapping.is_system_field || false,
    };

    setMappings([...mappings, mapping]);
    setHasChanges(true);
    setIsAdding(false);
    setNewMapping({
      source_column_name: '',
      target_column_name: '',
      target_type: 'text',
      is_key: false,
      is_readonly: false,
      sync_direction: 'BIDIRECTIONAL',
      is_system_field: false,
    });
  };

  const handleDelete = (id: string) => {
    if (confirm('Delete this field mapping?')) {
      setMappings(mappings.filter(m => m.id !== id));
      setHasChanges(true);
    }
  };

  const handleEdit = (mapping: FieldMapping, field: keyof FieldMapping, value: any) => {
    setMappings(mappings.map(m =>
      m.id === mapping.id ? { ...m, [field]: value } : m
    ));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(mappings);
      setHasChanges(false);
      setEditingId(null);
    } catch (err) {
      alert('Failed to save mappings');
    } finally {
      setSaving(false);
    }
  };

  const getDirectionIcon = (direction: string) => {
    const config = SYNC_DIRECTIONS.find(d => d.value === direction);
    if (!config) return null;
    const Icon = config.icon;
    return <Icon size={16} className={`text-${config.color}-500`} />;
  };

  return (
    <div className="space-y-4">
      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary">
            Field Mappings
          </h3>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Configure how fields sync between source and target
          </p>
        </div>
        {!readonly && (
          <div className="flex space-x-2">
            {hasChanges && (
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center space-x-2 px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 disabled:opacity-50"
              >
                <Save size={16} />
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            )}
            <button
              onClick={() => setIsAdding(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              <Plus size={16} />
              <span>Add Mapping</span>
            </button>
          </div>
        )}
      </div>

      {/* Mappings Table */}
      <div className="bg-white dark:bg-dark-surface rounded border border-gray-200 dark:border-gray-700 shadow-sm overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Direction</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Transform</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Flags</th>
              {!readonly && <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {mappings.map((mapping) => (
              <tr key={mapping.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-4 py-3 text-sm font-mono text-light-text-primary dark:text-dark-text-primary">
                  {mapping.source_column_name}
                </td>
                <td className="px-4 py-3 text-sm font-mono text-light-text-primary dark:text-dark-text-primary">
                  {mapping.target_column_name}
                </td>
                <td className="px-4 py-3">
                  {editingId === mapping.id && !readonly ? (
                    <select
                      value={mapping.target_type}
                      onChange={(e) => handleEdit(mapping, 'target_type', e.target.value)}
                      className="text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                    >
                      {TARGET_TYPES.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  ) : (
                    <span className="text-xs text-gray-600 dark:text-gray-400">{mapping.target_type}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {editingId === mapping.id && !readonly ? (
                    <select
                      value={mapping.sync_direction}
                      onChange={(e) => handleEdit(mapping, 'sync_direction', e.target.value)}
                      className="text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                    >
                      {SYNC_DIRECTIONS.map(d => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="flex items-center space-x-1">
                      {getDirectionIcon(mapping.sync_direction)}
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {SYNC_DIRECTIONS.find(d => d.value === mapping.sync_direction)?.label}
                      </span>
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  {editingId === mapping.id && !readonly ? (
                    <select
                      value={mapping.transform_rule || ''}
                      onChange={(e) => handleEdit(mapping, 'transform_rule', e.target.value || undefined)}
                      className="text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                    >
                      {TRANSFORM_RULES.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  ) : (
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {mapping.transform_rule || 'None'}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center space-x-2">
                    {mapping.is_key && (
                      <span className="px-2 py-0.5 text-xs rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        Key
                      </span>
                    )}
                    {mapping.is_readonly && (
                      <span className="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        RO
                      </span>
                    )}
                    {mapping.is_system_field && (
                      <Shield size={14} className="text-purple-500" title="System Field" />
                    )}
                  </div>
                </td>
                {!readonly && (
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      {editingId === mapping.id ? (
                        <button
                          onClick={() => setEditingId(null)}
                          className="text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                          title="Done Editing"
                        >
                          <X size={16} />
                        </button>
                      ) : (
                        <button
                          onClick={() => setEditingId(mapping.id || null)}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(mapping.id!)}
                        className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}

            {/* Add New Mapping Row */}
            {isAdding && (
              <tr className="bg-blue-50 dark:bg-blue-900/20">
                <td className="px-4 py-3">
                  <select
                    value={newMapping.source_column_name}
                    onChange={(e) => setNewMapping({ ...newMapping, source_column_name: e.target.value })}
                    className="w-full text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                  >
                    <option value="">Select source...</option>
                    {sourceColumns.map(col => (
                      <option key={col.id} value={col.name}>{col.name}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={newMapping.target_column_name}
                    onChange={(e) => {
                      const selectedCol = targetColumns.find(c => c.name === e.target.value);
                      const isSystemField = selectedCol?.is_readonly || false;
                      const isReadonly = selectedCol?.is_readonly || false;
                      setNewMapping({
                        ...newMapping,
                        target_column_name: e.target.value,
                        is_system_field: isSystemField,
                        is_readonly: isReadonly,
                        sync_direction: isSystemField ? 'PULL_ONLY' : 'BIDIRECTIONAL'
                      });
                    }}
                    className="w-full text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                  >
                    <option value="">Select target...</option>
                    {targetColumns.map(col => (
                      <option key={col.id} value={col.name}>
                        {col.name}{col.is_readonly ? ' [System]' : ''}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={newMapping.target_type}
                    onChange={(e) => setNewMapping({ ...newMapping, target_type: e.target.value })}
                    className="w-full text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                  >
                    {TARGET_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={newMapping.sync_direction}
                    onChange={(e) => setNewMapping({ ...newMapping, sync_direction: e.target.value })}
                    className="w-full text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                  >
                    {SYNC_DIRECTIONS.map(d => (
                      <option key={d.value} value={d.value}>{d.label}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={newMapping.transform_rule || ''}
                    onChange={(e) => setNewMapping({ ...newMapping, transform_rule: e.target.value || undefined })}
                    className="w-full text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                  >
                    {TRANSFORM_RULES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <label className="flex items-center space-x-1">
                      <input
                        type="checkbox"
                        checked={newMapping.is_key}
                        onChange={(e) => setNewMapping({ ...newMapping, is_key: e.target.checked })}
                        className="rounded"
                      />
                      <span className="text-xs">Key</span>
                    </label>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleAdd}
                      className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
                      title="Add"
                    >
                      <Save size={16} />
                    </button>
                    <button
                      onClick={() => setIsAdding(false)}
                      className="text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                      title="Cancel"
                    >
                      <X size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {mappings.length === 0 && !isAdding && (
          <div className="p-8 text-center text-gray-500">
            No field mappings configured.
            <br />
            <button
              onClick={() => setIsAdding(true)}
              className="mt-2 text-light-primary dark:text-dark-primary hover:underline"
            >
              Add your first mapping
            </button>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-4 text-xs space-y-2">
        <div className="font-semibold text-gray-700 dark:text-gray-300">Sync Directions:</div>
        <div className="grid grid-cols-3 gap-4">
          {SYNC_DIRECTIONS.map(d => {
            const Icon = d.icon;
            return (
              <div key={d.value} className="flex items-center space-x-2">
                <Icon size={14} className={`text-${d.color}-500`} />
                <span className="text-gray-600 dark:text-gray-400">{d.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

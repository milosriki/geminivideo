import React, { useState, useEffect } from 'react';
import { EditTemplate, templateManager } from '../services/templateSystem';
import { AdvancedEdit } from '../types';

interface TemplateSelectorProps {
  onTemplateApply: (edits: AdvancedEdit[]) => void;
  onClose: () => void;
}

const TemplateSelector: React.FC<TemplateSelectorProps> = ({ onTemplateApply, onClose }) => {
  const [allTemplates, setAllTemplates] = useState<EditTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<EditTemplate[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'reels' | 'story' | 'feed' | 'custom'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<EditTemplate | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showImportExport, setShowImportExport] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [newTemplateDescription, setNewTemplateDescription] = useState('');
  const [importJson, setImportJson] = useState('');
  const [exportJson, setExportJson] = useState('');
  const [stats, setStats] = useState(templateManager.getTemplateStats());

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    filterTemplates();
  }, [selectedCategory, searchQuery, allTemplates]);

  const loadTemplates = () => {
    const templates = templateManager.getAllTemplates();
    setAllTemplates(templates);
    setStats(templateManager.getTemplateStats());
  };

  const filterTemplates = () => {
    let filtered = allTemplates;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(t => t.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        t =>
          t.name.toLowerCase().includes(query) ||
          t.description.toLowerCase().includes(query) ||
          t.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    setFilteredTemplates(filtered);
  };

  const handleApplyTemplate = (template: EditTemplate) => {
    const edits = templateManager.applyTemplate(template);
    onTemplateApply(edits);
    onClose();
  };

  const handleDeleteTemplate = (templateId: string) => {
    if (window.confirm('Are you sure you want to delete this custom template?')) {
      templateManager.deleteCustomTemplate(templateId);
      loadTemplates();
      if (selectedTemplate?.id === templateId) {
        setSelectedTemplate(null);
      }
    }
  };

  const handleDuplicateTemplate = (template: EditTemplate) => {
    const duplicated = templateManager.duplicateTemplate(template.id);
    if (duplicated) {
      loadTemplates();
      setSelectedTemplate(duplicated);
    }
  };

  const handleExportTemplate = (template: EditTemplate) => {
    const json = templateManager.exportTemplate(template);
    setExportJson(json);
    setShowImportExport(true);
  };

  const handleExportAllCustom = () => {
    const json = templateManager.exportAllCustomTemplates();
    setExportJson(json);
    setShowImportExport(true);
  };

  const handleImportTemplate = () => {
    try {
      const imported = templateManager.importTemplate(importJson);
      alert(`Template "${imported.name}" imported successfully!`);
      loadTemplates();
      setImportJson('');
      setShowImportExport(false);
    } catch (error) {
      alert(`Import failed: ${error}`);
    }
  };

  const handleSaveToFile = () => {
    const blob = new Blob([exportJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'video-templates.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'reels':
        return '📱';
      case 'story':
        return '📖';
      case 'feed':
        return '🖼️';
      case 'custom':
        return '⭐';
      default:
        return '🎬';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Video Templates</h2>
            <p className="text-sm text-gray-600 mt-1">
              {stats.total} templates ({stats.builtIn} built-in, {stats.custom} custom)
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExportAllCustom}
              className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            >
              Export All
            </button>
            <button
              onClick={() => setShowImportExport(true)}
              className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            >
              Import
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="p-6 border-b bg-gray-50">
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search templates by name, description, or tags..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Category Tabs */}
          <div className="flex gap-2 flex-wrap">
            {(['all', 'reels', 'story', 'feed', 'custom'] as const).map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                {getCategoryIcon(category)} {category.charAt(0).toUpperCase() + category.slice(1)}
                {category !== 'all' && ` (${stats.byCategory[category] || 0})`}
              </button>
            ))}
          </div>
        </div>

        {/* Templates Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredTemplates.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No templates found</p>
              <p className="text-gray-400 text-sm mt-2">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredTemplates.map(template => (
                <div
                  key={template.id}
                  className={`border rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer ${
                    selectedTemplate?.id === template.id ? 'ring-2 ring-blue-500' : 'border-gray-300'
                  }`}
                  onClick={() => setSelectedTemplate(template)}
                >
                  {/* Preview Image */}
                  <div className="bg-gradient-to-br from-blue-500 to-purple-600 h-32 flex items-center justify-center text-white text-4xl">
                    {getCategoryIcon(template.category)}
                  </div>

                  {/* Template Info */}
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 text-sm">{template.name}</h3>
                      <span className="text-xs text-gray-500">{template.estimatedDuration}s</span>
                    </div>
                    <p className="text-xs text-gray-600 mb-3 line-clamp-2">{template.description}</p>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1 mb-3">
                      {template.tags.slice(0, 3).map(tag => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {template.tags.length > 3 && (
                        <span className="px-2 py-1 text-gray-500 text-xs">
                          +{template.tags.length - 3}
                        </span>
                      )}
                    </div>

                    {/* Edit Count */}
                    <p className="text-xs text-gray-500 mb-3">{template.edits.length} edits included</p>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          handleApplyTemplate(template);
                        }}
                        className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors"
                      >
                        Apply
                      </button>
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          handleDuplicateTemplate(template);
                        }}
                        className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-lg transition-colors"
                        title="Duplicate"
                      >
                        📋
                      </button>
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          handleExportTemplate(template);
                        }}
                        className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-lg transition-colors"
                        title="Export"
                      >
                        💾
                      </button>
                      {template.category === 'custom' && (
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleDeleteTemplate(template.id);
                          }}
                          className="px-3 py-2 bg-red-100 hover:bg-red-200 text-red-700 text-xs rounded-lg transition-colors"
                          title="Delete"
                        >
                          🗑️
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Template Details */}
        {selectedTemplate && (
          <div className="border-t bg-gray-50 p-4">
            <div className="max-w-4xl mx-auto">
              <h3 className="font-semibold text-gray-900 mb-2">{selectedTemplate.name}</h3>
              <p className="text-sm text-gray-600 mb-3">{selectedTemplate.description}</p>
              <div className="bg-white rounded-lg p-3 border border-gray-300">
                <p className="text-xs font-semibold text-gray-700 mb-2">Included Edits:</p>
                <div className="flex flex-wrap gap-2">
                  {selectedTemplate.edits.map((edit, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-medium"
                    >
                      {edit.type}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Import/Export Modal */}
      {showImportExport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Import / Export Templates</h3>
              <button
                onClick={() => {
                  setShowImportExport(false);
                  setImportJson('');
                  setExportJson('');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Export Section */}
            {exportJson && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export (Copy or Download)
                </label>
                <textarea
                  value={exportJson}
                  readOnly
                  className="w-full h-40 px-3 py-2 border border-gray-300 rounded-lg font-mono text-xs"
                />
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(exportJson);
                      alert('Copied to clipboard!');
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                  >
                    Copy to Clipboard
                  </button>
                  <button
                    onClick={handleSaveToFile}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors"
                  >
                    Download JSON
                  </button>
                </div>
              </div>
            )}

            {/* Import Section */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Import Template (Paste JSON)
              </label>
              <textarea
                value={importJson}
                onChange={e => setImportJson(e.target.value)}
                placeholder="Paste template JSON here..."
                className="w-full h-40 px-3 py-2 border border-gray-300 rounded-lg font-mono text-xs"
              />
              <button
                onClick={handleImportTemplate}
                disabled={!importJson.trim()}
                className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
              >
                Import Template
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateSelector;

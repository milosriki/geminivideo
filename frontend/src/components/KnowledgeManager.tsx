/**
 * Knowledge Base Manager Component
 * Agent 14: Knowledge Base Hot-Reload Engineer
 *
 * Features:
 * - Category selector
 * - Version history list
 * - Upload new knowledge (JSON editor)
 * - Activate version button
 * - Current status display
 * - Reload button
 * - File import/export
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Divider,
  Tooltip,
  Snackbar,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  PlayArrow as ActivateIcon,
  GetApp as ExportIcon,
  Publish as ImportIcon,
  History as HistoryIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// TypeScript interfaces
interface VersionInfo {
  version_id: string;
  category: string;
  timestamp: string;
  checksum: string;
  size_bytes: number;
  description: string;
  author: string;
  is_active: boolean;
}

interface CategoryStatus {
  active_version: string | null;
  active_timestamp: string | null;
  total_versions: number;
  latest_version: string | null;
  cached: boolean;
}

interface KnowledgeData {
  [key: string]: any;
}

// API base URL - configure for your environment
const API_BASE_URL = import.meta.env.VITE_KNOWLEDGE_API_URL || 'http://localhost:8004';

// Knowledge categories
const CATEGORIES = [
  'brand_guidelines',
  'competitor_analysis',
  'industry_benchmarks',
  'hook_templates',
  'storyboard_templates',
  'winning_patterns',
];

export default function KnowledgeManager() {
  // State
  const [selectedCategory, setSelectedCategory] = useState<string>(CATEGORIES[0]);
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [categoryStatus, setCategoryStatus] = useState<Record<string, CategoryStatus>>({});
  const [currentData, setCurrentData] = useState<KnowledgeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Upload dialog state
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadData, setUploadData] = useState<string>('{}');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadAuthor, setUploadAuthor] = useState('');

  // Load status on mount
  useEffect(() => {
    loadStatus();
  }, []);

  // Load versions when category changes
  useEffect(() => {
    if (selectedCategory) {
      loadVersions(selectedCategory);
      loadCurrentData(selectedCategory);
    }
  }, [selectedCategory]);

  // API calls
  const loadStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/knowledge/status`);
      if (!response.ok) throw new Error('Failed to load status');
      const data = await response.json();
      setCategoryStatus(data);
    } catch (err) {
      setError(`Failed to load status: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const loadVersions = async (category: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/knowledge/${category}/versions`);
      if (!response.ok) throw new Error('Failed to load versions');
      const data = await response.json();
      setVersions(data);
    } catch (err) {
      setError(`Failed to load versions: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setVersions([]);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentData = async (category: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/knowledge/${category}?version=latest`);
      if (!response.ok) {
        if (response.status === 404) {
          setCurrentData(null);
          return;
        }
        throw new Error('Failed to load current data');
      }
      const result = await response.json();
      setCurrentData(result.data);
    } catch (err) {
      setError(`Failed to load data: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setCurrentData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    try {
      // Validate JSON
      let parsedData: KnowledgeData;
      try {
        parsedData = JSON.parse(uploadData);
      } catch (err) {
        setError('Invalid JSON format');
        return;
      }

      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: selectedCategory,
          data: parsedData,
          description: uploadDescription,
          author: uploadAuthor || 'web_user',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      setSuccess(`Uploaded successfully as version ${result.version_id}`);
      setUploadDialogOpen(false);
      setUploadData('{}');
      setUploadDescription('');
      setUploadAuthor('');

      // Reload data
      await loadVersions(selectedCategory);
      await loadStatus();
      await loadCurrentData(selectedCategory);
    } catch (err) {
      setError(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleActivateVersion = async (versionId: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/knowledge/activate/${selectedCategory}/${versionId}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Activation failed');
      }

      setSuccess(`Version ${versionId} activated successfully`);

      // Reload data
      await loadVersions(selectedCategory);
      await loadStatus();
      await loadCurrentData(selectedCategory);
    } catch (err) {
      setError(`Activation failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVersion = async (versionId: string) => {
    if (!confirm(`Are you sure you want to delete version ${versionId}?`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/knowledge/${selectedCategory}/versions/${versionId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Deletion failed');
      }

      setSuccess(`Version ${versionId} deleted successfully`);

      // Reload data
      await loadVersions(selectedCategory);
      await loadStatus();
    } catch (err) {
      setError(`Deletion failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReload = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/knowledge/reload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: selectedCategory }),
      });

      if (!response.ok) throw new Error('Reload failed');

      setSuccess(`Category ${selectedCategory} reloaded successfully`);
      await loadCurrentData(selectedCategory);
    } catch (err) {
      setError(`Reload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReloadAll = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/knowledge/reload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      if (!response.ok) throw new Error('Reload failed');

      const result = await response.json();
      setSuccess(`Reloaded ${result.count} categories successfully`);
      await loadStatus();
      await loadCurrentData(selectedCategory);
    } catch (err) {
      setError(`Reload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!currentData) {
      setError('No data to export');
      return;
    }

    const dataStr = JSON.stringify(currentData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedCategory}_${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const data = JSON.parse(text);
        setUploadData(JSON.stringify(data, null, 2));
        setUploadDialogOpen(true);
      } catch (err) {
        setError('Failed to parse imported file');
      }
    };
    input.click();
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Knowledge Base Manager
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Agent 14: Hot-Reload Knowledge Management System
      </Typography>

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                label="Category"
              >
                {CATEGORIES.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    {categoryStatus[cat]?.total_versions > 0 && (
                      <Chip
                        label={categoryStatus[cat].total_versions}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={8}>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<UploadIcon />}
                onClick={() => setUploadDialogOpen(true)}
              >
                Upload
              </Button>
              <Button
                variant="outlined"
                startIcon={<ImportIcon />}
                onClick={handleImport}
              >
                Import
              </Button>
              <Button
                variant="outlined"
                startIcon={<ExportIcon />}
                onClick={handleExport}
                disabled={!currentData}
              >
                Export
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleReload}
              >
                Reload
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleReloadAll}
              >
                Reload All
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={3}>
        {/* Status Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Status
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {categoryStatus[selectedCategory] ? (
                <Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Active Version
                    </Typography>
                    <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                      {categoryStatus[selectedCategory].active_version || 'None'}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Last Updated
                    </Typography>
                    <Typography variant="body1">
                      {categoryStatus[selectedCategory].active_timestamp
                        ? formatDate(categoryStatus[selectedCategory].active_timestamp!)
                        : 'Never'}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Versions
                    </Typography>
                    <Typography variant="body1">
                      {categoryStatus[selectedCategory].total_versions}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Cache Status
                    </Typography>
                    <Chip
                      label={categoryStatus[selectedCategory].cached ? 'Cached' : 'Not Cached'}
                      color={categoryStatus[selectedCategory].cached ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </Box>
              ) : (
                <Typography color="text.secondary">Loading status...</Typography>
              )}
            </CardContent>
          </Card>

          {/* Current Data Preview */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Data
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {currentData ? (
                <Box
                  sx={{
                    maxHeight: 300,
                    overflow: 'auto',
                    bgcolor: 'grey.100',
                    p: 1,
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                  }}
                >
                  <pre>{JSON.stringify(currentData, null, 2)}</pre>
                </Box>
              ) : (
                <Typography color="text.secondary">No active version</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Version History */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <HistoryIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Version History</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />

              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : versions.length > 0 ? (
                <List>
                  {versions.map((version) => (
                    <ListItem
                      key={version.version_id}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                        bgcolor: version.is_active ? 'action.selected' : 'background.paper',
                      }}
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                              {version.version_id}
                            </Typography>
                            {version.is_active && (
                              <Chip label="ACTIVE" color="success" size="small" />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {formatDate(version.timestamp)} • {version.author}
                            </Typography>
                            {version.description && (
                              <Typography variant="body2" color="text.secondary">
                                {version.description}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary">
                              {formatBytes(version.size_bytes)} • {version.checksum.slice(0, 8)}...
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {!version.is_active && (
                            <Tooltip title="Activate this version">
                              <IconButton
                                edge="end"
                                onClick={() => handleActivateVersion(version.version_id)}
                                color="primary"
                              >
                                <ActivateIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          {!version.is_active && (
                            <Tooltip title="Delete this version">
                              <IconButton
                                edge="end"
                                onClick={() => handleDeleteVersion(version.version_id)}
                                color="error"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', p: 3 }}>
                  <Typography color="text.secondary">
                    No versions available. Upload your first version to get started.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Upload New Knowledge Version</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              label="Description"
              fullWidth
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              sx={{ mb: 2 }}
              placeholder="Describe this version..."
            />

            <TextField
              label="Author"
              fullWidth
              value={uploadAuthor}
              onChange={(e) => setUploadAuthor(e.target.value)}
              sx={{ mb: 2 }}
              placeholder="Your name or email"
            />

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Knowledge Data (JSON)
            </Typography>
            <TextField
              multiline
              rows={15}
              fullWidth
              value={uploadData}
              onChange={(e) => setUploadData(e.target.value)}
              placeholder='{"key": "value"}'
              sx={{
                fontFamily: 'monospace',
                '& textarea': { fontFamily: 'monospace', fontSize: '0.9rem' },
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpload} variant="contained" disabled={loading}>
            {loading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for messages */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error">
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success">
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
}

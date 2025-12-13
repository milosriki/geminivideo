import React, { Suspense, useState } from 'react';
import { ErrorBoundary } from '../layout/ErrorBoundary';
import ProVideoEditor from '../ProVideoEditor';
import { useAuth } from '@/contexts/AuthContext';
import { apiUrl } from '@/config/api';

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-950">
    <div className="text-center">
      <svg className="animate-spin h-10 w-10 text-indigo-500 mx-auto mb-4" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p className="text-gray-400">Loading Video Editor...</p>
    </div>
  </div>
);

interface ProVideoEditorWrapperProps {
  projectId?: string;
}

export const ProVideoEditorWrapper: React.FC<ProVideoEditorWrapperProps> = ({ projectId }) => {
  const { currentUser, getIdToken } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleSave = async (project: any) => {
    if (!currentUser) {
      console.error('User not authenticated, cannot save project');
      window.dispatchEvent(new CustomEvent('project-save-error', {
        detail: { message: 'You must be logged in to save projects' }
      }));
      return;
    }

    setIsSaving(true);
    try {
      const token = await getIdToken();

      // Save project data to backend
      const endpoint = projectId
        ? apiUrl(`/projects/${projectId}`)
        : apiUrl('/projects');

      const method = projectId ? 'PUT' : 'POST';

      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          userId: currentUser.uid,
          projectId,
          name: project.name,
          type: 'video',
          timeline: project.timeline,
          clips: project.clips,
          effects: project.effects,
          audio: project.audio,
          metadata: {
            duration: project.duration,
            resolution: project.resolution,
            fps: project.fps,
            lastModified: new Date().toISOString(),
            ...project.metadata
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to save project');
      }

      const savedProject = await response.json();
      console.log('Project saved successfully:', savedProject);

      // Show success notification
      window.dispatchEvent(new CustomEvent('project-saved', {
        detail: {
          project: savedProject,
          message: `Project "${project.name}" saved successfully`
        }
      }));

      return savedProject;
    } catch (error) {
      console.error('Failed to save project:', error);
      window.dispatchEvent(new CustomEvent('project-save-error', {
        detail: {
          error,
          message: error instanceof Error ? error.message : 'Failed to save project'
        }
      }));
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = async (settings: any) => {
    if (!currentUser) {
      console.error('User not authenticated, cannot export video');
      window.dispatchEvent(new CustomEvent('export-error', {
        detail: { message: 'You must be logged in to export videos' }
      }));
      return;
    }

    setIsExporting(true);
    try {
      const token = await getIdToken();

      // Step 1: Create render job
      const renderResponse = await fetch(apiUrl('/render/remix'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          userId: currentUser.uid,
          projectId,
          scenes: settings.scenes || [],
          variant: settings.variant || 'default',
          output_format: settings.format || 'mp4',
          resolution: settings.resolution || '1920x1080',
          fps: settings.fps || 30,
          bitrate: settings.bitrate || '5000k',
          codec: settings.codec || 'h264',
          audio: {
            enabled: settings.includeAudio !== false,
            bitrate: settings.audioBitrate || '192k'
          },
          transitions: settings.transitions !== false,
          watermark: settings.watermark || null,
          metadata: {
            exportedAt: new Date().toISOString(),
            exportedBy: currentUser.uid,
            ...settings.metadata
          }
        })
      });

      if (!renderResponse.ok) {
        const errorData = await renderResponse.json();
        throw new Error(errorData.message || 'Failed to create render job');
      }

      const renderJob = await renderResponse.json();
      const jobId = renderJob.job_id;

      console.log('Render job created:', renderJob);

      // Show processing notification
      window.dispatchEvent(new CustomEvent('export-started', {
        detail: {
          jobId,
          message: 'Video export started. This may take a few minutes...',
          estimatedCompletion: renderJob.estimated_completion
        }
      }));

      // Step 2: Poll for render status
      const pollInterval = 3000; // Poll every 3 seconds
      const maxPolls = 200; // Max 10 minutes (200 * 3s)
      let pollCount = 0;

      const checkStatus = async (): Promise<any> => {
        const statusResponse = await fetch(apiUrl(`/render/status/${jobId}`), {
          headers: {
            ...(token && { 'Authorization': `Bearer ${token}` })
          }
        });

        if (!statusResponse.ok) {
          throw new Error('Failed to check render status');
        }

        const status = await statusResponse.json();
        console.log('Render status:', status);

        // Update progress notification
        if (status.progress !== undefined) {
          window.dispatchEvent(new CustomEvent('export-progress', {
            detail: {
              jobId,
              progress: status.progress,
              status: status.status,
              message: status.message
            }
          }));
        }

        if (status.status === 'COMPLETED') {
          // Export completed successfully
          window.dispatchEvent(new CustomEvent('export-completed', {
            detail: {
              jobId,
              outputUrl: status.output_url,
              message: 'Video exported successfully!',
              downloadUrl: status.output_url
            }
          }));
          return status;
        } else if (status.status === 'FAILED') {
          throw new Error(status.error || 'Video export failed');
        } else if (pollCount >= maxPolls) {
          throw new Error('Export timed out. Please check your exports page.');
        } else {
          // Continue polling
          pollCount++;
          await new Promise(resolve => setTimeout(resolve, pollInterval));
          return checkStatus();
        }
      };

      return await checkStatus();

    } catch (error) {
      console.error('Failed to export video:', error);
      window.dispatchEvent(new CustomEvent('export-error', {
        detail: {
          error,
          message: error instanceof Error ? error.message : 'Failed to export video'
        }
      }));
      throw error;
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <ProVideoEditor
          projectId={projectId}
          onSave={handleSave}
          onExport={handleExport}
        />
      </Suspense>
    </ErrorBoundary>
  );
};

export default ProVideoEditorWrapper;

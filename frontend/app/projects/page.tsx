"use client";

import { ClientHeader } from "@/components/ClientHeader";
import { api, Project } from "@/lib/api";
import Link from "next/link";
import { Badge } from "@/components/Badge";
import { UserSync } from "@/components/UserSync";
import { useEffect, useState } from "react";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('🔵 useEffect STARTED');
    
    const fetchProjects = async () => {
      console.log('🟢 fetchProjects function called');
      
      setLoading(true);
      setError(null);
      
      try {
        console.log('🟡 About to call api.getProjects()');
        const response = await api.getProjects();
        console.log('✅ API response:', response);
        
        if (response && response.projects) {
          console.log('✅ Setting projects:', response.projects.length);
          setProjects(response.projects);
          setError(null);
        } else {
          console.error('❌ Invalid response:', response);
          setError('Invalid response from server');
          setProjects([]);
        }
      } catch (e) {
        // Only log as error if it's not a 401/403 (expected during initial load)
        const isAuthError = e instanceof Error && (
          e.message.includes('401') || 
          e.message.includes('403') ||
          e.message.includes('Unauthorized') ||
          e.message.includes('Forbidden')
        );
        
        if (!isAuthError) {
          console.error('❌ Error in fetchProjects:', e);
        } else {
          console.log('🟡 Auth error (expected during initial load), will retry after sync');
        }
        
        const errorMessage = e instanceof Error ? e.message : "Failed to load projects";
        // Don't show auth errors in UI - they'll be resolved after sync
        if (!isAuthError) {
          setError(errorMessage);
        }
        setProjects([]);
      } finally {
        console.log('🟣 Setting loading to false');
        setLoading(false);
      }
    };

    // Wait for token to be available before making first API call
    const waitForTokenAndFetch = async () => {
      const { getApiToken } = await import('@/lib/api');
      
      // Check if token already exists
      const existingToken = getApiToken();
      if (existingToken) {
        console.log('🟡 Token exists, fetching projects immediately');
        fetchProjects();
        return;
      }
      
      // Wait for user-synced event (with timeout)
      console.log('🟡 No token found, waiting for user sync...');
      const timeout = setTimeout(() => {
        console.log('🟡 Token wait timeout, attempting fetch anyway');
        fetchProjects();
      }, 5000); // 5 second timeout
      
      const handleUserSynced = () => {
        console.log('🟢 User synced event received, fetching projects');
        clearTimeout(timeout);
        fetchProjects();
      };
      
      window.addEventListener('user-synced', handleUserSynced, { once: true });
      
      // Also check periodically if token becomes available
      const checkInterval = setInterval(() => {
        const token = getApiToken();
        if (token) {
          console.log('🟡 Token found during periodic check');
          clearTimeout(timeout);
          clearInterval(checkInterval);
          window.removeEventListener('user-synced', handleUserSynced);
          fetchProjects();
        }
      }, 200);
      
      // Cleanup interval after timeout
      setTimeout(() => {
        clearInterval(checkInterval);
      }, 5000);
    };

    // Start the wait-and-fetch process
    waitForTokenAndFetch();

    // Listen for user-synced event to retry after token refresh (for subsequent syncs)
    const handleUserSyncedRetry = () => {
      console.log('🟢 User synced event received (retry)');
      fetchProjects();
    };

    window.addEventListener('user-synced', handleUserSyncedRetry);

    return () => {
      console.log('🔴 Cleanup: removing event listener');
      window.removeEventListener('user-synced', handleUserSyncedRetry);
    };
  }, []);

  console.log('🔴 ProjectsPage render - loading:', loading, 'projects:', projects.length, 'error:', error);

  return (
    <div className="min-h-screen bg-gray-50">
      <UserSync />
      <ClientHeader />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
            <p className="mt-2 text-gray-600">
              Manage your projects and view error analytics
            </p>
          </div>
          <Link
            href="/projects/new"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Create New Project
          </Link>
        </div>

        {loading && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500">Loading projects...</p>
          </div>
        )}

        {!loading && error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {!loading && !error && (
          projects.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-gray-500 mb-4">No projects yet</p>
              <Link
                href="/projects/new"
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                Create your first project →
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {projects.map((project) => (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <h2 className="text-xl font-semibold text-gray-900">
                      {project.name}
                    </h2>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">Key:</span>
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono">
                        {project.project_key}
                      </code>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">Errors:</span>
                      <Badge variant={project.error_count && project.error_count > 0 ? "error" : "default"}>
                        {project.error_count || 0}
                      </Badge>
                    </div>
                    
                    {project.repo_config && (
                      <div className="text-sm text-gray-500">
                        <span className="font-medium">Repo:</span>{" "}
                        {project.repo_config.owner}/{project.repo_config.repo}
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )
        )}
      </main>
    </div>
  );
}


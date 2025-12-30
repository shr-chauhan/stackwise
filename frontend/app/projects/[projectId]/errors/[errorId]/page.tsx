"use client";

import { ClientHeader } from "@/components/ClientHeader";
import { api, ErrorEventWithAnalysis } from "@/lib/api";
import { Badge } from "@/components/Badge";
import Link from "next/link";
import { UserSync } from "@/components/UserSync";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function ErrorDetailPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const errorId = params.errorId as string;
  const errorIdNum = parseInt(errorId, 10);

  const [errorData, setErrorData] = useState<ErrorEventWithAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isNaN(errorIdNum)) {
      setError("Invalid error ID");
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        // Wait for token
        await new Promise<void>((resolve) => {
          const token = localStorage.getItem('debug_ai_api_token');
          if (token) {
            resolve();
            return;
          }
          const timeout = setTimeout(resolve, 2000);
          const handler = () => {
            clearTimeout(timeout);
            window.removeEventListener('user-synced', handler);
            resolve();
          };
          window.addEventListener('user-synced', handler, { once: true });
        });

        const data = await api.getErrorEventWithAnalysis(errorIdNum);
        setErrorData(data);
      } catch (e) {
        console.error('Failed to fetch error details:', e);
        setError(e instanceof Error ? e.message : "Failed to load error details");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [errorIdNum]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <UserSync />
        <ClientHeader />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500">Loading error details...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !errorData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <UserSync />
        <ClientHeader />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <Link
              href={`/projects/${projectId}`}
              className="text-indigo-600 hover:text-indigo-700 text-sm mb-4 inline-block"
            >
              ← Back to Project
            </Link>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error || "Error not found"}</p>
          </div>
        </main>
      </div>
    );
  }

  const { event, analysis } = errorData;

  return (
    <div className="min-h-screen bg-gray-50">
      <UserSync />
      <ClientHeader />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <Link
            href={`/projects/${projectId}`}
            className="text-indigo-600 hover:text-indigo-700 text-sm mb-4 inline-block"
          >
            ← Back to Project
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Error Details</h1>
        </div>

        <div className="space-y-6">
          {/* Error Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Error Information
            </h2>
            
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">Timestamp</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(event.timestamp).toLocaleString()}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Status Code</dt>
                <dd className="mt-1">
                  {event.status_code ? (
                    <Badge
                      variant={
                        event.status_code >= 500
                          ? "error"
                          : event.status_code >= 400
                          ? "warning"
                          : "default"
                      }
                    >
                      {event.status_code}
                    </Badge>
                  ) : (
                    <span className="text-sm text-gray-500">N/A</span>
                  )}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Method</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <code className="bg-gray-100 px-2 py-1 rounded">
                    {event.payload.method}
                  </code>
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Path</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <code className="bg-gray-100 px-2 py-1 rounded">
                    {event.payload.path}
                  </code>
                </dd>
              </div>
              
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-gray-500">Error Message</dt>
                <dd className="mt-1 text-sm text-gray-900 bg-red-50 border border-red-200 rounded p-3">
                  {event.payload.message}
                </dd>
              </div>
            </dl>
          </div>

          {/* Stack Trace */}
          {event.payload.stack && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Stack Trace
              </h2>
              <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-xs overflow-x-auto">
                <pre className="whitespace-pre-wrap">{event.payload.stack}</pre>
              </div>
            </div>
          )}

          {/* AI Analysis */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">AI Analysis</h2>
              {analysis ? (
                <div className="flex gap-2">
                  <Badge variant="success">Analyzed</Badge>
                  <Badge variant="default">{analysis.model}</Badge>
                  {analysis.confidence && (
                    <Badge variant="default">Confidence: {analysis.confidence}</Badge>
                  )}
                </div>
              ) : (
                <Badge variant="warning">Pending</Badge>
              )}
            </div>
            
            {analysis ? (
              <div className="prose max-w-none">
                <div className="bg-gray-50 border border-gray-200 rounded p-4 text-sm text-gray-900 whitespace-pre-wrap">
                  {analysis.analysis_text}
                </div>
                <div className="mt-4 text-xs text-gray-500">
                  Analysis generated at {new Date(analysis.created_at).toLocaleString()}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
                <p className="text-gray-600">
                  AI analysis is being generated. This may take a few moments.
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Refresh the page to check for updates.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}



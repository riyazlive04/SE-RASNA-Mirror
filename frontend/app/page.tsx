"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { uploadCall, getBaseline, getBaselineTrends, generateBaseline } from "@/lib/api";
import type { LeadType, CallStage, Baseline, BaselineTrend } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";

export default function UploadPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();

  // IMPORTANT: All hooks must be called before any conditional returns
  // This ensures React hooks are called in the same order every render
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    agent_name: "",
    customer_name: "",
    call_type: "",
    lead_type: "warm" as LeadType,
    call_stage: "main" as CallStage,
    deck_shared: false,
  });
  const [audioFile, setAudioFile] = useState<File | null>(null);

  // Phase 8.2: Baseline and trend state
  const [baseline, setBaseline] = useState<Baseline | null>(null);
  const [trends, setTrends] = useState<BaselineTrend | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  // Phase 8.2: Fetch baseline and trends when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchBaselineData();
    }
  }, [isAuthenticated]);

  const fetchBaselineData = async () => {
    try {
      const baselineData = await getBaseline();
      setBaseline(baselineData);

      // Only fetch trends if baseline exists
      if (baselineData) {
        const trendsData = await getBaselineTrends();
        setTrends(trendsData);
      }
    } catch (err) {
      // Silently fail - baseline is optional
      console.error("Failed to fetch baseline data:", err);
    }
  };

  const handleRegenerateBaseline = async () => {
    setIsRegenerating(true);
    setError(null);
    try {
      await generateBaseline();
      await fetchBaselineData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to regenerate baseline");
    } finally {
      setIsRegenerating(false);
    }
  };

  // Show loading while checking auth (after all hooks are called)
  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.agent_name.trim()) {
      setError("Agent name is required");
      return;
    }

    if (!formData.call_type.trim()) {
      setError("Call type is required");
      return;
    }

    if (!audioFile) {
      setError("Audio file is required");
      return;
    }

    setIsLoading(true);

    try {
      const call = await uploadCall({
        ...formData,
        customer_name: formData.customer_name || undefined,
        audio_file: audioFile,
      });

      router.push(`/calls/${call.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-light text-gray-900 mb-1">
                SE RASNA Mirror
              </h1>
              <p className="text-sm text-gray-600">Welcome, {user?.name}</p>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 underline"
            >
              Log out
            </button>
          </div>
          <p className="text-gray-600 text-center">
            Upload a sales call for analysis and reflection
          </p>
        </div>

        {/* Phase 8.2: Baseline Staleness Banner */}
        {baseline && baseline.is_stale && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-amber-900 mb-1">
                  Baseline may be outdated
                </h3>
                <p className="text-sm text-amber-800">
                  Your baseline may be outdated. Regenerate to reflect your latest best calls.
                </p>
              </div>
              <button
                onClick={handleRegenerateBaseline}
                disabled={isRegenerating}
                className="ml-4 px-4 py-2 bg-amber-600 text-white text-sm rounded-md hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {isRegenerating ? "Regenerating..." : "Regenerate Baseline"}
              </button>
            </div>
          </div>
        )}

        {/* Phase 8.2: Baseline Evolution Trends */}
        {baseline && (
          <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Your Baseline Evolution
            </h2>
            {trends ? (
              <>
                <p className="text-sm text-gray-700 mb-4">{trends.summary}</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {trends.improved_dimensions.length > 0 && (
                    <div className="bg-green-50 rounded-md p-4">
                      <h3 className="text-sm font-medium text-green-800 mb-2">
                        ↑ Improved
                      </h3>
                      <ul className="space-y-1">
                        {trends.improved_dimensions.map((dim, idx) => (
                          <li key={idx} className="text-sm text-green-700 capitalize">
                            {dim.replace(/_/g, " ")}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {trends.declined_dimensions.length > 0 && (
                    <div className="bg-red-50 rounded-md p-4">
                      <h3 className="text-sm font-medium text-red-800 mb-2">
                        ↓ Declined
                      </h3>
                      <ul className="space-y-1">
                        {trends.declined_dimensions.map((dim, idx) => (
                          <li key={idx} className="text-sm text-red-700 capitalize">
                            {dim.replace(/_/g, " ")}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {trends.stable_dimensions.length > 0 && (
                    <div className="bg-gray-50 rounded-md p-4">
                      <h3 className="text-sm font-medium text-gray-700 mb-2">
                        → Stable
                      </h3>
                      <ul className="space-y-1">
                        {trends.stable_dimensions.map((dim, idx) => (
                          <li key={idx} className="text-sm text-gray-600 capitalize">
                            {dim.replace(/_/g, " ")}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-600">
                Trends will appear after you regenerate your baseline at least twice.
              </p>
            )}
          </div>
        )}

        <div className="bg-white shadow-sm rounded-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Agent Name */}
            <div>
              <label
                htmlFor="agent_name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Agent Name *
              </label>
              <input
                type="text"
                id="agent_name"
                value={formData.agent_name}
                onChange={(e) =>
                  setFormData({ ...formData, agent_name: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-gray-400 focus:border-transparent outline-none"
                placeholder="John Smith"
              />
            </div>

            {/* Customer Name */}
            <div>
              <label
                htmlFor="customer_name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Customer Name
              </label>
              <input
                type="text"
                id="customer_name"
                value={formData.customer_name}
                onChange={(e) =>
                  setFormData({ ...formData, customer_name: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-gray-400 focus:border-transparent outline-none"
                placeholder="Acme Corp (optional)"
              />
            </div>

            {/* Call Type */}
            <div>
              <label
                htmlFor="call_type"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Call Type *
              </label>
              <input
                type="text"
                id="call_type"
                value={formData.call_type}
                onChange={(e) =>
                  setFormData({ ...formData, call_type: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-gray-400 focus:border-transparent outline-none"
                placeholder="Sales, Support, Discovery, etc."
              />
            </div>

            {/* Lead Type */}
            <div>
              <label
                htmlFor="lead_type"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Lead Type *
              </label>
              <select
                id="lead_type"
                value={formData.lead_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    lead_type: e.target.value as LeadType,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-gray-400 focus:border-transparent outline-none bg-white"
              >
                <option value="hot">Hot</option>
                <option value="warm">Warm</option>
                <option value="cold">Cold</option>
              </select>
            </div>

            {/* Call Stage */}
            <div>
              <label
                htmlFor="call_stage"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Call Stage *
              </label>
              <select
                id="call_stage"
                value={formData.call_stage}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    call_stage: e.target.value as CallStage,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-gray-400 focus:border-transparent outline-none bg-white"
              >
                <option value="qualification">Qualification</option>
                <option value="main">Main</option>
                <option value="follow-up">Follow-up</option>
              </select>
            </div>

            {/* Deck Shared */}
            <div>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={formData.deck_shared}
                  onChange={(e) =>
                    setFormData({ ...formData, deck_shared: e.target.checked })
                  }
                  className="w-4 h-4 text-gray-600 border-gray-300 rounded focus:ring-2 focus:ring-gray-400"
                />
                <span className="text-sm text-gray-700">
                  Presentation deck was shared
                </span>
              </label>
            </div>

            {/* Audio File */}
            <div>
              <label
                htmlFor="audio_file"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Audio File *
              </label>
              <input
                type="file"
                id="audio_file"
                accept=".wav,.mp3,.m4a,.flac,.ogg"
                onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-gray-400 focus:border-transparent outline-none file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
              />
              <p className="mt-1 text-xs text-gray-500">
                Supported: WAV, MP3, M4A, FLAC, OGG (max 50MB)
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gray-800 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? "Uploading..." : "Upload Call"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

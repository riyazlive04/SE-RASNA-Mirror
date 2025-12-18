"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import { getCall, transcribeCall, evaluateCall, markAsBaseline, unmarkAsBaseline } from "@/lib/api";
import type { Call } from "@/lib/types";

export default function CallAnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [call, setCall] = useState<Call | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isTogglingBaseline, setIsTogglingBaseline] = useState(false);

  const fetchCall = async () => {
    try {
      const data = await getCall(id);
      setCall(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load call");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCall();
  }, [id]);

  const handleTranscribe = async () => {
    if (!call) return;
    setIsTranscribing(true);
    setError(null);

    try {
      await transcribeCall(id);
      await fetchCall();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transcription failed");
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleEvaluate = async () => {
    if (!call) return;
    setIsEvaluating(true);
    setError(null);

    try {
      await evaluateCall(id);
      await fetchCall();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleToggleBaseline = async () => {
    if (!call) return;
    setIsTogglingBaseline(true);
    setError(null);

    try {
      if (call.is_baseline) {
        await unmarkAsBaseline(id);
      } else {
        await markAsBaseline(id);
      }
      await fetchCall();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle baseline");
    } finally {
      setIsTogglingBaseline(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading call analysis...</div>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-light text-gray-900 mb-2">
            Call not found
          </h1>
          <a href="/" className="text-gray-600 hover:text-gray-800 underline">
            Return to upload
          </a>
        </div>
      </div>
    );
  }

  const canTranscribe = call.transcription.status === "pending";
  const canEvaluate = call.transcription.status === "completed" && call.evaluation.status === "pending";
  const hasEvaluation = call.evaluation.result !== null;
  const canToggleBaseline = call.transcription.status === "completed" && call.evaluation.status === "completed";

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-light text-gray-900">
              Call Analysis
            </h1>
            <a
              href="/"
              className="text-sm text-gray-600 hover:text-gray-800 underline"
            >
              Upload another
            </a>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>Call #{call.id}</span>
            <span>•</span>
            <span className="capitalize">{call.lead_type} lead</span>
            <span>•</span>
            <span className="capitalize">{call.call_stage} stage</span>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            <span className="font-medium">Agent:</span> {call.agent_name}
            {call.customer_name && (
              <>
                <span className="mx-2">•</span>
                <span className="font-medium">Customer:</span>{" "}
                {call.customer_name}
              </>
            )}
          </div>
          {call.is_baseline && (
            <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
              ⭐ This call is part of your baseline
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Actions */}
        <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Actions</h2>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <button
                onClick={handleTranscribe}
                disabled={!canTranscribe || isTranscribing}
                className="w-full py-2 px-4 bg-gray-800 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isTranscribing
                  ? "Transcribing..."
                  : "Transcribe Call"}
              </button>
              <p className="mt-2 text-xs text-gray-500">
                Status: <span className="capitalize">{call.transcription.status}</span>
              </p>
            </div>
            <div className="flex-1">
              <button
                onClick={handleEvaluate}
                disabled={!canEvaluate || isEvaluating}
                className="w-full py-2 px-4 bg-gray-800 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isEvaluating ? "Evaluating..." : "Evaluate Call"}
              </button>
              <p className="mt-2 text-xs text-gray-500">
                Status: <span className="capitalize">{call.evaluation.status}</span>
              </p>
            </div>
            <div className="flex-1">
              <button
                onClick={handleToggleBaseline}
                disabled={!canToggleBaseline || isTogglingBaseline}
                className="w-full py-2 px-4 bg-amber-600 text-white rounded-md hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isTogglingBaseline
                  ? "Updating..."
                  : call.is_baseline
                  ? "Unmark as Best Call ⭐"
                  : "Mark as Best Call ⭐"}
              </button>
              <p className="mt-2 text-xs text-gray-500">
                {call.is_baseline ? "Baseline call" : "Not marked as baseline"}
              </p>
            </div>
          </div>
        </div>

        {/* Evaluation Results */}
        {hasEvaluation && (
          <>
            {/* Overall Score */}
            <div className="bg-white shadow-sm rounded-lg p-8 mb-6 text-center">
              <div className="text-6xl font-light text-gray-900 mb-2">
                {call.evaluation.result.scores.overall}
              </div>
              <div className="text-sm text-gray-600 uppercase tracking-wide">
                Overall RASNA Score
              </div>
              {call.evaluation.result.llm_used !== undefined && (
                <div className="mt-3 text-xs text-gray-400">
                  {call.evaluation.result.llm_used
                    ? "AI-powered analysis"
                    : "Standard analysis"}
                </div>
              )}
            </div>

            {/* RASNA Breakdown */}
            <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                RASNA Breakdown
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <div className="text-2xl font-light text-gray-900 mb-1">
                    {call.evaluation.result.scores.rapport}
                  </div>
                  <div className="text-sm text-gray-600">Rapport</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <div className="text-2xl font-light text-gray-900 mb-1">
                    {call.evaluation.result.scores.situation}
                  </div>
                  <div className="text-sm text-gray-600">Situation</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <div className="text-2xl font-light text-gray-900 mb-1">
                    {call.evaluation.result.scores.pain}
                  </div>
                  <div className="text-sm text-gray-600">Pain</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <div className="text-2xl font-light text-gray-900 mb-1">
                    {call.evaluation.result.scores.need}
                  </div>
                  <div className="text-sm text-gray-600">Need</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <div className="text-2xl font-light text-gray-900 mb-1">
                    {call.evaluation.result.scores.ask}
                  </div>
                  <div className="text-sm text-gray-600">Ask</div>
                </div>
              </div>
            </div>

            {/* Strengths */}
            <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Strengths
              </h2>
              <ul className="space-y-3">
                {call.evaluation.result.strengths.map((strength, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-gray-400 mr-3">•</span>
                    <span className="text-gray-700">{strength}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Improvements */}
            <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Areas for Improvement
              </h2>
              <ul className="space-y-3">
                {call.evaluation.result.improvements.map((improvement, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-gray-400 mr-3">•</span>
                    <span className="text-gray-700">{improvement}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Next Call Focus */}
            <div className="bg-gray-100 rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-2">
                Next Call Focus
              </h2>
              <p className="text-gray-700 leading-relaxed">
                {call.evaluation.result.next_call_focus}
              </p>
            </div>
          </>
        )}

        {/* Empty States */}
        {!hasEvaluation && (
          <div className="bg-white shadow-sm rounded-lg p-12 text-center">
            <p className="text-gray-500">
              {call.transcription.status === "pending"
                ? "Transcribe the call to begin analysis"
                : call.transcription.status === "completed"
                ? "Evaluate the call to see RASNA analysis"
                : "Transcription failed. Please try again or upload a new call."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

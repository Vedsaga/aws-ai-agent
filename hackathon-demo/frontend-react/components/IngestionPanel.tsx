"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { submitReport } from "@/lib/api-client";
import { subscribeToJobStatus, StatusUpdate } from "@/lib/appsync-client";
import { getStoredUser } from "@/lib/auth";
import {
  showValidationErrorToast,
  showSuccessToast,
  showErrorToast,
} from "@/lib/toast-utils";
import { useAppContext } from "@/contexts/AppContext";
import DomainSelector from "./DomainSelector";
import ExecutionStatusPanel, { AgentStatus } from "./ExecutionStatusPanel";
import ClarificationDialog, { LowConfidenceField } from "./ClarificationDialog";
import {
  extractLowConfidenceFields,
  formatEnhancedText,
} from "@/lib/confidence-utils";

export default function IngestionPanel() {
  const { selectedDomain, setSelectedDomain, addChatMessage } = useAppContext();
  const [reportText, setReportText] = useState("");
  const [originalReportText, setOriginalReportText] = useState("");
  const [images, setImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState<
    Record<string, AgentStatus>
  >({});
  const [agentNames, setAgentNames] = useState<string[]>([]);
  const [showStatusPanel, setShowStatusPanel] = useState(false);
  const [showClarification, setShowClarification] = useState(false);
  const [lowConfidenceFields, setLowConfidenceFields] = useState<
    LowConfidenceField[]
  >([]);
  const [clarificationRound, setClarificationRound] = useState(0);
  const [agentOutputs, setAgentOutputs] = useState<any[]>([]);

  useEffect(() => {
    if (!jobId || !selectedDomain) return;

    const user = getStoredUser();
    if (!user) return;

    // Show status panel when job starts
    setShowStatusPanel(true);

    // Subscribe to status updates for this specific job
    const subscription = subscribeToJobStatus(
      user.userId,
      jobId,
      (update: StatusUpdate) => {
        const message = `${update.agentName}: ${update.message}`;
        setStatusMessages((prev) => [...prev, message]);

        // Update agent status
        const newStatus: AgentStatus = {
          agentName: update.agentName,
          status: update.status as AgentStatus["status"],
          message: update.message,
          confidence: update.confidence,
          timestamp: update.timestamp,
        };

        setAgentStatuses((prev) => ({
          ...prev,
          [update.agentName]: newStatus,
        }));

        // Add agent to list if not already present
        setAgentNames((prev) => {
          if (!prev.includes(update.agentName)) {
            return [...prev, update.agentName];
          }
          return prev;
        });

        // Collect agent outputs for confidence checking
        if (update.status === "complete" && update.confidence !== undefined) {
          setAgentOutputs((prev) => [
            ...prev,
            {
              agent_name: update.agentName,
              output: {
                confidence: update.confidence,
              },
            },
          ]);
        }

        // Add to chat history
        addChatMessage(selectedDomain, {
          id: `${Date.now()}-${Math.random()}`,
          type: "agent",
          content: message,
          timestamp: new Date().toISOString(),
          metadata: {
            jobId: update.jobId,
            agentName: update.agentName,
            status: update.status,
            confidence: update.confidence,
          },
        });

        if (update.status === "complete") {
          // Check if all agents are complete
          const updatedStatuses = {
            ...agentStatuses,
            [update.agentName]: newStatus,
          };

          const allComplete = Object.values(updatedStatuses).every(
            (status) =>
              status.status === "complete" || status.status === "error",
          );

          if (allComplete) {
            setLoading(false);
            setShowStatusPanel(false);

            // Check for low confidence fields
            const currentOutputs = [...agentOutputs];
            if (update.confidence !== undefined) {
              currentOutputs.push({
                agent_name: update.agentName,
                output: {
                  confidence: update.confidence,
                },
              });
            }

            const lowConfFields = extractLowConfidenceFields(
              currentOutputs,
              0.9,
            );

            // Only show clarification if we haven't exceeded max rounds
            if (lowConfFields.length > 0 && clarificationRound < 3) {
              setLowConfidenceFields(lowConfFields);
              setShowClarification(true);
            } else {
              setSuccess(true);
              showSuccessToast(
                "Processing complete",
                "Your report has been processed successfully",
              );
            }
          }
        } else if (update.status === "error") {
          setLoading(false);
          showErrorToast(`${update.agentName} failed`, update.message);
        }
      },
      (error) => {
        console.error("Status subscription error:", error);
        showErrorToast("Connection error", "Lost connection to status updates");
        setShowStatusPanel(false);
      },
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [jobId, selectedDomain, addChatMessage, agentStatuses]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const maxImages = 5;
    const maxSize = 5 * 1024 * 1024; // 5MB

    const newImages: string[] = [];
    const errors: string[] = [];

    Array.from(files)
      .slice(0, maxImages - images.length)
      .forEach((file) => {
        if (file.size > maxSize) {
          errors.push(`Image ${file.name} exceeds 5MB limit`);
          return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
          if (event.target?.result) {
            newImages.push(event.target.result as string);
            if (
              newImages.length ===
              Math.min(files.length, maxImages - images.length)
            ) {
              setImages((prev) => [...prev, ...newImages]);
            }
          }
        };
        reader.readAsDataURL(file);
      });

    if (errors.length > 0) {
      showValidationErrorToast(errors);
    }
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const errors: string[] = [];
    if (!selectedDomain) {
      errors.push("Please select a domain");
    }
    if (!reportText.trim()) {
      errors.push("Report text is required");
    }

    if (errors.length > 0) {
      showValidationErrorToast(errors);
      return;
    }

    // TypeScript guard - we know selectedDomain is not null here
    if (!selectedDomain) return;

    // Store original text on first submission
    if (!originalReportText) {
      setOriginalReportText(reportText);
    }

    setLoading(true);
    setStatusMessages([]);
    setSuccess(false);
    setJobId(null);
    setAgentOutputs([]);

    // Add user message to chat history
    addChatMessage(selectedDomain, {
      id: `${Date.now()}-${Math.random()}`,
      type: "user",
      content: reportText,
      timestamp: new Date().toISOString(),
    });

    const response = await submitReport(selectedDomain, reportText, images);

    if (response.data?.job_id) {
      setJobId(response.data.job_id);
      setStatusMessages(["Report submitted. Processing..."]);
      setAgentStatuses({});
      setAgentNames([]);
      showSuccessToast("Report submitted", "Your report is being processed");
    } else {
      // Error toast is already shown by API client
      setLoading(false);
    }
  };

  const handleClarificationSubmit = (
    clarifications: Record<string, string>,
  ) => {
    // Append clarification to original text
    const enhancedText = formatEnhancedText(originalReportText, clarifications);

    // Increment clarification round
    setClarificationRound((prev) => prev + 1);

    // Update report text and re-submit
    setReportText(enhancedText);
    setShowClarification(false);

    // Re-submit with enhanced context
    setTimeout(() => {
      const form = document.querySelector("form");
      if (form) {
        form.dispatchEvent(
          new Event("submit", { cancelable: true, bubbles: true }),
        );
      }
    }, 100);
  };

  const handleClarificationSkip = () => {
    setShowClarification(false);
    setSuccess(true);
    showSuccessToast(
      "Processing complete",
      "Your report has been processed (with low confidence)",
    );
  };

  const handleReset = () => {
    setReportText("");
    setOriginalReportText("");
    setImages([]);
    setStatusMessages([]);
    setJobId(null);
    setSuccess(false);
    setLoading(false);
    setAgentStatuses({});
    setAgentNames([]);
    setShowStatusPanel(false);
    setShowClarification(false);
    setLowConfidenceFields([]);
    setClarificationRound(0);
    setAgentOutputs([]);
  };

  return (
    <div className="h-full flex flex-col bg-card p-4 overflow-hidden">
      <h2 className="text-xl font-bold mb-4 text-foreground">Submit Report</h2>

      <form
        onSubmit={handleSubmit}
        className="flex-1 flex flex-col overflow-hidden"
      >
        {/* Domain Selection */}
        <div className="mb-4">
          <label
            htmlFor="domain"
            className="block text-sm font-medium text-foreground mb-1"
          >
            Domain
          </label>
          <DomainSelector
            selectedDomain={selectedDomain}
            onDomainChange={setSelectedDomain}
          />
        </div>

        {/* Report Text */}
        <div className="mb-4 flex-1 flex flex-col min-h-0">
          <label
            htmlFor="report"
            className="block text-sm font-medium text-foreground mb-1"
          >
            Report Description
          </label>
          <textarea
            id="report"
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
            disabled={loading}
            placeholder="Describe the incident or issue..."
            className="flex-1 px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring resize-none bg-background text-foreground"
          />
        </div>

        {/* Image Upload */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-foreground mb-1">
            Images (max 5, 5MB each)
          </label>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handleImageUpload}
            disabled={loading || images.length >= 5}
            className="w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
          />

          {images.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {images.map((img, index) => (
                <div key={index} className="relative">
                  <Image
                    src={img}
                    alt={`Upload ${index + 1}`}
                    width={64}
                    height={64}
                    className="w-16 h-16 object-cover rounded"
                  />
                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    disabled={loading}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Clarification Dialog */}
        {showClarification && jobId && (
          <ClarificationDialog
            isOpen={showClarification}
            jobId={jobId}
            lowConfidenceFields={lowConfidenceFields}
            onSubmit={handleClarificationSubmit}
            onSkip={handleClarificationSkip}
          />
        )}

        {/* Execution Status Panel */}
        {showStatusPanel && jobId && agentNames.length > 0 && (
          <div className="mb-4">
            <ExecutionStatusPanel
              jobId={jobId}
              agentStatuses={agentStatuses}
              agentNames={agentNames}
            />
          </div>
        )}

        {/* Status Messages (fallback for simple text display) */}
        {!showStatusPanel && statusMessages.length > 0 && (
          <div className="mb-4 p-3 bg-muted rounded-md max-h-32 overflow-y-auto custom-scrollbar">
            {statusMessages.map((msg, index) => (
              <div key={index} className="text-sm text-foreground mb-1">
                {msg}
              </div>
            ))}
          </div>
        )}

        {/* Success Message */}
        {success && jobId && (
          <div className="mb-4 p-3 bg-green-500/10 rounded-md">
            <div className="text-sm text-green-500">
              ✓ Report submitted successfully! Job ID: {jobId}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading || !selectedDomain || !reportText.trim()}
            className="flex-1 py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Processing..." : "Submit Report"}
          </button>

          {(success || statusMessages.length > 0) && (
            <button
              type="button"
              onClick={handleReset}
              disabled={loading}
              className="py-2 px-4 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring"
            >
              New Report
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

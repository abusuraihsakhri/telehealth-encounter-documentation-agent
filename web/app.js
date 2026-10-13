"use strict";

const $ = (id) => document.getElementById(id);
const form = $("audit-form");
const runButton = $("run");
const copyButton = $("copy");
let backendAvailable = false;
let modeReady = false;
let evaluations = 0;
let lastOutput = "";

function setMode(server) {
  backendAvailable = server;
  modeReady = true;
  $("mode").textContent = server ? "Connected to local API" : "Browser demonstration";
  $("metric-mode").textContent = server ? "API" : "Preview";
  if (!server) $("metric-audit").textContent = "Not available";
}

async function checkBackend() {
  if (window.location.protocol === "file:" || window.location.hostname.endsWith(".github.io")) {
    setMode(false);
    return;
  }
  try {
    const response = await fetch("./health", { cache: "no-store" });
    if (!response.ok || !(response.headers.get("content-type") || "").includes("application/json")) {
      setMode(false);
      return;
    }
    const health = await response.json();
    if (health.service !== "telehealth-encounter-documentation-agent") {
      setMode(false);
      return;
    }
    setMode(true);
    await updateServerMetrics();
  } catch {
    setMode(false);
  }
}

async function updateServerMetrics() {
  if (!backendAvailable) return;
  try {
    const response = await fetch("./metrics", { cache: "no-store" });
    if (!response.ok) return;
    const metrics = await response.json();
    const count = Number(metrics.audit_blocks_total);
    if (Number.isSafeInteger(count) && count >= 0) $("metric-audit").textContent = String(count);
  } catch {
    $("metric-audit").textContent = "Unavailable";
  }
}

function validateInput() {
  if (!form.reportValidity()) return null;
  const primary = Number($("primary").value);
  const secondary = $("secondary").value.trim() === "" ? 0 : Number($("secondary").value);
  if (!Number.isFinite(primary) || !Number.isFinite(secondary)) {
    throw new Error("Both measurements must be finite numeric values.");
  }
  const taskId = $("task-id").value.trim();
  const targetId = $("target-id").value.trim();
  if (!taskId || !targetId) throw new Error("Task ID and synthetic target ID are required.");
  return {
    task_id: taskId,
    target_identifier: targetId,
    primary_metric: primary,
    secondary_metric: secondary,
    status_descriptor: $("descriptor").value.trim() || "NOMINAL",
    is_critical_flag: $("critical").checked
  };
}

function browserPreview(payload) {
  const alerts = [];
  if (payload.primary_metric > 25) {
    alerts.push({ worker: "InvariantQCWorker", urgency: "ELEVATED_RISK",
      summary: "Primary metric exceeds the demonstration threshold of 25" });
  }
  if (payload.is_critical_flag || payload.secondary_metric > 12) {
    alerts.push({ worker: "SafetyEscalationWorker",
      urgency: payload.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      summary: "Critical flag or secondary metric exceeds the demonstration threshold of 12" });
  }
  if (["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"].some(
    (keyword) => payload.status_descriptor.toUpperCase().includes(keyword)
  )) {
    alerts.push({ worker: "ProtocolConformanceWorker", urgency: "ELEVATED_RISK",
      summary: "Descriptor matches a configured keyword" });
  }
  const critical = alerts.some((alert) => alert.urgency === "CRITICAL_STAT_PANIC");
  const elevated = alerts.length > 0;
  return {
    mode: "LOCAL_BROWSER_PREVIEW",
    disclaimer: "Illustrative logic only; not a clinical or billing assessment.",
    task_id: payload.task_id,
    target_identifier: payload.target_identifier,
    overall_urgency: critical ? "CRITICAL_STAT_PANIC" : elevated ? "ELEVATED_RISK" : "ROUTINE",
    integrity_status: critical ? "RECALIBRATION_REQUIRED" : elevated ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
    total_alerts: alerts.length,
    alerts,
    audit_hash: null,
    audit_verification: "Not applicable: no HMAC key or signed audit ledger in browser preview"
  };
}

function showResult(result, caption) {
  lastOutput = JSON.stringify(result, null, 2);
  $("result").textContent = lastOutput;
  $("result-caption").textContent = caption;
  copyButton.disabled = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  let payload;
  try {
    payload = validateInput();
    if (!payload) return;
  } catch (error) {
    showResult({ error: error.message }, "Input validation failed; no task evaluated.");
    return;
  }
  runButton.disabled = true;
  runButton.textContent = "Evaluating…";
  try {
    if (!modeReady) await checkBackend();
    if (!backendAvailable) {
      showResult(browserPreview(payload), "Browser-only preview. No data sent, no audit signature created.");
    } else {
      const response = await fetch("./api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        const reason = typeof data.detail === "string" ? data.detail : "API rejected the request";
        showResult({ error: reason, status: response.status }, "Server rejected the task; no result was recorded.");
        return;
      }
      showResult(data, "Result generated by the local FastAPI server; audit hash is server-generated.");
      await updateServerMetrics();
    }
    evaluations += 1;
    $("metric-count").textContent = String(evaluations);
  } catch {
    showResult({ error: "Local API unavailable. No task was evaluated. Retry or use a static browser preview." },
      "Connection failed; no fallback dossier or signature was fabricated.");
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Evaluate task";
  }
});

copyButton.addEventListener("click", async () => {
  if (!lastOutput) return;
  try {
    await navigator.clipboard.writeText(lastOutput);
    $("result-caption").textContent = "Result copied to clipboard.";
  } catch {
    $("result-caption").textContent = "Clipboard not available in this browser or context.";
  }
});

checkBackend();

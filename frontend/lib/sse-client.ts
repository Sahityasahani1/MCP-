/**
 * Robust Client-side SSE Stream Consumer for Next.js.
 * Parses line-delimited Server-Sent Events with error resilience.
 */

export interface SSECallbacks {
  onThought?: (content: string) => void;
  onToolStart?: (tool: string, args: Record<string, any>) => void;
  onToolResult?: (tool: string, result: any) => void;
  onHITLRequired?: (data: { dataset_id: string; approval_token: string; cleaning_recipe: any }) => void;
  onTextDelta?: (content: string) => void;
  onCostAudit?: (data: { provider: string; model: string; prompt_tokens: number; completion_tokens: number; cost_usd: number }) => void;
  onComplete?: (sessionId: string) => void;
  onError?: (errorMessage: string) => void;
}

export async function consumeSSEStream(
  url: string,
  payload: Record<string, any>,
  callbacks: SSECallbacks,
  signal?: AbortSignal
): Promise<void> {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      const errText = await response.text();
      callbacks.onError?.(`HTTP ${response.status}: ${errText}`);
      return;
    }

    if (!response.body) {
      callbacks.onError?.("ReadableStream not supported on this browser.");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || ""; // Keep partial chunk in buffer

      for (const block of lines) {
        const cleanBlock = block.trim();
        if (!cleanBlock.startsWith("data:")) continue;

        const jsonStr = cleanBlock.replace(/^data:\s*/, "");
        try {
          const event = JSON.parse(jsonStr);
          switch (event.type) {
            case "thought":
              callbacks.onThought?.(event.content);
              break;
            case "tool_start":
              callbacks.onToolStart?.(event.tool, event.args);
              break;
            case "tool_result":
              callbacks.onToolResult?.(event.tool, event.result);
              break;
            case "hitl_required":
              callbacks.onHITLRequired?.({
                dataset_id: event.dataset_id,
                approval_token: event.approval_token,
                cleaning_recipe: event.cleaning_recipe,
              });
              break;
            case "text_delta":
              callbacks.onTextDelta?.(event.content);
              break;
            case "cost_audit":
              callbacks.onCostAudit?.(event);
              break;
            case "complete":
              callbacks.onComplete?.(event.session_id);
              break;
            case "error":
              callbacks.onError?.(event.error_message);
              break;
          }
        } catch (e) {
          console.warn("Failed to parse SSE JSON block:", jsonStr, e);
        }
      }
    }
  } catch (err: any) {
    if (err.name === "AbortError") {
      console.log("SSE Stream aborted by user.");
    } else {
      callbacks.onError?.(err.message || "Unknown stream error");
    }
  }
}

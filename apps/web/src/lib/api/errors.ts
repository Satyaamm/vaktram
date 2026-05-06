// Shared FastAPI error-payload parser.
//
// FastAPI shapes its `detail` field three ways and the frontend has to
// handle all of them safely — rendering the raw object as a React child
// crashes with "Objects are not valid as a React child" (error #31).
//
//   1. Pydantic validation:  detail: [{ loc, msg, type }]   ← list of errors
//   2. Plain string:          detail: "Meeting not found"
//   3. Structured error:      detail: { error: "weak_password", message: "..." }
//
// This helper always returns `{ code, message }` strings — never an object —
// so callers can safely setError(message) and toast.
//
// Use:
//   const { code, message } = parseApiError(await res.json());

export interface ParsedApiError {
  code: string | null;
  message: string;
}

const FALLBACK = "Something went wrong. Please try again.";

export function parseApiError(payload: unknown, fallback = FALLBACK): ParsedApiError {
  if (!payload || typeof payload !== "object") {
    return { code: null, message: fallback };
  }

  const detail = (payload as { detail?: unknown }).detail;

  // Plain string detail
  if (typeof detail === "string" && detail.trim()) {
    return { code: null, message: detail };
  }

  // Pydantic validation: list of {loc, msg, type}
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown; loc?: unknown };
    const msg = typeof first?.msg === "string" ? first.msg : null;
    const loc = Array.isArray(first?.loc) ? first.loc.slice(1).join(".") : null;
    if (msg) {
      return { code: "validation_error", message: loc ? `${loc}: ${msg}` : msg };
    }
  }

  // Structured: { error: "...", message: "..." }
  if (detail && typeof detail === "object") {
    const d = detail as { error?: unknown; message?: unknown };
    const msg = typeof d.message === "string" ? d.message : null;
    const code = typeof d.error === "string" ? d.error : null;
    if (msg) return { code, message: msg };
  }

  // Top-level message (some endpoints return { message: ... })
  const top = (payload as { message?: unknown }).message;
  if (typeof top === "string" && top.trim()) {
    return { code: null, message: top };
  }

  return { code: null, message: fallback };
}

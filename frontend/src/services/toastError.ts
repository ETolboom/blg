import type { ToastServiceMethods } from "primevue/toastservice";
import { ApiError } from "./api";

/**
 * Extract a human-readable message from a thrown value. Prefers the
 * `detail` carried by an {@link ApiError} (already parsed from FastAPI's
 * `{detail}` shape), then a caller-supplied fallback, then `String(error)`.
 */
export function getErrorDetail(error: unknown, fallback?: string): string {
    if (error instanceof ApiError) {
        return error.detail ?? fallback ?? error.message;
    }
    return fallback ?? String(error);
}

interface ToastErrorOptions {
    /** Toast lifetime in ms. Omitted ⇒ PrimeVue default (sticky). */
    life?: number;
    /** Message to show when the error is not an ApiError (or carries no detail). */
    fallback?: string;
    /** Severity; defaults to "error". Use "warn" for non-fatal failures. */
    severity?: "error" | "warn";
}

/**
 * Show an error toast with a consistent shape, replacing the
 * `error instanceof ApiError ? error.detail : String(error)` boilerplate.
 */
export function toastError(
    toast: ToastServiceMethods,
    summary: string,
    error: unknown,
    options: ToastErrorOptions = {},
): void {
    toast.add({
        severity: options.severity ?? "error",
        summary,
        detail: getErrorDetail(error, options.fallback),
        ...(options.life !== undefined ? { life: options.life } : {}),
    });
}

/**
 * Extract the `message` string from a backend success response of the
 * `{ message: string }` shape (e.g. delete/update endpoints). Returns the
 * caller-supplied fallback when the field is absent or not a string.
 */
export function getMessage(data: unknown, fallback?: string): string | undefined {
    if (data && typeof data === "object" && "message" in data) {
        const message = (data as { message: unknown }).message;
        if (typeof message === "string") return message;
    }
    return fallback;
}

interface ToastSuccessOptions {
    /** Toast lifetime in ms. Defaults to 3000. */
    life?: number;
    /** Detail to show when the response carries no `message`. */
    fallback?: string;
    /** Severity; defaults to "success". Use "info" for neutral notices. */
    severity?: "success" | "info";
}

/**
 * Show a success toast, surfacing the backend's `{message}` as the detail when
 * present. The mirror image of {@link toastError} for the success envelope.
 */
export function toastSuccess(
    toast: ToastServiceMethods,
    summary: string,
    data?: unknown,
    options: ToastSuccessOptions = {},
): void {
    toast.add({
        severity: options.severity ?? "success",
        summary,
        detail: getMessage(data, options.fallback),
        life: options.life ?? 3000,
    });
}

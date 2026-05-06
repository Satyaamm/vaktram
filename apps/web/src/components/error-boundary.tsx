"use client";

import React from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

// Top-level error boundary. Without one, a render-time exception (e.g.
// rendering an object as a React child, hitting React error #31) blanks
// the whole app with the unhelpful "Application error: a client-side
// exception has occurred". This boundary catches it, logs it, and shows
// a friendly retry surface so the user can recover with one click.
//
// Wrap once at the route-group root (auth, dashboard, marketing layouts).
// For per-section boundaries (e.g. dashboard widgets that may fail
// independently), wrap individual <Section/> children too.

interface Props {
  children: React.ReactNode;
  fallback?: (error: Error, reset: () => void) => React.ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Single place to wire Sentry / Bugsnag later. Until then, console
    // is enough — production stack traces show up via the browser's
    // native error reporter and the source map served by Vercel.
    console.error("Caught render error:", error, info);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    if (this.props.fallback) return this.props.fallback(this.state.error, this.reset);
    return <DefaultFallback error={this.state.error} reset={this.reset} />;
  }
}

function DefaultFallback({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="max-w-md rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-amber-50 text-amber-700">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="mt-5 text-xl font-semibold tracking-tight text-slate-900">
          Something broke on this screen
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          The rest of the app should still work. Try again, or go back to the
          dashboard. If this keeps happening, drop us a line at{" "}
          <a
            href="mailto:hello@vaktram.com"
            className="font-medium text-slate-900 hover:underline"
          >
            hello@vaktram.com
          </a>
          .
        </p>
        {process.env.NODE_ENV !== "production" && (
          <pre className="mt-5 max-h-32 overflow-auto rounded-md bg-slate-50 p-3 text-left text-[11px] text-slate-600">
            {error.message}
          </pre>
        )}
        <div className="mt-6 flex justify-center gap-2">
          <Button
            onClick={reset}
            className="h-10 gap-2 rounded-md bg-slate-950 px-5 text-white hover:bg-slate-800"
          >
            <RefreshCcw className="h-4 w-4" />
            Try again
          </Button>
        </div>
      </div>
    </div>
  );
}

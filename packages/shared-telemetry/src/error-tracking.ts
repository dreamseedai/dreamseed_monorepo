// Error tracking utilities for frontend and backend

export interface ErrorContext {
  userId?: string;
  sessionId?: string;
  url?: string;
  userAgent?: string;
  timestamp?: number;
  customData?: Record<string, any>;
}

export interface ErrorReport {
  message: string;
  stack?: string;
  name: string;
  context: ErrorContext;
  severity: 'low' | 'medium' | 'high' | 'critical';
  fingerprint?: string;
}

export interface ErrorTrackingConfig {
  endpoint?: string;
  debug?: boolean;
  sampleRate?: number;
  maxErrorsPerSession?: number;
  ignorePatterns?: RegExp[];
}

class ErrorTracker {
  private config: ErrorTrackingConfig;
  private errorCount = 0;
  private sessionId: string;

  constructor(config: ErrorTrackingConfig = {}) {
    this.config = {
      endpoint: '/api/telemetry/errors',
      debug: false,
      sampleRate: 1.0,
      maxErrorsPerSession: 50,
      ignorePatterns: [
        /Script error/i,
        /Non-Error promise rejection/i,
        /ResizeObserver loop limit exceeded/i,
      ],
      ...config,
    };

    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private shouldSample(): boolean {
    return Math.random() < (this.config.sampleRate || 1.0);
  }

  private shouldIgnore(error: Error): boolean {
    if (!this.config.ignorePatterns) {
      return false;
    }

    return this.config.ignorePatterns.some(pattern =>
      pattern.test(error.message) || pattern.test(error.name)
    );
  }

  private createFingerprint(error: Error): string {
    // Create a simple fingerprint based on error message and stack
    const message = error.message || '';
    const stack = error.stack || '';
    const firstStackLine = stack.split('\n')[1] || '';

    return btoa(message + firstStackLine).substring(0, 16);
  }

  private sendError(errorReport: ErrorReport): void {
    if (!this.shouldSample()) {
      return;
    }

    if (this.errorCount >= (this.config.maxErrorsPerSession || 50)) {
      return;
    }

    this.errorCount++;

    const payload = {
      ...errorReport,
      sessionId: this.sessionId,
      timestamp: Date.now(),
    };

    if (this.config.debug) {
      console.error('Error Report:', payload);
    }

    // Send to error tracking endpoint
    if (this.config.endpoint) {
      fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      }).catch((sendError) => {
        console.error('Failed to send error report:', sendError);
      });
    }
  }

  public captureError(
    error: Error,
    context: Partial<ErrorContext> = {},
    severity: ErrorReport['severity'] = 'medium'
  ): void {
    if (this.shouldIgnore(error)) {
      return;
    }

    const errorReport: ErrorReport = {
      message: error.message,
      stack: error.stack,
      name: error.name,
      context: {
        url: typeof window !== 'undefined' ? window.location.href : undefined,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        timestamp: Date.now(),
        ...context,
      },
      severity,
      fingerprint: this.createFingerprint(error),
    };

    this.sendError(errorReport);
  }

  public captureMessage(
    message: string,
    context: Partial<ErrorContext> = {},
    severity: ErrorReport['severity'] = 'low'
  ): void {
    const error = new Error(message);
    this.captureError(error, context, severity);
  }

  public setUser(userId: string): void {
    // Update user context for future errors
    this.config.customData = {
      ...this.config.customData,
      userId,
    };
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  public getErrorCount(): number {
    return this.errorCount;
  }
}

export const createErrorTracker = (config?: ErrorTrackingConfig) => {
  return new ErrorTracker(config);
};

// Default instance
export const errorTracker = createErrorTracker();

// Global error handlers for frontend
export const setupGlobalErrorHandlers = (tracker: ErrorTracker = errorTracker): void => {
  if (typeof window === 'undefined') {
    return;
  }

  // Unhandled JavaScript errors
  window.addEventListener('error', (event) => {
    tracker.captureError(event.error || new Error(event.message), {
      url: event.filename,
      line: event.lineno,
      column: event.colno,
    }, 'high');
  });

  // Unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error
      ? event.reason
      : new Error(String(event.reason));

    tracker.captureError(error, {
      type: 'unhandledrejection',
    }, 'high');
  });
};

// Web Vitals tracking for frontend applications

export interface WebVitalsMetric {
  name: 'CLS' | 'FID' | 'FCP' | 'LCP' | 'TTFB';
  value: number;
  delta: number;
  id: string;
  navigationType: 'navigate' | 'reload' | 'back-forward' | 'back-forward-cache';
}

export interface WebVitalsConfig {
  endpoint?: string;
  debug?: boolean;
  sampleRate?: number;
  customDimensions?: Record<string, string | number>;
}

class WebVitalsTracker {
  private config: WebVitalsConfig;
  private metrics: WebVitalsMetric[] = [];

  constructor(config: WebVitalsConfig = {}) {
    this.config = {
      endpoint: '/api/telemetry/web-vitals',
      debug: false,
      sampleRate: 1.0,
      ...config,
    };
  }

  private shouldSample(): boolean {
    return Math.random() < (this.config.sampleRate || 1.0);
  }

  private sendMetric(metric: WebVitalsMetric): void {
    if (!this.shouldSample()) {
      return;
    }

    this.metrics.push(metric);

    const payload = {
      ...metric,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      ...this.config.customDimensions,
    };

    if (this.config.debug) {
      console.log('Web Vitals Metric:', payload);
    }

    // Send to analytics endpoint
    if (this.config.endpoint) {
      fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      }).catch((error) => {
        console.error('Failed to send Web Vitals metric:', error);
      });
    }
  }

  public startTracking(): void {
    // Only run in browser environment
    if (typeof window === 'undefined') {
      return;
    }

    // Import web-vitals library dynamically
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS((metric) => this.sendMetric(metric));
      getFID((metric) => this.sendMetric(metric));
      getFCP((metric) => this.sendMetric(metric));
      getLCP((metric) => this.sendMetric(metric));
      getTTFB((metric) => this.sendMetric(metric));
    }).catch((error) => {
      console.error('Failed to load web-vitals library:', error);
    });
  }

  public getMetrics(): WebVitalsMetric[] {
    return [...this.metrics];
  }

  public clearMetrics(): void {
    this.metrics = [];
  }
}

export const createWebVitalsTracker = (config?: WebVitalsConfig) => {
  return new WebVitalsTracker(config);
};

// Default instance
export const webVitalsTracker = createWebVitalsTracker();

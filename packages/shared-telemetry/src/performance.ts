// Performance monitoring utilities

export interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  type: 'timing' | 'counter' | 'gauge';
  tags?: Record<string, string>;
}

export interface PerformanceConfig {
  endpoint?: string;
  debug?: boolean;
  sampleRate?: number;
  batchSize?: number;
  flushInterval?: number;
}

class PerformanceMonitor {
  private config: PerformanceConfig;
  private metrics: PerformanceMetric[] = [];
  private flushTimer?: NodeJS.Timeout;

  constructor(config: PerformanceConfig = {}) {
    this.config = {
      endpoint: '/api/telemetry/performance',
      debug: false,
      sampleRate: 1.0,
      batchSize: 10,
      flushInterval: 30000, // 30 seconds
      ...config,
    };

    this.startFlushTimer();
  }

  private shouldSample(): boolean {
    return Math.random() < (this.config.sampleRate || 1.0);
  }

  private startFlushTimer(): void {
    if (this.config.flushInterval && this.config.flushInterval > 0) {
      this.flushTimer = setInterval(() => {
        this.flush();
      }, this.config.flushInterval);
    }
  }

  private async sendMetrics(metrics: PerformanceMetric[]): Promise<void> {
    if (!this.config.endpoint || metrics.length === 0) {
      return;
    }

    const payload = {
      metrics,
      timestamp: Date.now(),
      sessionId: this.getSessionId(),
    };

    if (this.config.debug) {
      console.log('Performance Metrics:', payload);
    }

    try {
      await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error('Failed to send performance metrics:', error);
    }
  }

  private getSessionId(): string {
    if (typeof window !== 'undefined') {
      return (window as any).__SESSION_ID__ || 'unknown';
    }
    return 'server';
  }

  public recordTiming(name: string, value: number, tags?: Record<string, string>): void {
    if (!this.shouldSample()) {
      return;
    }

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      type: 'timing',
      tags,
    };

    this.metrics.push(metric);
    this.checkFlush();
  }

  public recordCounter(name: string, value: number = 1, tags?: Record<string, string>): void {
    if (!this.shouldSample()) {
      return;
    }

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      type: 'counter',
      tags,
    };

    this.metrics.push(metric);
    this.checkFlush();
  }

  public recordGauge(name: string, value: number, tags?: Record<string, string>): void {
    if (!this.shouldSample()) {
      return;
    }

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      type: 'gauge',
      tags,
    };

    this.metrics.push(metric);
    this.checkFlush();
  }

  private checkFlush(): void {
    if (this.metrics.length >= (this.config.batchSize || 10)) {
      this.flush();
    }
  }

  public async flush(): Promise<void> {
    if (this.metrics.length === 0) {
      return;
    }

    const metricsToSend = [...this.metrics];
    this.metrics = [];

    await this.sendMetrics(metricsToSend);
  }

  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  public clearMetrics(): void {
    this.metrics = [];
  }

  public destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flush();
  }
}

// Timing decorator for functions
export function measureTiming(name: string, tags?: Record<string, string>) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const start = performance.now();
      try {
        const result = await originalMethod.apply(this, args);
        const duration = performance.now() - start;
        performanceMonitor.recordTiming(name, duration, tags);
        return result;
      } catch (error) {
        const duration = performance.now() - start;
        performanceMonitor.recordTiming(name, duration, { ...tags, error: 'true' });
        throw error;
      }
    };

    return descriptor;
  };
}

// Performance timing utility
export class PerformanceTimer {
  private startTime: number;
  private name: string;
  private tags?: Record<string, string>;

  constructor(name: string, tags?: Record<string, string>) {
    this.name = name;
    this.tags = tags;
    this.startTime = performance.now();
  }

  public end(): number {
    const duration = performance.now() - this.startTime;
    performanceMonitor.recordTiming(this.name, duration, this.tags);
    return duration;
  }
}

export const createPerformanceMonitor = (config?: PerformanceConfig) => {
  return new PerformanceMonitor(config);
};

// Default instance
export const performanceMonitor = createPerformanceMonitor();

// Auto-flush on page unload (frontend only)
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    performanceMonitor.flush();
  });
}

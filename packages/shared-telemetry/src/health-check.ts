// Health check utilities for monitoring application health

export interface HealthCheckResult {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  message?: string;
  timestamp: number;
  duration?: number;
  metadata?: Record<string, any>;
}

export interface HealthCheckConfig {
  timeout?: number;
  retries?: number;
  interval?: number;
}

export interface HealthCheck {
  name: string;
  check: () => Promise<HealthCheckResult>;
  config?: HealthCheckConfig;
}

class HealthChecker {
  private checks: HealthCheck[] = [];
  private results: Map<string, HealthCheckResult> = new Map();

  public addCheck(check: HealthCheck): void {
    this.checks.push(check);
  }

  public async runCheck(name: string): Promise<HealthCheckResult> {
    const check = this.checks.find(c => c.name === name);
    if (!check) {
      throw new Error(`Health check '${name}' not found`);
    }

    const config = {
      timeout: 5000,
      retries: 1,
      ...check.config,
    };

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= config.retries!; attempt++) {
      try {
        const startTime = Date.now();

        const result = await Promise.race([
          check.check(),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Health check timeout')), config.timeout)
          )
        ]);

        const duration = Date.now() - startTime;

        const finalResult: HealthCheckResult = {
          ...result,
          duration,
          timestamp: Date.now(),
        };

        this.results.set(name, finalResult);
        return finalResult;
      } catch (error) {
        lastError = error as Error;
        if (attempt < config.retries!) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }

    const errorResult: HealthCheckResult = {
      name,
      status: 'unhealthy',
      message: lastError?.message || 'Health check failed',
      timestamp: Date.now(),
    };

    this.results.set(name, errorResult);
    return errorResult;
  }

  public async runAllChecks(): Promise<HealthCheckResult[]> {
    const results = await Promise.allSettled(
      this.checks.map(check => this.runCheck(check.name))
    );

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          name: this.checks[index].name,
          status: 'unhealthy' as const,
          message: result.reason?.message || 'Health check failed',
          timestamp: Date.now(),
        };
      }
    });
  }

  public getResult(name: string): HealthCheckResult | undefined {
    return this.results.get(name);
  }

  public getAllResults(): HealthCheckResult[] {
    return Array.from(this.results.values());
  }

  public getOverallStatus(): 'healthy' | 'unhealthy' | 'degraded' {
    const results = this.getAllResults();

    if (results.length === 0) {
      return 'healthy';
    }

    const unhealthyCount = results.filter(r => r.status === 'unhealthy').length;
    const degradedCount = results.filter(r => r.status === 'degraded').length;

    if (unhealthyCount > 0) {
      return 'unhealthy';
    } else if (degradedCount > 0) {
      return 'degraded';
    } else {
      return 'healthy';
    }
  }

  public clearResults(): void {
    this.results.clear();
  }
}

// Common health check implementations
export const createDatabaseHealthCheck = (dbQuery: () => Promise<any>): HealthCheck => ({
  name: 'database',
  check: async () => {
    try {
      await dbQuery();
      return {
        name: 'database',
        status: 'healthy',
        message: 'Database connection successful',
        timestamp: Date.now(),
      };
    } catch (error) {
      return {
        name: 'database',
        status: 'unhealthy',
        message: `Database connection failed: ${(error as Error).message}`,
        timestamp: Date.now(),
      };
    }
  },
});

export const createExternalServiceHealthCheck = (
  name: string,
  url: string,
  timeout: number = 5000
): HealthCheck => ({
  name,
  check: async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        return {
          name,
          status: 'healthy',
          message: 'External service is responding',
          timestamp: Date.now(),
          metadata: {
            statusCode: response.status,
            responseTime: Date.now(),
          },
        };
      } else {
        return {
          name,
          status: 'degraded',
          message: `External service returned ${response.status}`,
          timestamp: Date.now(),
          metadata: {
            statusCode: response.status,
          },
        };
      }
    } catch (error) {
      return {
        name,
        status: 'unhealthy',
        message: `External service check failed: ${(error as Error).message}`,
        timestamp: Date.now(),
      };
    }
  },
});

export const createMemoryHealthCheck = (): HealthCheck => ({
  name: 'memory',
  check: async () => {
    if (typeof process === 'undefined') {
      return {
        name: 'memory',
        status: 'healthy',
        message: 'Memory check not available in browser',
        timestamp: Date.now(),
      };
    }

    const memUsage = process.memoryUsage();
    const heapUsedMB = Math.round(memUsage.heapUsed / 1024 / 1024);
    const heapTotalMB = Math.round(memUsage.heapTotal / 1024 / 1024);
    const usagePercent = (heapUsedMB / heapTotalMB) * 100;

    let status: 'healthy' | 'unhealthy' | 'degraded' = 'healthy';
    let message = `Memory usage: ${heapUsedMB}MB / ${heapTotalMB}MB (${usagePercent.toFixed(1)}%)`;

    if (usagePercent > 90) {
      status = 'unhealthy';
      message += ' - Critical memory usage';
    } else if (usagePercent > 80) {
      status = 'degraded';
      message += ' - High memory usage';
    }

    return {
      name: 'memory',
      status,
      message,
      timestamp: Date.now(),
      metadata: {
        heapUsed: heapUsedMB,
        heapTotal: heapTotalMB,
        usagePercent: Math.round(usagePercent * 100) / 100,
      },
    };
  },
});

export const createHealthChecker = () => {
  return new HealthChecker();
};

// Default instance
export const healthChecker = createHealthChecker();

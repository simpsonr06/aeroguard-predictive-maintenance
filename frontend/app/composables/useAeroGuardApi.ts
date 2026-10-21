import type {
  HealthResponse,
  FleetSummaryResponse,
  EngineListResponse,
  EngineDetailResponse,
  PredictionRequest,
  PredictionResponse,
  SensorsSummaryResponse,
  ModelMetricsResponse,
  MaintenanceQueueResponse
} from '~/types/aeroguard'

export function useAeroGuardApi() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  const fetchApi = async <T>(path: string, options: Parameters<typeof $fetch>[1] = {}): Promise<T> => {
    return await $fetch<T>(`${apiBase}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.headers || {})
      }
    })
  }

  return {
    apiBase,
    getHealth: () => fetchApi<HealthResponse>('/api/health'),
    getFleetSummary: (warningThreshold = 45, criticalThreshold = 20) =>
      fetchApi<FleetSummaryResponse>(`/api/fleet/summary?warning_threshold=${warningThreshold}&critical_threshold=${criticalThreshold}`),
    getEngines: (dataset: 'train' | 'test' = 'test', status = 'all') =>
      fetchApi<EngineListResponse>(`/api/engines?dataset=${dataset}&status=${status}`),
    getEngineDetail: (engineId: number, dataset: 'train' | 'test' = 'test', cutoffCycle?: number) => {
      const q = cutoffCycle ? `?dataset=${dataset}&cutoff_cycle=${cutoffCycle}` : `?dataset=${dataset}`
      return fetchApi<EngineDetailResponse>(`/api/engines/${engineId}${q}`)
    },
    postPredict: (payload: PredictionRequest) =>
      fetchApi<PredictionResponse>('/api/predict', {
        method: 'POST',
        body: payload
      }),
    getSensorsSummary: () => fetchApi<SensorsSummaryResponse>('/api/sensors/summary'),
    getModelMetrics: () => fetchApi<ModelMetricsResponse>('/api/models/metrics'),
    getMaintenanceQueue: (warningThreshold = 45, criticalThreshold = 20, status = 'all') =>
      fetchApi<MaintenanceQueueResponse>(
        `/api/maintenance/queue?warning_threshold=${warningThreshold}&critical_threshold=${criticalThreshold}&status=${status}`
      ),
    getExportUrl: (warningThreshold = 45, criticalThreshold = 20, status = 'all') =>
      `${apiBase}/api/maintenance/export?warning_threshold=${warningThreshold}&critical_threshold=${criticalThreshold}&status=${status}`,
    getMetrics: () => fetchApi<any>('/api/metrics'),
    getDrift: (ksAlpha = 0.01, psiWarning = 0.10, psiDrift = 0.25) =>
      fetchApi<any>(`/api/drift?ks_alpha=${ksAlpha}&psi_warning=${psiWarning}&psi_drift=${psiDrift}`),
    getLineage: () => fetchApi<any>('/api/models/lineage'),
    getSecurityStatus: () => fetchApi<any>('/api/security/status'),
    getAttackSimulation: () => fetchApi<any>('/api/security/attack-simulation')
  }
}


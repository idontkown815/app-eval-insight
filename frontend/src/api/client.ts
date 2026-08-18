import axios from 'axios'
import type {
  ValidateLinkRequest, ValidateLinkResponse,
  CreateTaskRequest, CreateTaskResponse,
  Progress, TaskResults,
} from '../types'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export async function validateLink(url: string): Promise<ValidateLinkResponse> {
  const req: ValidateLinkRequest = { url }
  const res = await api.post<ValidateLinkResponse>('/validate-link', req)
  return res.data
}

export async function createTask(data: CreateTaskRequest): Promise<CreateTaskResponse> {
  const res = await api.post<CreateTaskResponse>('/tasks', data)
  return res.data
}

export async function getProgress(taskId: string): Promise<Progress> {
  const res = await api.get(`/tasks/${taskId}/progress`)
  return res.data
}

export async function getResults(taskId: string): Promise<TaskResults> {
  const res = await api.get(`/tasks/${taskId}/results`)
  return res.data
}

export async function importFile(file: File, user_goal: string): Promise<any> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('user_goal', user_goal)
  const res = await api.post('/import', fd)
  return res.data
}

export async function exportResults(taskId: string, format: 'csv' | 'md' | 'json'): Promise<Blob> {
  const res = await api.get(`/tasks/${taskId}/export`, {
    params: { format },
    responseType: 'blob',
  })
  return res.data
}

export async function checkHealth(): Promise<any> {
  const res = await api.get('/health')
  return res.data
}

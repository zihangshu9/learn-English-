export interface DashboardTask {
  id: number
  title: string
  task_type: string
  target_count: number
  completed_count: number
  estimated_minutes: number
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
}

export interface Dashboard {
  plan_name: string
  target_completion_date: string
  days_remaining: number
  progress_percent: number
  streak_days: number
  tasks: DashboardTask[]
}

const demoDashboard: Dashboard = {
  plan_name: '四级基础提升计划',
  target_completion_date: '2027-06-01',
  days_remaining: 304,
  progress_percent: 0,
  streak_days: 0,
  tasks: [
    { id: 1, title: '复习旧单词', task_type: 'word_review', target_count: 20, completed_count: 0, estimated_minutes: 8, status: 'pending' },
    { id: 2, title: '学习新单词', task_type: 'new_words', target_count: 15, completed_count: 0, estimated_minutes: 12, status: 'pending' },
    { id: 3, title: '基础阅读', task_type: 'reading', target_count: 1, completed_count: 0, estimated_minutes: 15, status: 'pending' },
    { id: 4, title: '复习错题', task_type: 'mistake_review', target_count: 5, completed_count: 0, estimated_minutes: 8, status: 'pending' },
  ],
}

export async function getDashboard(): Promise<{ data: Dashboard; offline: boolean }> {
  try {
    const response = await fetch('/api/dashboard')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return { data: await response.json(), offline: false }
  } catch {
    return { data: demoDashboard, offline: true }
  }
}

export interface AiStatus {
  configured: boolean
  default_model: string
  base_url: string
}

export async function getAiStatus(): Promise<AiStatus> {
  const response = await fetch('/api/ai/status')
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export async function saveAiSettings(apiKey: string, model: string): Promise<AiStatus> {
  const response = await fetch('/api/ai/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey || null, model }),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export interface WordCard {
  id: number
  word: string
  phonetic: string | null
  meaning: string
  part_of_speech: string | null
  example: string | null
  example_translation: string | null
  status: string
  review_count: number
}

export interface WordSession {
  words: WordCard[]
  review_count: number
  new_count: number
}

export async function getWordSession(limit = 15): Promise<WordSession> {
  const response = await fetch(`/api/words/session?limit=${limit}`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export async function reviewWord(wordId: number, result: 'unknown' | 'fuzzy' | 'known'): Promise<void> {
  const response = await fetch(`/api/words/${wordId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result }),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
}

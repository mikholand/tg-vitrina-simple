import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSyncStatus, startSync as startSyncRequest, stopSync as stopSyncRequest } from './api'
import type { SyncState } from './types'

export const useSyncStore = defineStore('sync', () => {
  const state = ref<SyncState | null>(null)

  async function fetchStatus(): Promise<void> {
    state.value = await getSyncStatus()
  }

  async function startSync(resume = false): Promise<void> {
    state.value = await startSyncRequest(resume)
  }

  async function stopSync(): Promise<void> {
    state.value = await stopSyncRequest()
  }

  return { state, fetchStatus, startSync, stopSync }
})

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
const error = ref('')
const busy = ref(false)

const nameOf = computed(() => {
  const m = {}
  for (const s of stations.value) m[s.code] = s.name
  return (code) => (code in m ? `${m[code]}(${code})` : code)
})

const edgeText = (e) => `${nameOf.value(e.a)} — ${nameOf.value(e.b)}`

async function run() {
  error.value = ''
  busy.value = true
  try {
    // persist=false：只读试算，不写入试算记录
    out.value = await postJSON('/api/quote', {
      start: start.value,
      end: end.value,
      persist: false,
    })
  } catch (err) {
    out.value = null
    error.value = err.message
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  stations.value = (await getJSON('/api/stations')).items
})
</script>
<template>
  <div class="page">
    <h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start">
        <option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option>
      </select>
      →
      <select v-model="end">
        <option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option>
      </select>
      <button :disabled="busy" @click="run">试算</button>
      <span class="muted">（只读试算，不落库）</span>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <p>
          站数 {{ out.hops }} · 票价 <span class="hero-num">¥{{ out.fare }}</span>
        </p>
        <p>
          途经：
          <span v-for="(code, i) in out.path" :key="i">
            <span class="waypoint">{{ nameOf(code) }}</span>
            <span v-if="i < out.path.length - 1" class="muted"> → </span>
          </span>
        </p>
        <div v-if="out.detour_edges && out.detour_edges.length" class="detour-box">
          <p>当前生效中断迫使绕开区间：</p>
          <ul>
            <li v-for="(e, i) in out.detour_edges" :key="i">{{ edgeText(e) }}</li>
          </ul>
        </div>
      </template>
      <template v-else>
        <p class="error-text">不可达：起终点之间的路径被生效中断切断。</p>
        <p v-if="out.blocking_edges && out.blocking_edges.length">
          被挡区间：
          <span v-for="(e, i) in out.blocking_edges" :key="i" class="blocked-edge">
            {{ edgeText(e) }}<span v-if="i < out.blocking_edges.length - 1">、</span>
          </span>
        </p>
        <p v-else class="muted">（当前没有与该起终点相关的生效中断边）</p>
      </template>
    </div>
  </div>
</template>

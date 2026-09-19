<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
const error = ref('')

const nameOf = (code) => {
  const s = stations.value.find(x => x.code === code)
  return s ? `${s.name}(${code})` : code
}
const edgeText = (e) => `${e.a} — ${e.b}${e.reason ? `（${e.reason}）` : ''}`

onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
// 只读试算：不落库，因此不产生试算记录
const run = async () => {
  error.value = ''
  try {
    out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: false })
  } catch (e) { error.value = e.message }
}
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <button @click="run">试算</button>
      <span class="muted" style="margin-left:.75rem;">只读试算，不落库</span>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>
    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <p>站数 {{ out.hops }} · 票价 <span class="hero-num">¥{{ out.fare }}</span></p>
        <p>途经站：<span v-for="(c, i) in out.path" :key="i">
          {{ nameOf(c) }}<span v-if="i < out.path.length - 1"> → </span>
        </span></p>
        <p v-if="out.detoured" class="warn-text">
          ⚠ 区间中断绕行：已绕开
          <span v-for="(e, i) in out.avoided_edges" :key="i">「{{ edgeText(e) }}」</span>
        </p>
      </template>
      <template v-else>
        <p class="warn-text">不可达：生效区间中断挡住去路，未编造途经站。</p>
        <p>被挡的邻接边：
          <span v-if="out.blocked_edges.length">
            <span v-for="(e, i) in out.blocked_edges" :key="i">「{{ edgeText(e) }}」<span v-if="i < out.blocked_edges.length - 1">、</span></span>
          </span>
          <span v-else class="muted">该起终点本就无通路</span>
        </p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const edges = ref([])
const disruptions = ref([])
const picked = ref('')
const reason = ref('')
const busy = ref(false)
const error = ref('')

const keyOf = (a, b) => [a, b].sort().join('—')
const activeByEdge = computed(() => {
  const m = {}
  for (const d of disruptions.value) if (d.active) m[keyOf(d.a, d.b)] = d
  return m
})

const load = async () => {
  const [e, d] = await Promise.all([getJSON('/api/edges'), getJSON('/api/disruptions')])
  edges.value = e.items
  disruptions.value = d.items
  if (!picked.value && edges.value.length) picked.value = keyOf(edges.value[0].a, edges.value[0].b)
}

const register = async () => {
  error.value = ''
  if (!picked.value) return
  const [a, b] = picked.value.split('—')
  busy.value = true
  try {
    await postJSON('/api/disruptions', { a, b, reason: reason.value })
    reason.value = ''
    await load()
  } catch (e) { error.value = `登记失败：${e.message}` } finally { busy.value = false }
}

const release = async (id) => {
  error.value = ''
  busy.value = true
  try { await postJSON(`/api/disruptions/${id}/release`); await load() }
  catch (e) { error.value = `解除失败：${e.message}` } finally { busy.value = false }
}

onMounted(load)
</script>
<template>
  <div class="page"><h1>邻接区间</h1>
    <div class="panel">
      <h2>登记区间中断</h2>
      <p class="muted">对一条邻接边登记生效中断后，该边不得进入最短路。</p>
      <select v-model="picked">
        <option v-for="e in edges" :key="keyOf(e.a, e.b)" :value="keyOf(e.a, e.b)">{{ e.a }} — {{ e.b }}</option>
      </select>
      <input v-model="reason" placeholder="中断原因（如：信号检修）" style="width: 14rem; margin: 0 .5rem;" />
      <button :disabled="busy || !!activeByEdge[picked]" @click="register">登记生效中断</button>
      <p v-if="activeByEdge[picked]" class="muted">该边已有生效中断，请先解除或选择其他区间。</p>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>

    <div class="panel">
      <h2>邻接边状态</h2>
      <table>
        <thead><tr><th>两端编码</th><th>状态</th><th>原因</th><th></th></tr></thead>
        <tbody>
          <tr v-for="e in edges" :key="keyOf(e.a, e.b)">
            <td>{{ e.a }} — {{ e.b }}</td>
            <td>
              <span v-if="activeByEdge[keyOf(e.a, e.b)]" class="badge-off">中断生效</span>
              <span v-else class="badge-ok">正常</span>
            </td>
            <td>{{ activeByEdge[keyOf(e.a, e.b)]?.reason || '—' }}</td>
            <td>
              <button v-if="activeByEdge[keyOf(e.a, e.b)]" :disabled="busy"
                      @click="release(activeByEdge[keyOf(e.a, e.b)].id)">解除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="panel">
      <h2>中断记录</h2>
      <table>
        <thead><tr><th>#</th><th>区间</th><th>原因</th><th>状态</th><th>登记时间</th><th>解除时间</th><th></th></tr></thead>
        <tbody>
          <tr v-for="d in disruptions" :key="d.id">
            <td>{{ d.id }}</td>
            <td>{{ d.a }} — {{ d.b }}</td>
            <td>{{ d.reason }}</td>
            <td><span :class="d.active ? 'badge-off' : 'badge-ok'">{{ d.active ? '生效中' : '已解除' }}</span></td>
            <td class="muted">{{ d.created_at }}</td>
            <td class="muted">{{ d.released_at || '—' }}</td>
            <td><button v-if="d.active" :disabled="busy" @click="release(d.id)">解除</button></td>
          </tr>
          <tr v-if="!disruptions.length"><td colspan="7" class="muted">暂无中断记录</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

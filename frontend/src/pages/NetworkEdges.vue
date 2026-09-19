<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const items = ref([])
const reasons = ref({})
const error = ref('')
const busy = ref(false)

const keyOf = (e) => `${e.a}|${e.b}`

async function load() {
  items.value = (await getJSON('/api/edges')).items
  for (const e of items.value) {
    if (!(keyOf(e) in reasons.value)) reasons.value[keyOf(e)] = ''
  }
}

async function register(e) {
  error.value = ''
  const reason = (reasons.value[keyOf(e)] || '').trim()
  if (!reason) {
    error.value = `登记 ${e.a} — ${e.b} 需要填写中断原因`
    return
  }
  busy.value = true
  try {
    await postJSON('/api/disruptions', { a: e.a, b: e.b, reason })
    reasons.value[keyOf(e)] = ''
    await load()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

async function lift(e) {
  error.value = ''
  busy.value = true
  try {
    await postJSON('/api/disruptions/lift', { a: e.a, b: e.b })
    await load()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
<template>
  <div class="page">
    <h1>邻接区间</h1>
    <p class="muted">对一条邻接边登记生效中断后，它不会进入最短路；解除后恢复原路径与票价。</p>
    <p v-if="error" class="error">{{ error }}</p>
    <table>
      <thead>
        <tr><th>区间</th><th>状态</th><th>中断原因</th><th>登记</th><th>解除</th></tr>
      </thead>
      <tbody>
        <tr v-for="e in items" :key="keyOf(e)">
          <td>{{ e.a }} — {{ e.b }}</td>
          <td>
            <span v-if="e.disrupted" class="badge badge-off">生效中断</span>
            <span v-else class="badge badge-on">正常</span>
          </td>
          <td>
            <span v-if="e.disrupted">{{ e.reason }}</span>
            <input
              v-else
              v-model="reasons[keyOf(e)]"
              placeholder="如：区间检修"
              :disabled="busy"
            />
          </td>
          <td>
            <button v-if="!e.disrupted" :disabled="busy" @click="register(e)">登记中断</button>
          </td>
          <td>
            <button
              v-if="e.disrupted"
              class="btn-secondary"
              :disabled="busy"
              @click="lift(e)"
            >解除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

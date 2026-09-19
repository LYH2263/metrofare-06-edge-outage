<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const rows = ref([])

onMounted(async () => {
  const [h, st] = await Promise.all([getJSON('/api/history'), getJSON('/api/stations')])
  rows.value = h.items.map((row) => {
    let input = {}
    let result = null
    try {
      input = JSON.parse(row.input_json)
      result = JSON.parse(row.result_json)
    } catch {
      /* keep nulls */
    }
    return { ...row, input, result, stationNames: st.items }
  })
})

const stationName = (row, code) => {
  const s = row.stationNames.find((x) => x.code === code)
  return s ? s.name : code
}
</script>
<template>
  <div class="page">
    <h1>试算记录</h1>
    <p class="muted">每条记录保存写入当时的途经站与票价；之后登记或解除中断不会改写历史记录。</p>
    <table>
      <thead>
        <tr><th>#</th><th>时间</th><th>起终</th><th>当时站数</th><th>当时票价</th><th>当时途经站</th></tr>
      </thead>
      <tbody>
        <tr v-for="h in rows" :key="h.id">
          <td>#{{ h.id }}</td>
          <td>{{ h.created_at }}</td>
          <td>{{ h.input.start }} → {{ h.input.end }}</td>
          <td v-if="h.result">{{ h.result.hops }}</td>
          <td v-if="h.result">¥{{ h.result.fare }}</td>
          <td v-if="h.result">
            <span v-for="(code, i) in h.result.path" :key="i">
              {{ stationName(h, code) }}<span v-if="i < h.result.path.length - 1"> → </span>
            </span>
          </td>
          <td v-if="!h.result" colspan="3" class="muted">无结果快照</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

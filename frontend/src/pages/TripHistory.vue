<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/history')).items })
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <p class="muted">记录为询价落库当时的快照；后来中断登记或解除均不改写历史途经站与票价。</p>
    <table>
      <thead><tr><th>#</th><th>时间</th><th>起终点</th><th>当时站数</th><th>当时票价</th><th>当时途经站</th><th>备注</th></tr></thead>
      <tbody>
        <tr v-for="h in items" :key="h.id">
          <td>#{{ h.id }}</td>
          <td>{{ h.created_at }}</td>
          <td>{{ h.input.start }} → {{ h.input.end }}</td>
          <td>{{ h.result.hops }}</td>
          <td>¥{{ h.result.fare }}</td>
          <td>{{ (h.result.path || []).join(' → ') }}</td>
          <td>
            <span v-if="h.result.detoured" class="warn-text">
              绕行绕开 {{ (h.result.avoided_edges || []).map(e => `${e.a}—${e.b}`).join('、') }}
            </span>
            <span v-else-if="!h.result.reachable" class="muted">不可达</span>
            <span v-else class="muted">正常</span>
          </td>
        </tr>
        <tr v-if="!items.length"><td colspan="7" class="muted">暂无落库记录（只读试算不产生记录）</td></tr>
      </tbody>
    </table>
  </div>
</template>

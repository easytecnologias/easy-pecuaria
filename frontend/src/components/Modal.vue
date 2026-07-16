<script setup lang="ts">
import { X } from "lucide-vue-next";
defineProps<{ titulo: string; sub?: string; largura?: number }>();
const emit = defineEmits<{ fechar: [] }>();
</script>

<template>
  <div class="overlay" @click.self="emit('fechar')">
    <div class="modal" :style="{ maxWidth: (largura ?? 480) + 'px' }">
      <header class="mhead">
        <div>
          <div class="mtitle">{{ titulo }}</div>
          <div class="msub" v-if="sub">{{ sub }}</div>
        </div>
        <button class="xbtn" @click="emit('fechar')"><X :size="18" /></button>
      </header>
      <div class="mbody"><slot /></div>
      <footer class="mfoot" v-if="$slots.acoes"><slot name="acoes" /></footer>
    </div>
  </div>
</template>

<style scoped>
.overlay { position: fixed; inset: 0; background: rgba(16,38,45,.45); display: grid; place-items: center;
  z-index: 50; padding: 20px; }
.modal { width: 100%; max-width: 480px; background: var(--surface); border-radius: 12px;
  box-shadow: 0 16px 48px rgba(16,38,45,.25); overflow: hidden; }
.mhead { display: flex; justify-content: space-between; align-items: flex-start;
  padding: 16px 18px; border-bottom: 1px solid var(--border); }
.mtitle { font-size: 16px; font-weight: 700; }
.msub { font-size: 12.5px; color: var(--muted); margin-top: 2px; }
.xbtn { border: none; background: transparent; color: var(--muted); cursor: pointer; padding: 4px; border-radius: 6px; }
.xbtn:hover { background: #f0f3f5; }
.mbody { padding: 18px; max-height: 72vh; overflow-y: auto; }
.mfoot { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 18px; border-top: 1px solid var(--border); }
</style>

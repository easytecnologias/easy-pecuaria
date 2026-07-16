<script setup lang="ts">
defineProps<{ title?: string; sub?: string }>();
</script>

<template>
  <section class="panel">
    <header class="panel__head" v-if="title || $slots.actions">
      <div>
        <div class="panel__title" v-if="title">{{ title }}</div>
        <div class="panel__sub" v-if="sub">{{ sub }}</div>
      </div>
      <slot name="actions" />
    </header>
    <div class="panel__body">
      <slot />
    </div>
  </section>
</template>

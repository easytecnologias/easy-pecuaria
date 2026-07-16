<script setup lang="ts">
import type { Severidade } from "../api";
defineProps<{ situacao: Severidade }>();
</script>

<template>
  <span :class="['badge', situacao]">
    <span class="dot" />
    {{ situacao }}
  </span>
</template>

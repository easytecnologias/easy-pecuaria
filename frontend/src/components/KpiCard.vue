<script setup lang="ts">
import type { Component } from "vue";

defineProps<{
  label: string;
  value: string | number;
  sub?: string;
  icon?: Component;
  emoji?: string;
  tone?: "primary" | "danger" | "amber" | "blue" | "purple";
}>();

const bg: Record<string, string> = {
  primary: "#e7f4ee",
  danger: "#fcebeb",
  amber: "#fdf1df",
  blue: "#e6f0fb",
  purple: "#f0ecfb",
};
const fg: Record<string, string> = {
  primary: "#078b64",
  danger: "#dc2626",
  amber: "#d97706",
  blue: "#1971c2",
  purple: "#6a45c2",
};
</script>

<template>
  <div class="kpi">
    <div class="kpi__icon" :style="{ background: bg[tone ?? 'primary'], color: fg[tone ?? 'primary'] }">
      <span v-if="emoji" style="font-size:20px;line-height:1">{{ emoji }}</span>
      <component :is="icon" v-else-if="icon" :size="20" />
    </div>
    <div>
      <div class="kpi__label">{{ label }}</div>
      <div class="kpi__value">{{ value }}</div>
      <div class="kpi__sub" v-if="sub">{{ sub }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { sincronizarFila, getToken } from "./api";

// esvazia a fila offline ao abrir e sempre que a internet voltar
function sync() { if (getToken()) sincronizarFila().catch(() => { /* segue offline */ }); }
onMounted(() => { sync(); window.addEventListener("online", sync); });
onUnmounted(() => window.removeEventListener("online", sync));
</script>

<template>
  <RouterView />
</template>

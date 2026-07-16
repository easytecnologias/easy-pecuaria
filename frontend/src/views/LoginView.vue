<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { LogIn } from "lucide-vue-next";
import { login } from "../api";

const router = useRouter();
const email = ref("admin@pecuaria.local");
const senha = ref("admin123");
const erro = ref("");
const carregando = ref(false);

async function entrar() {
  erro.value = "";
  carregando.value = true;
  try {
    await login(email.value, senha.value);
    router.push("/");
  } catch (e) {
    erro.value = String(e instanceof Error ? e.message : e);
  } finally {
    carregando.value = false;
  }
}
</script>

<template>
  <div class="login-shell">
    <form class="login-card" @submit.prevent="entrar">
      <div class="login-brand">
        <div class="sidebar__logo" style="width:40px;height:40px">JLN</div>
        <div>
          <div style="font-weight:700;font-size:17px">Pecuária · Grupo JLN</div>
          <div class="muted" style="font-size:13px">Painel de gestão</div>
        </div>
      </div>

      <div class="field">
        <label>Email</label>
        <input class="input" v-model="email" type="email" autocomplete="username" />
      </div>
      <div class="field">
        <label>Senha</label>
        <input class="input" v-model="senha" type="password" autocomplete="current-password" />
      </div>

      <p v-if="erro" class="error">{{ erro }}</p>

      <button class="btn btn--primary" style="justify-content:center;height:46px" :disabled="carregando">
        <LogIn :size="18" /> {{ carregando ? "Entrando…" : "Entrar" }}
      </button>
    </form>
  </div>
</template>

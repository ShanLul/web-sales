<template>
  <div class="mx-auto flex min-h-screen w-full max-w-[430px] flex-col bg-[#F5F6F8]">
    <router-view v-slot="{ Component }">
      <transition
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="opacity-0 translate-x-3"
        leave-active-class="transition duration-150 ease-in"
        leave-to-class="opacity-0"
        mode="out-in"
      >
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup lang="ts">
</script>

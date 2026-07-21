<script setup>
import { computed } from 'vue'

const props = defineProps({
  card: String,          // 'As', 'Td'...
  size: { type: String, default: 'lg' } // 'lg' héroe, 'sm' board
})

const SUITS = { s: '♠', h: '♥', d: '♦', c: '♣' }
const rank = computed(() => props.card[0] === 'T' ? '10' : props.card[0])
const suit = computed(() => SUITS[props.card[1]])
const red = computed(() => 'hd'.includes(props.card[1]))
</script>

<template>
  <div
    class="bg-naipe rounded-lg shadow-card flex flex-col items-center justify-center font-num leading-none"
    :class="[
      size === 'lg' ? 'w-16 h-24 text-2xl' : 'w-10 h-14 text-base',
      red ? 'text-pierde' : 'text-felt-950'
    ]"
  >
    <span class="font-bold">{{ rank }}</span>
    <span :class="size === 'lg' ? 'text-3xl' : 'text-lg'">{{ suit }}</span>
  </div>
</template>

import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.pokergym.app',
  appName: 'Poker Gym',
  webDir: 'dist',
  android: { allowMixedContent: false }
};

export default config;

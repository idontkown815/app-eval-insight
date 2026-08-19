// Preload：在隔离上下文中向前端注入安全 API
const { contextBridge } = require('electron');

// 前端可通过 window.desktop.isDesktop 判断是否运行在桌面壳内
contextBridge.exposeInMainWorld('desktop', {
  isDesktop: true,
  platform: process.platform,
});

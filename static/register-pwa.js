/**
 * PWA 注册脚本
 * 在浏览器中注册 Service Worker 和 manifest
 */

// 注册 Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('[PWA] Service Worker 注册成功:', registration.scope);
      })
      .catch((error) => {
        console.log('[PWA] Service Worker 注册失败:', error);
      });
  });
}

// 监听更新
let refreshing = false;
navigator.serviceWorker.addEventListener('controllerchange', () => {
  if (refreshing) return;
  refreshing = true;
  window.location.reload();
});

// 监听安装提示
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // 可以在这里显示"添加到主屏幕"按钮
  console.log('[PWA] 可以添加到主屏幕');
});

// 监听安装完成
window.addEventListener('appinstalled', () => {
  console.log('[PWA] 已安装到主屏幕');
  deferredPrompt = null;
});

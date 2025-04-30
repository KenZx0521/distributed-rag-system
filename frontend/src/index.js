import React from 'react';
import { createRoot } from 'react-dom/client';  // 從 react-dom/client 導入 createRoot
import App from './App';
import './index.css';

// 取得根元素
const container = document.getElementById('root');

// 創建 root 實例
const root = createRoot(container);

// 使用 root.render 替代舊的 ReactDOM.render
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './pages/Home';
import Tasks from './pages/Tasks';

function App() {
  return (
    <Router>
      <div>
        {/* 導航連結 */}
        <nav>
          <ul>
            <li>
              <Link to="/">主頁</Link> {/* 使用絕對路徑 */}
            </li>
            <li>
              <Link to="/tasks">任務管理</Link> {/* 使用絕對路徑 */}
            </li>
          </ul>
        </nav>

        {/* 路由配置 */}
        <Routes>
          <Route path="/" element={<Home />} /> {/* 正確使用 element */}
          <Route path="/tasks" element={<Tasks />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
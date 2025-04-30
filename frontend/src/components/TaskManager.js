import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const cancelTask = async (taskId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/tasks/${taskId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('取消任務失敗');
      // 不需手動刷新，WebSocket 會自動更新
    } catch (err) {
      setError('取消任務失敗');
    }
  };

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/api/ws/tasks");

    ws.onopen = () => {
      console.log('WebSocket 連線成功');
      setLoading(false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setTasks(data.tasks || []);
        setError(null);
      } catch (err) {
        setError('解析任務數據失敗');
      }
    };

    ws.onerror = () => {
      setError('WebSocket 連線錯誤');
      setLoading(false);
    };

    ws.onclose = () => {
      console.log('WebSocket 連線關閉');
      setError('WebSocket 連線已斷開');
      setLoading(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div>
      <Link to="/">返回主頁</Link>
      <h2>任務列表</h2>
      {loading && <p>載入中...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table border="1">
        <thead>
          <tr>
            <th>任務 ID</th>
            <th>狀態</th>
            <th>執行節點</th>
            <th>結果</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.task_id}>
              <td>{task.task_id}</td>
              <td>{task.status}</td>
              <td>{task.node}</td>
              <td>{task.result ? JSON.stringify(task.result, null, 2) : task.error || '-'}</td>
              <td>
                {task.status === 'PENDING' && (
                  <button onClick={() => cancelTask(task.task_id)}>取消</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TaskManager;
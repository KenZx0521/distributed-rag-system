import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const cancelTask = async (taskId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/tasks/${taskId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('取消任務失敗');
      console.log(`任務 ${taskId} 已取消`);
    } catch (err) {
      setError('取消任務失敗');
      console.error('取消任務錯誤:', err);
    }
  };

  useEffect(() => {
    // 任務 WebSocket
    const taskWs = new WebSocket('ws://localhost:8000/api/ws/tasks');
    taskWs.onopen = () => {
      console.log('任務 WebSocket 連線成功');
      setLoading(false);
    };
    taskWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到任務 WebSocket 數據:', data);
        const tasks = data.tasks || [];
        tasks.forEach(task => {
          console.log(`任務 ${task.task_id} 狀態: ${task.status}`);
          if (task.status === 'PENDING') {
            console.log(`應顯示取消按鈕 for 任務 ${task.task_id}`);
          }
        });
        setTasks(tasks);
        setError(null);
      } catch (err) {
        setError('解析任務數據失敗');
        console.error('解析任務 WebSocket 數據錯誤:', err);
      }
    };
    taskWs.onerror = () => {
      setError('任務 WebSocket 連線錯誤');
      setLoading(false);
      console.error('任務 WebSocket 連線錯誤');
    };
    taskWs.onclose = () => {
      console.log('任務 WebSocket 連線關閉');
      setError('任務 WebSocket 連線已斷開');
      setLoading(false);
    };

    // 節點資源 WebSocket
    const nodeWs = new WebSocket('ws://localhost:8000/api/ws/nodes');
    nodeWs.onopen = () => {
      console.log('節點 WebSocket 連線成功');
    };
    nodeWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到節點 WebSocket 數據:', data);
        if (data.error) {
          setError(data.error);
        } else {
          setNodes(data.nodes || []);
        }
      } catch (err) {
        setError('解析節點數據失敗');
        console.error('解析節點 WebSocket 數據錯誤:', err);
      }
    };
    nodeWs.onerror = () => {
      setError('節點 WebSocket 連線錯誤');
      console.error('節點 WebSocket 連線錯誤');
    };
    nodeWs.onclose = () => {
      console.log('節點 WebSocket 連線關閉');
      setError('節點 WebSocket 連線已斷開');
    };

    return () => {
      taskWs.close();
      nodeWs.close();
    };
  }, []);

  return (
    <div>
      <Link to="/">返回主頁</Link>
      <h2>任務列表</h2>
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
                {task.status === 'PENDING' ? (
                  <button onClick={() => cancelTask(task.task_id)}>取消</button>
                ) : (
                  '-'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <h2>節點資源監控</h2>
      {loading && <p>載入中...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table border="1">
        <thead>
          <tr>
            <th>節點</th>
            <th>CPU 使用率</th>
            <th>記憶體使用率</th>
            <th>記憶體使用量</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((node) => (
            <tr key={node.node}>
              <td>{node.node}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <div style={{
                    width: '100px',
                    background: '#e0e0e0',
                    height: '10px',
                    marginRight: '10px'
                  }}>
                    <div style={{
                      width: `${node.cpu_percent}%`,
                      background: node.cpu_percent > 80 ? 'red' : node.cpu_percent > 50 ? 'orange' : 'green',
                      height: '100%'
                    }}></div>
                  </div>
                  {node.cpu_percent}%
                </div>
              </td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <div style={{
                    width: '100px',
                    background: '#e0e0e0',
                    height: '10px',
                    marginRight: '10px'
                  }}>
                    <div style={{
                      width: `${node.memory_percent}%`,
                      background: node.memory_percent > 80 ? 'red' : node.memory_percent > 50 ? 'orange' : 'green',
                      height: '100%'
                    }}></div>
                  </div>
                  {node.memory_percent}%
                </div>
              </td>
              <td>{node.memory_used_mb} / {node.memory_total_mb} MB</td>
            </tr>
          ))}
        </tbody>
      </table>

    </div>
  );
};

export default TaskManager;
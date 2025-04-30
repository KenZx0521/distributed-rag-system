import React, { useState } from 'react';
import FileUpload from '../components/FileUpload';
import QueryInput from '../components/QueryInput';
import ResultDisplay from '../components/ResultDisplay';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

const Home = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleQuerySubmit = async (query) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      // 提交查詢任務
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!response.ok) {
        throw new Error('查詢任務提交失敗');
      }
      const data = await response.json();
      const taskId = data.task_id;

      // 輪詢任務狀態
      const pollTaskStatus = async () => {
        const taskResponse = await fetch(`http://localhost:8000/api/tasks/${taskId}`);
        if (!taskResponse.ok) {
          throw new Error('查詢任務狀態失敗');
        }
        const taskData = await taskResponse.json();
        
        if (taskData.status === 'SUCCESS') {
          setResult(JSON.stringify(taskData.result, null, 2));
          setLoading(false);
        } else if (taskData.status === 'FAILED') {
          setError(taskData.error || '查詢任務失敗');
          setLoading(false);
        } else {
          // 任務仍在進行，1 秒後重試
          setTimeout(pollTaskStatus, 1000);
        }
      };

      await pollTaskStatus();
    } catch (err) {
      setError('查詢失敗，請稍後再試');
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    setLoading(true);
    setError(null);
    setUploadStatus('正在上傳檔案...');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error('檔案上傳任務提交失敗');
      }
      const data = await response.json();
      setUploadStatus(`上傳成功，任務 ID: ${data.task_id}`);
    } catch (err) {
      setError('檔案上傳失敗，請稍後再試');
      setUploadStatus('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>分散式 RAG 系統</h1>
      <FileUpload onUpload={handleFileUpload} />
      {uploadStatus && <p>{uploadStatus}</p>}
      <QueryInput onSubmit={handleQuerySubmit} />
      {loading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} />}
      <ResultDisplay result={result} />
    </div>
  );
};

export default Home;
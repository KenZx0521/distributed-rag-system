// src/components/FileUpload.js
import React, { useState } from 'react';
import '../styles/FileUpload.css'; // 引入樣式

function FileUpload({ onUpload }) {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
      setUploadStatus('');
    } else {
      setUploadStatus('請選擇有效的 CSV 檔案');
      setFile(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file) {
      onUpload(file);
      setUploadStatus('檔案上傳中...');
      setFile(null);
    } else {
      setUploadStatus('請先選擇一個 CSV 檔案');
    }
  };

  return (
    <div className="file-upload">
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
        />
        <button type="submit" disabled={!file}>
          上傳 CSV
        </button>
      </form>
      {uploadStatus && <p>{uploadStatus}</p>}
    </div>
  );
}

export default FileUpload;
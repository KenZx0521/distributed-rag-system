import React, { useState, useEffect } from 'react';
import TaskManager from '../components/TaskManager';

const Tasks = () => {
  return (
    <div>
      <h1>任務管理</h1>
      <TaskManager />
    </div>
  );
};

export default Tasks;
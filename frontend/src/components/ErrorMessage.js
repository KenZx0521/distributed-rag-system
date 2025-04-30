import React from 'react';

function ErrorMessage({ message }) {
  return message ? <div className="error">{message}</div> : null;
}

export default ErrorMessage;
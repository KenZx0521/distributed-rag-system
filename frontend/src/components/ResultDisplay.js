import React from 'react';

function ResultDisplay({ result }) {
  return (
    <div>
      {result ? <p>{result}</p> : <p>尚未有結果</p>}
    </div>
  );
}

export default ResultDisplay;
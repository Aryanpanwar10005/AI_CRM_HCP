import React from 'react';

const SentimentSelector = ({ value, onChange, highlightClass }) => {
  return (
    <div className="form-group">
      <label>Observed/Inferred HCP Sentiment</label>
      <div className={`sentiment-container ${highlightClass}`}>
        {['Positive', 'Neutral', 'Negative'].map((opt) => (
          <label key={opt} className="sentiment-option">
            <input
              type="radio"
              name="sentiment"
              value={opt}
              checked={value === opt}
              onChange={() => onChange(opt)}
            />
            <span className={`dot ${opt.toLowerCase()}`}></span>
            {opt}
          </label>
        ))}
      </div>
    </div>
  );
};

export default SentimentSelector;

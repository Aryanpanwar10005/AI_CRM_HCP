import React from 'react';

const FormField = ({ label, id, type = 'text', placeholder, value, onChange, className, children, rows }) => {
  return (
    <div className={`form-group ${className}`}>
      {type === 'checkbox' ? (
        <div className="checkbox-container">
          <input
            type="checkbox"
            id={id}
            name={id}
            checked={value}
            onChange={onChange}
            className={className}
          />
          <label htmlFor={id} className="checkbox-label">{label}</label>
        </div>
      ) : type === 'textarea' ? (
        <textarea
          id={id}
          name={id}
          rows={rows || 3}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          className={className}
        />
      ) : type === 'select' ? (
        <>
          <label htmlFor={id}>{label}</label>
          <select id={id} name={id} value={value} onChange={onChange} className={className}>
            {children}
          </select>
        </>
      ) : (
        <>
          <label htmlFor={id}>{label}</label>
          <input
            type={type}
            id={id}
            name={id}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={className}
          />
        </>
      )}
    </div>
  );
};

export default FormField;

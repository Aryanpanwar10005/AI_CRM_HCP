import React from 'react';
import { Search, Plus } from 'lucide-react';

const MaterialsSection = ({ materials, onChange, highlightClass }) => {
  return (
    <>
      <h3 className="section-heading">Materials Shared / Samples Distributed</h3>
      <div className="materials-samples-container">
        <div className="sub-section-row">
          <label>Materials Shared</label>
          <button className="secondary-btn">
            <Search size={14} />
            Search/Add
          </button>
        </div>
        <div className="textarea-container">
          <textarea
            id="materials_shared"
            name="materials_shared"
            rows="2"
            placeholder="List materials shared..."
            value={materials}
            onChange={onChange}
            className={highlightClass}
            style={{ marginBottom: '16px' }}
          />
        </div>

        <div className="sub-section-row">
          <label>Samples Distributed</label>
          <button className="secondary-btn">
            <Plus size={14} />
            Add Sample
          </button>
        </div>
        <p className="empty-text">No samples added.</p>
      </div>
    </>
  );
};

export default MaterialsSection;

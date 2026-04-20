import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  Mic, 
  Sparkles,
  Send,
  Loader2
} from 'lucide-react';

import { 
  updateField, 
  updateFromAI, 
  clearHighlights, 
  resetForm,
  setSaving,
  setSaveSuccess
} from '../store/formSlice';
import { addMessage, setTyping } from '../store/chatSlice';
import { setHcps } from '../store/hcpSlice';
import api from '../api/axios';

import './LogInteractionPage.css';

const TECHNICAL_LINE_PATTERN = /\b(form_updates|current_form_state|current_interaction_id|interaction_id|tool_call|tool_calls|hcp_id|raw_notes|traceback|json\.loads|langgraph|log_interaction|edit_interaction|get_hcp_profile|compliance_check|next_best_action)\b/i;
const META_REPLY_PATTERN = /^(here (is|are)|below is|i found|the following).*?(code|json|technical|raw|payload|object|block|response)/i;
const JSON_PAIR_PATTERN = /["']?[a-zA-Z_][\w]*["']?\s*:/;
const FIELD_LABELS = {
  hcp_name: 'HCP name',
  product_discussed: 'product discussed',
  materials_shared: 'materials shared',
  key_topics: 'key discussion topics',
  follow_up_notes: 'follow-up notes',
  follow_up_date: 'follow-up date'
};

const looksTechnicalText = (value) => {
  const text = String(value || '').trim();
  if (!text) return false;
  if (TECHNICAL_LINE_PATTERN.test(text)) return true;

  try {
    JSON.parse(text);
    return true;
  } catch {
    // Not JSON, continue with shape checks below.
  }

  if (JSON_PAIR_PATTERN.test(text) && /[{}\[\]]/.test(text)) return true;
  return /=>|<\/?[a-z][\s\S]*>|^\s*(const|let|var|function|def|class|import|return)\b|;\s*$/i.test(text);
};

const stripFencedBlocks = (value) =>
  value.replace(/```[a-zA-Z0-9_-]*\s*([\s\S]*?)```/g, (_, body) =>
    looksTechnicalText(body) ? '' : body.trim()
  );

const stripBalancedJson = (value) => {
  let output = '';
  let index = 0;

  while (index < value.length) {
    if (value[index] !== '{') {
      output += value[index];
      index += 1;
      continue;
    }

    let depth = 0;
    let endIndex = index;

    while (endIndex < value.length) {
      if (value[endIndex] === '{') depth += 1;
      if (value[endIndex] === '}') depth -= 1;
      if (depth === 0) break;
      endIndex += 1;
    }

    if (depth === 0) {
      const candidate = value.slice(index, endIndex + 1);
      if (looksTechnicalText(candidate)) {
        index = endIndex + 1;
        continue;
      }
    }

    output += value[index];
    index += 1;
  }

  return output;
};

const normalizeAssistantText = (content) => {
  let text = stripBalancedJson(stripFencedBlocks(String(content || '')));

  Object.entries(FIELD_LABELS).forEach(([field, label]) => {
    text = text.replace(new RegExp(`\\b${field}\\b`, 'gi'), label);
  });

  text = text
    .replace(/`/g, '')
    .replace(/\(ID:\s*\d+\)/gi, '')
    .replace(/\binteraction\s*#\d+\b/gi, 'the interaction')
    .replace(/\bStrategic NBA:\s*/gi, 'Next best action: ')
    .replace(/\bYou ARE compliant\b/gi, 'This is within the monthly limit')
    .replace(/\bDO NOT VISIT again this month\b/gi, 'Do not schedule another in-person visit this month')
    .replace(/\s+([.,;:!?])/g, '$1');

  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !META_REPLY_PATTERN.test(line) && !TECHNICAL_LINE_PATTERN.test(line) && !looksTechnicalText(line));

  return lines.length
    ? lines.join('\n')
    : 'I processed that and kept the next step clear.';
};

const renderMessageContent = (message) => {
  const content = message.role === 'assistant'
    ? normalizeAssistantText(message.content)
    : String(message.content || '');

  return content
    .split(/\r?\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const listItem = line.match(/^([-*]|\d+\.)\s+(.*)$/);
      return (
        <p
          className={`message-line${listItem ? ' message-list-item' : ''}`}
          key={`${index}-${line.slice(0, 16)}`}
        >
          {listItem ? listItem[2] : line}
        </p>
      );
    });
};

const LogInteractionPage = () => {
  const dispatch = useDispatch();
  const formData = useSelector((state) => state.form);
  const { messages, isTyping } = useSelector((state) => state.chat);
  const { list: hcps } = useSelector((state) => state.hcps);
  
  const [chatInput, setChatInput] = useState('');
  const chatMessagesRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    const chatMessages = chatMessagesRef.current;
    if (!chatMessages) return;
    chatMessages.scrollTo({
      top: chatMessages.scrollHeight,
      behavior: 'smooth'
    });
  }, [messages, isTyping]);

  // Fetch HCPs on mount
  useEffect(() => {
    const fetchHcps = async () => {
      try {
        const response = await api.get('/api/hcps');
        dispatch(setHcps(response.data));
      } catch (err) {
        console.error('Failed to fetch HCPs:', err);
      }
    };
    fetchHcps();
  }, [dispatch]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    const fieldValue = type === 'checkbox' ? checked : value;
    
    dispatch(updateField({ name, value: fieldValue }));
  };

  // Sync HCP ID when name changes (especially from AI updates)
  useEffect(() => {
    if (formData.hcp_name && hcps.length > 0) {
      const hcp = hcps.find(h => h.name.toLowerCase().includes(formData.hcp_name.toLowerCase()));
      if (hcp && hcp.id !== formData.hcp_id) {
        dispatch(updateField({ name: 'hcp_id', value: hcp.id }));
      }
    }
  }, [formData.hcp_name, hcps, formData.hcp_id, dispatch]);

  const handleSentimentChange = (value) => {
    dispatch(updateField({ name: 'sentiment', value }));
  };

  const handleChatSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!chatInput.trim() || isTyping) return;
    
    const userMsg = chatInput.trim();
    dispatch(addMessage({ role: 'user', content: userMsg }));
    setChatInput('');
    dispatch(setTyping(true));
    
    try {
      // API endpoint from requirements (backend/routers/chat.py)
      const response = await api.post('/api/chat', {
        message: userMsg,
        current_form_state: formData,
        session_id: "session_123" // Simplified for now
      });

      const { reply, form_updates } = response.data;
      
      dispatch(addMessage({ role: 'assistant', content: reply }));
      
      if (form_updates && Object.keys(form_updates).length > 0) {
        dispatch(updateFromAI(form_updates));
        
        // Phase 4 specific: 1500ms then clear
        setTimeout(() => {
          dispatch(clearHighlights());
        }, 1500);
      }
    } catch (err) {
      console.error('Chat error:', err);
      dispatch(addMessage({ role: 'assistant', content: "Sorry, I'm having trouble connecting to my brain. Please try again later." }));
    } finally {
      dispatch(setTyping(false));
    }
  };

  const handleSave = async () => {
    dispatch(setSaving(true));
    try {
      // Filter only relevant fields for the backend
      const payload = {
        hcp_id: formData.hcp_id,
        date: formData.date,
        mode: formData.mode,
        product_discussed: formData.product_discussed,
        sentiment: formData.sentiment,
        materials_shared: formData.materials_shared,
        key_topics: formData.key_topics,
        outcome: formData.outcome,
        follow_up_date: formData.follow_up_date,
        follow_up_notes: formData.follow_up_notes,
        status: 'Completed'
      };
      
      await api.post('/api/interactions', payload);
      dispatch(setSaveSuccess(true));
      dispatch(addMessage({ role: 'assistant', content: "Interaction saved successfully." }));
      setTimeout(() => dispatch(setSaveSuccess(false)), 3000);
    } catch (err) {
      console.error('Save error:', err);
      alert("Failed to save interaction.");
    } finally {
      dispatch(setSaving(false));
    }
  };

  const isHighlighted = (field) => formData.highlightedFields.includes(field) ? 'field-highlight' : '';

  return (
    <div className="log-interaction-container">
      <header className="log-interaction-header">
        <div className="header-top">
          <h1>Log HCP Interaction</h1>
          <button className="reset-btn" onClick={() => dispatch(resetForm())}>Reset Form</button>
        </div>
        <p className="header-subtitle">Record your engagement details with healthcare professionals</p>
      </header>

      <main className="log-interaction-content">
        {/* Left Panel: 40% Form */}
        <section className="crm-card left-card">
          <div className="card-header">
            <h2 className="card-title">Interaction Details</h2>
            <span className="status-badge">New Entry</span>
          </div>

          <div className="scrollable-form">
            <div className="form-row">
              <div className="form-group flex-2">
                <label>HCP Name</label>
                <select 
                  name="hcp_name" 
                  value={formData.hcp_name} 
                  onChange={handleInputChange}
                  className={isHighlighted('hcp_name')}
                >
                  <option value="">Select HCP...</option>
                  {hcps.map(hcp => (
                    <option key={hcp.id} value={hcp.name}>{hcp.name} - {hcp.specialty}</option>
                  ))}
                </select>
              </div>
              <div className="form-group flex-1">
                <label>Mode</label>
                <select 
                  name="mode" 
                  value={formData.mode} 
                  onChange={handleInputChange}
                  className={isHighlighted('mode')}
                >
                  <option value="Meeting">In-Person</option>
                  <option value="Call">Phone Call</option>
                  <option value="Email">Email</option>
                  <option value="Video">Video Call</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Product Discussed</label>
                <input 
                  type="text" 
                  name="product_discussed" 
                  placeholder="e.g. OncoBoost Phase III"
                  value={formData.product_discussed}
                  onChange={handleInputChange}
                  className={isHighlighted('product_discussed')}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Date</label>
                <input 
                  type="date" 
                  name="date" 
                  value={formData.date}
                  onChange={handleInputChange}
                  className={isHighlighted('date')}
                />
              </div>
              <div className="form-group">
                <label>Time</label>
                <input 
                  type="time" 
                  name="time" 
                  value={formData.time}
                  onChange={handleInputChange}
                  className={isHighlighted('time')}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Key Discussion Topics</label>
                <div className="textarea-wrapper">
                  <textarea 
                    name="key_topics" 
                    rows="3" 
                    placeholder="What did you talk about?"
                    value={formData.key_topics}
                    onChange={handleInputChange}
                    className={isHighlighted('key_topics')}
                  ></textarea>
                  <Mic className="textarea-icon" size={14} />
                </div>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Materials Shared</label>
                <input 
                  type="text" 
                  name="materials_shared" 
                  placeholder="e.g. Clinical Data Booklet"
                  value={formData.materials_shared}
                  onChange={handleInputChange}
                  className={isHighlighted('materials_shared')}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>HCP Sentiment</label>
                <div className="sentiment-bar">
                  {['Positive', 'Neutral', 'Negative'].map(s => (
                    <label key={s} className={`sentiment-btn ${formData.sentiment === s ? 'active' : ''}`}>
                      <input 
                        type="radio" 
                        name="sentiment" 
                        value={s} 
                        checked={formData.sentiment === s}
                        onChange={() => handleSentimentChange(s)}
                      />
                      {s}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Interaction Outcome</label>
                <textarea 
                  name="outcome" 
                  rows="2" 
                  placeholder="Next steps..."
                  value={formData.outcome}
                  onChange={handleInputChange}
                  className={isHighlighted('outcome')}
                ></textarea>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Follow-up Actions</label>
                <textarea 
                  name="follow_up_notes" 
                  rows="2" 
                  placeholder="Items for next visit..."
                  value={formData.follow_up_notes}
                  onChange={handleInputChange}
                  className={isHighlighted('follow_up_notes')}
                ></textarea>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Follow-up Date</label>
                <input 
                  type="date" 
                  name="follow_up_date" 
                  value={formData.follow_up_date}
                  onChange={handleInputChange}
                  className={isHighlighted('follow_up_date')}
                />
              </div>
            </div>

            <div className="form-row">
              <label className="compliance-box">
                <input 
                  type="checkbox" 
                  name="compliance_consent" 
                  checked={formData.compliance_consent}
                  onChange={handleInputChange}
                />
                <span>I confirm compliance with PhRMA guidelines.</span>
              </label>
            </div>
          </div>

          <div className="form-footer">
            <button 
              className="log-btn primary" 
              onClick={handleSave}
              disabled={formData.isSaving || !formData.compliance_consent}
            >
              {formData.isSaving ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
              {formData.saveSuccess ? "Saved!" : "Save Interaction"}
            </button>
          </div>
        </section>

        {/* Right Panel: 60% Chat */}
        <section className="crm-card right-card chat-panel">
          <div className="chat-header">
            <div className="ai-avatar">AI</div>
            <div>
              <h2 className="card-title">AI Assistant</h2>
              <p className="status-text">Online</p>
            </div>
          </div>
          
          <div className="chat-messages" ref={chatMessagesRef}>
            {messages.map((msg, i) => (
              <div key={i} className={`message-bubble ${msg.role}`}>
                <div className="message-content">{renderMessageContent(msg)}</div>
              </div>
            ))}
            {isTyping && <div className="typing-indicator"><span></span><span></span><span></span></div>}
          </div>

          <form className="chat-input-container" onSubmit={handleChatSubmit}>
            <input 
              type="text" 
              placeholder="Describe the HCP interaction..." 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={isTyping}
            />
            <button type="submit" className="send-btn" disabled={isTyping || !chatInput.trim()}>
              {isTyping ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
};

export default LogInteractionPage;

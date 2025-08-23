import React, { useState, useEffect } from 'react';
import { MessageCircle, Brain, Target, Lightbulb } from 'lucide-react';

// Natural Language Preference Input Component
export const NaturalLanguageInput = ({ onPreferencesParsed, pilotContext }) => {
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [parseResult, setParseResult] = useState(null);
  const [error, setError] = useState(null);

  const handleParse = async () => {
    if (!inputText.trim()) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const response = await fetch('/api/parse_preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferences_text: inputText,
          pilot_context: pilotContext
        })
      });
      
      if (!response.ok) throw new Error('Failed to parse preferences');
      
      const result = await response.json();
      setParseResult(result);
      onPreferencesParsed(result);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="ai-natural-input">
      <div className="input-header">
        <Brain className="icon" />
        <h3>Tell AI What You Want</h3>
        <span className="ai-badge">AI-Powered</span>
      </div>
      
      <div className="input-container">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Just tell me what you want... 'I want weekends off for family time, prefer morning departures, avoid red-eyes completely'"
          className="natural-input"
          rows={3}
        />
        
        <button 
          onClick={handleParse}
          disabled={!inputText.trim() || isProcessing}
          className="parse-btn"
        >
          {isProcessing ? 'AI Analyzing...' : 'Parse with AI'}
        </button>
      </div>
      
      {parseResult && (
        <div className="parse-result">
          <div className="confidence-indicator">
            <span className="confidence-score">{(parseResult.confidence * 100).toFixed(0)}% Confidence</span>
            <span className="method">{parseResult.method}</span>
          </div>
          
          <div className="ai-reasoning">
            <h4>🧠 AI Analysis:</h4>
            <p>{parseResult.reasoning}</p>
          </div>
          
          {parseResult.suggestions?.length > 0 && (
            <div className="suggestions">
              <h4>💡 AI Suggestions:</h4>
              <ul>
                {parseResult.suggestions.map((suggestion, i) => (
                  <li key={i}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}
    </div>
  );
};

// AI-Enhanced Schedule Display Component
export const AIScheduleResults = ({ schedules, onScheduleSelect, pilotContext }) => {
  const [enhancedResults, setEnhancedResults] = useState(null);
  const [isEnhancing, setIsEnhancing] = useState(false);

  const enhanceWithAI = async () => {
    if (!schedules?.length) return;
    
    setIsEnhancing(true);
    
    try {
      const response = await fetch('/api/optimize_enhanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feature_bundle: {
            preference_schema: schedules[0]?.preferences || {},
            // Add other required bundle fields
          },
          use_llm: true,
          pilot_context: pilotContext
        })
      });
      
      const result = await response.json();
      setEnhancedResults(result);
      
    } catch (err) {
      console.error('AI enhancement failed:', err);
    } finally {
      setIsEnhancing(false);
    }
  };

  useEffect(() => {
    if (schedules?.length > 0) {
      enhanceWithAI();
    }
  }, [schedules]);

  if (!schedules?.length) return null;

  return (
    <div className="ai-schedule-results">
      <div className="results-header">
        <Target className="icon" />
        <h3>AI-Enhanced Results</h3>
        {isEnhancing && <div className="processing-indicator">🤖 AI Analyzing...</div>}
      </div>
      
      {enhancedResults && (
        <div className="ai-analysis">
          <div className="optimization-summary">
            <div className="metric">
              <span className="label">Quality Score:</span>
              <span className="value">{(enhancedResults.optimization_analysis.quality * 100).toFixed(0)}%</span>
            </div>
            <div className="metric">
              <span className="label">Preference Alignment:</span>
              <span className="value">{(enhancedResults.optimization_analysis.preference_alignment * 100).toFixed(0)}%</span>
            </div>
            <div className="metric">
              <span className="label">AI Confidence:</span>
              <span className="value">{(enhancedResults.ai_insights.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
          
          <div className="ai-recommendation">
            <h4>🏆 AI Recommendation:</h4>
            <p>{enhancedResults.recommendations.explanation}</p>
          </div>
          
          <div className="trade-off-analysis">
            <h4>⚖️ Trade-off Analysis:</h4>
            <p>{enhancedResults.optimization_analysis.trade_off_analysis}</p>
          </div>
        </div>
      )}
      
      <div className="schedule-list">
        {(enhancedResults?.enhanced_candidates || schedules).map((schedule, index) => (
          <ScheduleCard 
            key={schedule.candidate_id || index}
            schedule={schedule}
            isRecommended={schedule.candidate_id === enhancedResults?.recommendations?.recommended_candidate_id}
            onSelect={() => onScheduleSelect(schedule)}
          />
        ))}
      </div>
    </div>
  );
};

// Individual Schedule Card with AI Insights
const ScheduleCard = ({ schedule, isRecommended, onSelect }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className={`schedule-card ${isRecommended ? 'recommended' : ''}`}>
      <div className="card-header">
        <div className="schedule-id">{schedule.candidate_id}</div>
        {isRecommended && <div className="recommended-badge">🏆 AI Recommended</div>}
        <div className="scores">
          <span className="math-score">Math: {schedule.score?.toFixed(2)}</span>
          {schedule.enhanced_score && (
            <span className="ai-score">AI: {schedule.enhanced_score.toFixed(2)}</span>
          )}
        </div>
      </div>
      
      <div className="schedule-metrics">
        <div className="metric">
          <span className="label">Credit:</span>
          <span className="value">{schedule.total_credit}</span>
        </div>
        <div className="metric">
          <span className="label">Duty:</span>
          <span className="value">{schedule.total_duty}</span>
        </div>
        {schedule.pilot_fit_score && (
          <div className="metric">
            <span className="label">Pilot Fit:</span>
            <span className="value">{(schedule.pilot_fit_score * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>
      
      {schedule.ai_reasoning && (
        <div className="ai-insights">
          <h5>🧠 AI Analysis:</h5>
          <p>{schedule.ai_reasoning}</p>
          
          {schedule.strengths?.length > 0 && (
            <div className="strengths">
              <h6>💪 Strengths:</h6>
              <ul>
                {schedule.strengths.slice(0, 2).map((strength, i) => (
                  <li key={i}>{strength}</li>
                ))}
              </ul>
            </div>
          )}
          
          {schedule.lifestyle_impact && (
            <div className="lifestyle-impact">
              <h6>🏠 Lifestyle Impact:</h6>
              <p>{schedule.lifestyle_impact}</p>
            </div>
          )}
        </div>
      )}
      
      <div className="card-actions">
        <button 
          onClick={() => setShowDetails(!showDetails)}
          className="details-btn"
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
        <button 
          onClick={onSelect}
          className="select-btn"
        >
          Select Schedule
        </button>
      </div>
      
      {showDetails && schedule.improvement_suggestions?.length > 0 && (
        <div className="improvement-suggestions">
          <h6>💡 AI Suggestions:</h6>
          <ul>
            {schedule.improvement_suggestions.map((suggestion, i) => (
              <li key={i}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Chat Widget Component
export const AIChat = ({ pilotContext, currentSchedules }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId] = useState(`pilot_${Date.now()}`);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      initializeChat();
    }
  }, [isOpen]);

  const initializeChat = async () => {
    try {
      const response = await fetch('/api/chat/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: sessionId,
          pilot_context: pilotContext
        })
      });
      
      const result = await response.json();
      setMessages([{
        role: 'assistant',
        content: result.greeting_message,
        timestamp: new Date()
      }]);
      
    } catch (err) {
      setMessages([{
        role: 'assistant',
        content: "Hello! I'm VectorBot, your AI bidding assistant. How can I help you today?",
        timestamp: new Date()
      }]);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isProcessing) return;
    
    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsProcessing(true);
    
    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: sessionId,
          message: inputMessage,
          context_update: {
            current_schedules: currentSchedules
          }
        })
      });
      
      const result = await response.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.response,
        timestamp: new Date()
      }]);
      
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm having trouble right now. Please try again or contact support.",
        timestamp: new Date()
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className={`ai-chat-widget ${isOpen ? 'open' : 'closed'}`}>
      <div className="chat-toggle" onClick={() => setIsOpen(!isOpen)}>
        <MessageCircle className="icon" />
        <span>VectorBot</span>
        {!isOpen && <div className="notification-dot"></div>}
      </div>
      
      {isOpen && (
        <div className="chat-container">
          <div className="chat-header">
            <div className="bot-info">
              <div className="bot-avatar">🤖</div>
              <div>
                <h4>VectorBot</h4>
                <p>AI Bidding Assistant</p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="close-btn">×</button>
          </div>
          
          <div className="chat-messages">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-content">{message.content}</div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="message assistant typing">
                <div className="typing-indicator">VectorBot is thinking...</div>
              </div>
            )}
          </div>
          
          <div className="chat-input">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask about bidding strategy, preferences, or career advice..."
              disabled={isProcessing}
            />
            <button onClick={sendMessage} disabled={!inputMessage.trim() || isProcessing}>
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Quick Tips Component
export const AIQuickTips = ({ category = 'general' }) => {
  const [tips, setTips] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadTips = async (cat) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/chat/tips/${cat}`);
      const result = await response.json();
      setTips(result.tips || []);
    } catch (err) {
      console.error('Failed to load tips:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTips(category);
  }, [category]);

  return (
    <div className="ai-quick-tips">
      <div className="tips-header">
        <Lightbulb className="icon" />
        <h4>AI Tips</h4>
      </div>
      
      <div className="tip-categories">
        {['general', 'family', 'commuting', 'career'].map(cat => (
          <button
            key={cat}
            onClick={() => loadTips(cat)}
            className={`category-btn ${cat === category ? 'active' : ''}`}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>
      
      {loading ? (
        <div className="loading">Loading AI tips...</div>
      ) : (
        <div className="tips-list">
          {tips.map((tip, index) => (
            <div key={index} className="tip-item">
              {tip}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Main AI Features Dashboard
export const AIFeaturesDashboard = ({ pilotContext, schedules, onScheduleSelect }) => {
  const [activeFeature, setActiveFeature] = useState('input');

  return (
    <div className="ai-features-dashboard">
      <div className="dashboard-header">
        <h2>🤖 VectorBid AI Features</h2>
        <p>World's first AI-powered pilot bidding system</p>
      </div>
      
      <div className="feature-tabs">
        <button 
          onClick={() => setActiveFeature('input')}
          className={`tab ${activeFeature === 'input' ? 'active' : ''}`}
        >
          Natural Language Input
        </button>
        <button 
          onClick={() => setActiveFeature('schedules')}
          className={`tab ${activeFeature === 'schedules' ? 'active' : ''}`}
        >
          AI-Enhanced Results
        </button>
        <button 
          onClick={() => setActiveFeature('tips')}
          className={`tab ${activeFeature === 'tips' ? 'active' : ''}`}
        >
          AI Tips
        </button>
      </div>
      
      <div className="feature-content">
        {activeFeature === 'input' && (
          <NaturalLanguageInput 
            pilotContext={pilotContext}
            onPreferencesParsed={(result) => console.log('Preferences parsed:', result)}
          />
        )}
        
        {activeFeature === 'schedules' && (
          <AIScheduleResults 
            schedules={schedules}
            pilotContext={pilotContext}
            onScheduleSelect={onScheduleSelect}
          />
        )}
        
        {activeFeature === 'tips' && (
          <AIQuickTips category="general" />
        )}
      </div>
      
      <AIChat 
        pilotContext={pilotContext}
        currentSchedules={schedules}
      />
    </div>
  );
};
/*
 * Lucidia Frontend Dashboard
 *
 * A simple React-based interface for interacting with the Lucidia backend. Users
 * can submit questions, view reasoning results, and monitor agent status in
 * real time via WebSockets. The dashboard polls the backend for agent
 * metrics and listens on a WebSocket for reasoning completion events.
 */

const { useState, useEffect, useRef } = React;

function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [agentStatus, setAgentStatus] = useState([]);
  const wsRef = useRef(null);

  // Establish WebSocket connection on mount
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.hostname}:8000/ws/updates`;
    wsRef.current = new WebSocket(wsUrl);
    wsRef.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'reasoning_complete') {
          const data = msg.data;
          setMessages((prev) => [...prev, { question: data.question, answer: data.answer, timestamp: data.timestamp }]);
        }
      } catch (e) {
        console.error('Invalid WebSocket message', e);
      }
    };
    wsRef.current.onclose = () => {
      console.warn('WebSocket connection closed');
    };
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Poll agent status periodically
  useEffect(() => {
    const fetchStatus = () => {
      fetch('/api/v1/agents/status')
        .then((res) => res.json())
        .then((data) => {
          if (data && data.agents) {
            setAgentStatus(data.agents);
          }
        })
        .catch((err) => console.error('Failed to fetch agent status', err));
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle form submission to ask a question
  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    fetch('/api/v1/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: trimmed }),
    })
      .then((res) => res.json())
      .then((data) => {
        // Append the response to messages; WebSocket will also push result
        setMessages((prev) => [...prev, { question: data.question, answer: data.answer, timestamp: data.timestamp }]);
        setQuestion('');
      })
      .catch((err) => console.error('Failed to submit question', err));
  };

  return (
    React.createElement('div', { style: { margin: '2rem' } },
      React.createElement('h1', null, 'Lucidia Dashboard'),
      React.createElement('form', { onSubmit: handleSubmit, style: { marginBottom: '1rem' } },
        React.createElement('input', {
          type: 'text',
          value: question,
          onChange: (e) => setQuestion(e.target.value),
          placeholder: 'Ask a question…',
          style: { width: '60%', padding: '0.5rem', fontSize: '1rem' }
        }),
        React.createElement('button', { type: 'submit', style: { padding: '0.5rem 1rem', fontSize: '1rem' } }, 'Ask')
      ),
      React.createElement('h2', null, 'Messages'),
      React.createElement('ul', null,
        messages.map((msg, idx) =>
          React.createElement('li', { key: idx, style: { marginBottom: '0.5rem' } },
            React.createElement('strong', null, 'Q: '), msg.question, React.createElement('br'),
            React.createElement('strong', null, 'A: '), msg.answer
          )
        )
      ),
      React.createElement('h2', null, 'Agent Status'),
      React.createElement('ul', null,
        agentStatus.map((agent) =>
          React.createElement('li', { key: agent.name }, `${agent.name}: ${agent.tasks_processed} tasks`)
        )
      )
    )
  );
}

// Mount the React application
ReactDOM.render(React.createElement(App), document.getElementById('root'));

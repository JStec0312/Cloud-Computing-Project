import { useState } from 'react';

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
        // Updated: Sending JSON data with 'email' and 'password'
        const response = await fetch('http://localhost:8000/api/v1/auth/login', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // We are sending JSON now
            },
            body: JSON.stringify({ 
                email: email, 
                password: password 
            }),
        });

        if (!response.ok) {
            // Try to read the error message from the backend if possible
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Login failed');
        }

        const data = await response.json();
        
        // Save the token (assuming the backend returns { "access_token": "..." })
        // If your backend calls it something else (like "token"), update this line.
        localStorage.setItem('token', data.access_token);
        
        onLoginSuccess();

    } catch (err) {
        setError(err.message);
        console.error(err);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', maxWidth: '300px', margin: 'auto', marginTop: '50px' }}>
      <h2>Cloud Drive Login</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <input 
          type="email" 
          placeholder="Email Address" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" style={{ cursor: 'pointer', padding: '10px' }}>Log In</button>
      </form>
      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
    </div>
  );
}

export default Login;
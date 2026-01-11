import { useState } from 'react';
import { domain_name } from '../config'

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState(''); 

  const [isRegistering, setIsRegistering] = useState(false); 
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    try {
        const response = await fetch(`${domain_name}/auth/login`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Login failed');
        }

        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        onLoginSuccess();

    } catch (err) {
        setError(err.message);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    try {
        const response = await fetch(`${domain_name}/auth/register`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                display_name: displayName,
                email: email, 
                password: password 
            }),
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Registration failed');
        }

        setSuccessMsg('✅ Registration successful! Please log in.');
        setIsRegistering(false);
        setPassword(''); 

    } catch (err) {
        setError(err.message);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', maxWidth: '300px', margin: 'auto', marginTop: '50px' }}>
      <h2>{isRegistering ? 'Create Account' : 'Cloud Drive Login'}</h2>
      
      <form onSubmit={isRegistering ? handleRegister : handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        
        {isRegistering && (
          <input 
            type="text" 
            placeholder="Display Name" 
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
        )}
        
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
        
        <button 
            type="submit" 
            style={{ 
                cursor: 'pointer', 
                padding: '10px', 
                backgroundColor: isRegistering ? '#4CAF50' : '#2196F3', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px' 
            }}
        >
            {isRegistering ? 'Register' : 'Log In'}
        </button>
      </form>

      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
      {successMsg && <p style={{ color: 'green', marginTop: '10px' }}>{successMsg}</p>}

      <p style={{ marginTop: '15px', fontSize: '0.9em', textAlign: 'center' }}>
        {isRegistering ? "Already have an account? " : "Don't have an account? "}
        <span 
            onClick={() => {
                setIsRegistering(!isRegistering);
                setError('');
                setSuccessMsg('');
            }} 
            style={{ color: '#2196F3', cursor: 'pointer', textDecoration: 'underline' }}
        >
            {isRegistering ? "Log in here" : "Register here"}
        </span>
      </p>
    </div>
  );
}

export default Login;
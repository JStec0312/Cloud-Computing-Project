import { useState } from 'react'
import Login from './components/Login'
import FilesList from './components/FilesList' // <--- IMPORT THIS

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  );

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      
      {!isAuthenticated ? (
        <Login onLoginSuccess={() => setIsAuthenticated(true)} />
      ) : (
        <div>
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', borderBottom: '1px solid #ddd', paddingBottom: '10px' }}>
            <h1 style={{ margin: 0 }}>📂 My Cloud Drive</h1>
            <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px' }}>
              Logout
            </button>
          </header>

          <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px' }}>
            {/* HERE IS THE NEW COMPONENT */}
            <FilesList /> 
          </div>
        </div>
      )}
    </div>
  )
}

export default App
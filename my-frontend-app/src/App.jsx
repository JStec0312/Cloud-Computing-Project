import { useState } from 'react'
import Login from './components/Login'
import FilesList from './components/FilesList'
import FileUpload from './components/FileUpload'
import { domain_name } from './config'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  );
  
  const [refreshKey, setRefreshKey] = useState(0);
  const [currentFolderId, setCurrentFolderId] = useState(null); 

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setCurrentFolderId(null);
  };

  const handleLogoutAll = async () => {
    if(!confirm("Are you sure you want to log out of ALL devices?")) return;

    try {
        const token = localStorage.getItem('token');
        await fetch(`${domain_name}/auth/logout/all`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    } catch (error) {
        console.error("Logout all error:", error);
    } finally {
        handleLogout();
        alert("Logged out from all devices.");
    }
  };

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      width: '100vw',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: '#1a1a1a',
      color: '#333',
      margin: 0,
      padding: 0,
      boxSizing: 'border-box'
    }}>
      
     
      <div style={{ 
        width: '100%', 
        maxWidth: '800px',        
        padding: '20px',
        borderRadius: '8px'
      }}>
        
        {!isAuthenticated ? (
          <Login onLoginSuccess={() => setIsAuthenticated(true)} />
        ) : (
          <div>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', borderBottom: '1px solid #444', paddingBottom: '10px' }}>
              <h1 style={{ margin: 0, color: '#f0f0f0' }}>My Cloud Drive</h1>
              
              <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                      onClick={handleLogoutAll} 
                      title="Invalidate all sessions"
                      style={{ padding: '8px 12px', cursor: 'pointer', backgroundColor: '#555', color: 'white', border: 'none', borderRadius: '4px' }}
                  >
                      Logout All
                  </button>

                  <button 
                      onClick={handleLogout} 
                      style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px' }}
                  >
                      Logout
                  </button>
              </div>
            </header>

            <FileUpload 
              onUploadSuccess={handleUploadSuccess} 
              currentFolderId={currentFolderId} 
            />

            <div style={{ border: '1px solid #444', padding: '20px', borderRadius: '8px', marginTop: '20px', backgroundColor: '#222' }}>
              <FilesList 
                key={refreshKey} 
                currentFolderId={currentFolderId}
                onNavigate={setCurrentFolderId}
              /> 
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
import { useState } from 'react'
import Login from './components/Login'
import FilesList from './components/FilesList'
import FileUpload from './components/FileUpload'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  );
  
  const [refreshKey, setRefreshKey] = useState(0);

  // --- NEW: LIFTED STATE ---
  // We keep track of the current folder here so BOTH components know about it
  const [currentFolderId, setCurrentFolderId] = useState(null); 

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto', color: '#333' }}>
      
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

          {/* 1. Pass currentFolderId so uploads go to the right place */}
          <FileUpload 
            onUploadSuccess={handleUploadSuccess} 
            currentFolderId={currentFolderId} 
          />

          {/* 2. Pass currentFolderId and the function to change it (onNavigate) */}
          <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginTop: '20px' }}>
            <FilesList 
              key={refreshKey} 
              currentFolderId={currentFolderId}
              onNavigate={setCurrentFolderId}
            /> 
          </div>
        </div>
      )}
    </div>
  )
}

export default App
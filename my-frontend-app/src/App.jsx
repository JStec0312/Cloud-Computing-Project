import { useState } from 'react'
import Login from './components/Login'
import FilesList from './components/FilesList'
import FileUpload from './components/FileUpload' // <--- Make sure this is imported

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  );
  
  // This number changes every time an upload finishes
  const [refreshKey, setRefreshKey] = useState(0);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  // We pass this function to the FileUpload component
  const handleUploadSuccess = () => {
    console.log("Upload finished! Refreshing list...");
    setRefreshKey(prev => prev + 1); // This change forces FilesList to re-render
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto', color: '#333' }}>
      
      {!isAuthenticated ? (
        <Login onLoginSuccess={() => setIsAuthenticated(true)} />
      ) : (
        <div>
          {/* Header */}
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', borderBottom: '1px solid #ddd', paddingBottom: '10px' }}>
            <h1 style={{ margin: 0 }}>📂 My Cloud Drive</h1>
            <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px' }}>
              Logout
            </button>
          </header>

          {/* 1. File Upload Section */}
          <FileUpload onUploadSuccess={handleUploadSuccess} />

          {/* 2. File List Section */}
          {/* The 'key' prop is the magic trick. When it changes, React deletes and recreates this component. */}
          <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginTop: '20px' }}>
            <FilesList key={refreshKey} /> 
          </div>
        </div>
      )}
    </div>
  )
}

export default App
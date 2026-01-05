import { useState, useEffect } from 'react';

function FilesList() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 1. Function to fetch files
  const fetchFiles = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // CHECK YOUR DOCS: The endpoint is likely /api/v1/files or /api/v1/files/list
      // I am guessing /api/v1/files based on standard REST practices.
      const response = await fetch('http://localhost:8000/api/v1/files', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`, // <--- THIS IS THE KEY!
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch files');
      }

      const data = await response.json();
      // Adjust this based on whether backend returns [ ... ] or { items: [ ... ] }
      setFiles(data); 
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 2. Run this when component mounts
  useEffect(() => {
    fetchFiles();
  }, []);

  if (loading) return <p>Loading files...</p>;
  if (error) return <p style={{color: 'red'}}>Error: {error}</p>;

  return (
    <div style={{ marginTop: '20px' }}>
      <h3>Your Files</h3>
      {files.length === 0 ? (
        <p>No files found. Upload one!</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {files.map((file) => (
            <li key={file.id || file.name} style={{ 
              padding: '10px', 
              borderBottom: '1px solid #eee',
              display: 'flex',
              justifyContent: 'space-between'
            }}>
              <span>📄 {file.name || file.filename}</span>
              <span style={{ color: '#888', fontSize: '0.9em' }}>
                {file.size ? `${file.size} bytes` : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default FilesList;
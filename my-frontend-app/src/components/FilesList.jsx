import { useState, useEffect } from 'react';

function FilesList() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchFiles = async () => {
    try {
      const token = localStorage.getItem('token');
      // Using 127.0.0.1 directly to match your backend fix
      const response = await fetch('http://localhost:8000/api/v1/files', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      console.log("Backend Data Received:", data); // <--- Check your browser console!

      // SAFETY CHECK: Ensure we extract the array correctly
      if (Array.isArray(data)) {
        setFiles(data);
      } else if (data.items && Array.isArray(data.items)) {
        // Some APIs return { items: [...] }
        setFiles(data.items);
      } else {
        // If we can't find an array, assume empty to prevent crash
        console.warn("Could not find file array in response", data);
        setFiles([]);
      }
      
    } catch (err) {
      console.error("Fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  if (loading) return <p style={{color: '#888'}}>Loading files...</p>;
  if (error) return <p style={{color: 'red'}}>Error: {error}</p>;

  return (
    <div style={{ marginTop: '20px', color: 'white' }}> 
      <h3>Your Files</h3>
      {files.length === 0 ? (
        <div style={{ padding: '20px', border: '1px dashed #555', borderRadius: '8px', color: '#aaa' }}>
          <p>No files found.</p>
        </div>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {files.map((file) => (
            <li key={file.id || file.name} style={{ 
              padding: '10px', 
              borderBottom: '1px solid #333',
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
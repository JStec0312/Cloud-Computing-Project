import { useState } from 'react';

function FileUpload({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setMessage('');
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setMessage('Please select a file first.');
      return;
    }

    setUploading(true);
    setMessage('');

    try {
      const token = localStorage.getItem('token');
      
      // --- CONSTRUCTING THE BODY ---
      const formData = new FormData();
      
      // 1. "file" parameter (REQUIRED by your spec)
      formData.append('file', selectedFile);

      // 2. "parent_id" parameter (OPTIONAL)
      // The spec says: "Jeśli brak - plik zostanie przesłany do Root"
      // So we simply DO NOT append it here.
      // If you implement folders later, you would do: 
      // formData.append('parent_id', currentFolderId);

      const response = await fetch('http://localhost:8000/api/v1/files', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          // IMPORTANT: Do NOT set Content-Type header manually.
          // The browser automatically sets it to "multipart/form-data; boundary=..."
        },
        body: formData, // This sends the binary body
      });

      if (!response.ok) {
        // Handle common upload errors (like 422 Validation Error)
        const errorText = await response.text();
        throw new Error(`Server responded with ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      setMessage('✅ Upload successful!');
      setSelectedFile(null);
      
      // Reset the file input visually
      document.getElementById('fileInput').value = ""; 

      if (onUploadSuccess) {
        onUploadSuccess();
      }

    } catch (error) {
      console.error('Upload Error:', error);
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ marginBottom: '20px', padding: '20px', border: '1px solid #444', borderRadius: '8px', backgroundColor: '#222', color: 'white' }}>
      <h4 style={{ marginTop: 0 }}>Upload New File</h4>
      <form onSubmit={handleUpload} style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
        <input 
          id="fileInput"
          type="file" 
          onChange={handleFileChange} 
          style={{ color: '#ccc' }}
        />
        <button 
          type="submit" 
          disabled={!selectedFile || uploading}
          style={{ 
            padding: '10px 20px', 
            cursor: 'pointer',
            backgroundColor: uploading ? '#555' : '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 'bold'
          }}
        >
          {uploading ? 'Uploading...' : 'Upload ⬆️'}
        </button>
      </form>
      {message && <p style={{ marginTop: '15px', fontWeight: 'bold', color: message.startsWith('✅') ? '#4CAF50' : '#f44336' }}>{message}</p>}
    </div>
  );
}

export default FileUpload;
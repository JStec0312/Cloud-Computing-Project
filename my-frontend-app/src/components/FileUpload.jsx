import { useState } from 'react';
import { domain_name } from '../config'
function FileUpload({ onUploadSuccess, currentFolderId }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [isZipMode, setIsZipMode] = useState(false);

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
      const formData = new FormData();
      formData.append('file', selectedFile);


      if (currentFolderId) {
        formData.append('parent_id', currentFolderId);
      }

      const endpoint = isZipMode 
        ? `${domain_name}/files/zip` 
        : `${domain_name}/files`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server Error (${response.status}): ${errorText}`);
      }

      setMessage(`✅ ${isZipMode ? 'Zip' : 'File'} uploaded successfully!`);
      setSelectedFile(null);
      document.getElementById('fileInput').value = ""; 
      
      if (onUploadSuccess) onUploadSuccess();

    } catch (error) {
      console.error('Upload Error:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleCreateFolder = async () => {
    const folderName = prompt("Enter folder name:");
    if (!folderName) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${domain_name}/files/folders`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          folder_name: folderName,
          parent_folder_id: currentFolderId 
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Failed to create folder");
      }

      setMessage(`Folder "${folderName}" created!`);
      if (onUploadSuccess) onUploadSuccess();

    } catch (error) {
      console.error('Folder Error:', error);
      alert(`Error creating folder: ${error.message}`);
    }
  };

  return (
    <div style={{ marginBottom: '20px', padding: '20px', border: '1px solid #444', borderRadius: '8px', backgroundColor: '#222', color: 'white' }}>
      <div style={{ display: 'flex', gap: '15px', marginBottom: '15px', borderBottom: '1px solid #444', paddingBottom: '10px' }}>
        <button 
          onClick={handleCreateFolder}
          style={{ padding: '8px 12px', cursor: 'pointer', backgroundColor: '#FF9800', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          New Folder
        </button>

        <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: '#ccc' }}>
          <input 
            type="checkbox" 
            checked={isZipMode} 
            onChange={(e) => setIsZipMode(e.target.checked)} 
          />
          Upload as Zip (Unpack)
        </label>
      </div>

      <h4 style={{ marginTop: 0 }}>
        {isZipMode ? 'Upload Zip Archive' : 'Upload Single File'} 
        {currentFolderId && <span style={{fontSize: '0.8em', color: '#aaa', marginLeft: '10px'}}>(inside active folder)</span>}
      </h4>
      
      <form onSubmit={handleUpload} style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
        <input 
          id="fileInput"
          type="file" 
          onChange={handleFileChange} 
          accept={isZipMode ? ".zip" : "*"} 
          style={{ color: '#ccc' }}
        />
        <button 
          type="submit" 
          disabled={!selectedFile || uploading}
          style={{ 
            padding: '10px 20px', 
            cursor: 'pointer',
            backgroundColor: uploading ? '#555' : (isZipMode ? '#9C27B0' : '#2196F3'),
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 'bold'
          }}
        >
          {uploading ? 'Uploading...' : (isZipMode ? 'Upload Zip' : 'Upload ')}
        </button>
      </form>

      {message && <p style={{ marginTop: '15px', fontWeight: 'bold', color: message.startsWith('✅') ? '#4CAF50' : '#f44336' }}>{message}</p>}
    </div>
  );
}

export default FileUpload;
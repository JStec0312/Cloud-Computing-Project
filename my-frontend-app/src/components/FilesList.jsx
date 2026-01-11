import { useState, useEffect } from 'react';
import { domain_name } from '../config'
const formatBytes = (bytes, decimals = 2) => {
  if (!+bytes) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function FilesList({ currentFolderId, onNavigate }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [currentFolderName, setCurrentFolderName] = useState('Root');
  const [folderHistory, setFolderHistory] = useState([]); 

  const [activeVersionFileId, setActiveVersionFileId] = useState(null);  
  const [fileVersions, setFileVersions] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  const fetchFiles = async () => {
    setLoading(true);
    setActiveVersionFileId(null); 
    try {
      const token = localStorage.getItem('token');
      let url = `${domain_name}/files`;
      if (currentFolderId) {
        url += `?folder_id=${currentFolderId}`;
      }

      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',

        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      console.log("Fetch response:", response);

      if (!response.ok) throw new Error(`Error ${response.status}: ${await response.text()}`);
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setFiles(data);
      } else if (data.items && Array.isArray(data.items)) {
        setFiles(data.items);
      } else {
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
  }, [currentFolderId]); 

  const handleToggleVersions = async (fileId) => {
    if (activeVersionFileId === fileId) {
      setActiveVersionFileId(null);
      setFileVersions([]);
      return;
    }

    setLoadingVersions(true);
    setActiveVersionFileId(fileId);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${domain_name}/files/${fileId}/versions`, {
        credentials: 'include',
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error("Failed to fetch versions");

      const data = await response.json();
      const versionsList = Array.isArray(data) ? data : (data.items || []);
      setFileVersions(versionsList);

    } catch (err) {
      alert(`Error fetching versions: ${err.message}`);
      setActiveVersionFileId(null);
    } finally {
      setLoadingVersions(false);
    }
  };

  const handleDownloadVersion = async (fileId, versionId, fileName) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${domain_name}/files/${fileId}/versions/${versionId}/download`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `v${versionId.substring(0,4)}_${fileName}`; 
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

    } catch (err) {
      alert(`Error downloading version: ${err.message}`);
    }
  };

  const handleEnterFolder = (folderId, folderName) => {
    setFolderHistory(prev => [...prev, { id: currentFolderId, name: currentFolderName }]);
    setCurrentFolderName(folderName);
    onNavigate(folderId); 
  };

  const handleGoUp = () => {
    if (folderHistory.length === 0) {
      onNavigate(null);
      setCurrentFolderName('Root');
      return;
    }
    const previous = folderHistory[folderHistory.length - 1];
    setFolderHistory(prev => prev.slice(0, -1));
    setCurrentFolderName(previous.name);
    onNavigate(previous.id); 
  };

  const handleRename = async (fileId, currentName) => {
    const newName = prompt("Enter new name:", currentName);
    if (!newName || newName === currentName) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${domain_name}/files/${fileId}/rename`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_name: newName }) 
      });
      if (!response.ok) throw new Error(await response.text());
      fetchFiles(); 
    } catch (err) { alert(`Error renaming: ${err.message}`); }
  };

  const handleDownload = async (fileId, fileName) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${domain_name}/files/${fileId}/download`, {
        credentials: 'include',
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error("Download failed");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) { alert(`Error downloading: ${err.message}`); }
  };

  const handleDelete = async (fileId) => {
    if (!confirm("Are you sure you want to delete this item?")) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${domain_name}/files/${fileId}`, {
        credentials: 'include',
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error("Delete failed");
      fetchFiles();
    } catch (err) { alert(`Error deleting: ${err.message}`); }
  };

  const getIcon = (file) => {
    if (file.is_folder) return '📁';
    if (file.name?.endsWith('.zip')) return '📦';
    if (file.name?.endsWith('.jpg') || file.name?.endsWith('.png')) return '🖼️';
    return '📄';
  };

  if (loading) return <p style={{color: '#888'}}>Loading...</p>;
  if (error) return <p style={{color: 'red'}}>Error: {error}</p>;

  return (
    <div style={{ marginTop: '20px', color: 'white' }}> 
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
        <h3>{currentFolderId ? `${currentFolderName}` : 'Root'}</h3>
        {currentFolderId && (
          <button 
            onClick={handleGoUp}
            style={{ cursor: 'pointer', background: '#555', border: 'none', color: 'white', borderRadius: '4px', padding: '5px 10px' }}
          >
            ⬆️ Go Up
          </button>
        )}
      </div>

      {files.length === 0 ? (
        <div style={{ padding: '20px', border: '1px dashed #555', borderRadius: '8px', color: '#aaa' }}>
          <p>Empty folder.</p>
        </div>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {files.map((file) => {
            const isFolder = file.is_folder;
            const displayName = file.name || file.filename || file.folder_name;
            const isExpanded = activeVersionFileId === file.id;

            return (
              <li key={file.id} style={{ 
                borderBottom: '1px solid #333',
                backgroundColor: isFolder ? '#2a2a2a' : 'transparent',
                borderRadius: '4px',
                marginBottom: '5px',
                padding: '10px'
              }}>
                {/* --- MAIN ROW --- */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div 
                    onClick={() => isFolder ? handleEnterFolder(file.id, displayName) : null}
                    style={{ 
                      flex: 1, 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '10px',
                      cursor: isFolder ? 'pointer' : 'default' 
                    }}
                  >
                    <span style={{ fontSize: '1.5em' }}>{getIcon(file)}</span>
                    <span style={{ 
                      fontWeight: isFolder ? 'bold' : 'normal',
                      color: isFolder ? '#ffcc80' : 'white',
                      textDecoration: isFolder ? 'underline' : 'none',
                      textDecorationColor: '#555'
                    }}>
                      {displayName}
                    </span>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {/* NEW: Version Button (Only for files) */}
                    {!isFolder && (
                      <button 
                        onClick={() => handleToggleVersions(file.id)}
                        title="View Versions"
                        style={{ cursor: 'pointer', background: isExpanded ? '#FF9800' : 'none', border: '1px solid #555', color: isExpanded ? 'white' : '#ddd', borderRadius: '4px', padding: '5px 10px' }}
                      >
                        View Versions
                      </button>
                    )}

                    <button onClick={() => handleRename(file.id, displayName)} title="Rename">Rename</button>
                    {!isFolder && (
                      <button onClick={() => handleDownload(file.id, displayName)} title="Download">Download</button>
                    )}
                    <button onClick={() => handleDelete(file.id)} title="Delete" style={{ background: '#d32f2f', border: 'none', color: 'white' }}>Delete</button>
                  </div>
                </div>

                {/* --- VERSIONS SUB-LIST --- */}
                {isExpanded && (
                  <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#222', borderRadius: '4px', borderLeft: '3px solid #FF9800' }}>
                    <h5 style={{ margin: '0 0 10px 0', color: '#ccc' }}>History for "{displayName}"</h5>
                    
                    {loadingVersions ? (
                      <p style={{ fontSize: '0.9em', color: '#888' }}>Loading versions...</p>
                    ) : fileVersions.length === 0 ? (
                      <p style={{ fontSize: '0.9em', color: '#888' }}>No history found.</p>
                    ) : (
                      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                        {fileVersions.map((ver) => (
                          <li key={ver.id} style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center',
                            padding: '5px 0',
                            borderBottom: '1px dashed #444',
                            fontSize: '0.9em',
                            color: '#aaa'
                          }}>
                            <span>
                              {/* Use version_no, uploaded_at, and size_bytes */}
v{ver.version_no} - {new Date(ver.uploaded_at).toLocaleString()} 
<span style={{marginLeft: '10px', fontSize: '0.85em'}}>
  ({formatBytes(ver.size_bytes)})
</span>
                            </span>
                            <button 
                              onClick={() => handleDownloadVersion(file.id, ver.id, displayName)}
                              style={{ cursor: 'pointer', background: 'none', border: '1px solid #555', color: '#4CAF50', borderRadius: '4px', padding: '2px 8px', fontSize: '0.85em' }}
                            >
                              Restore
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default FilesList;
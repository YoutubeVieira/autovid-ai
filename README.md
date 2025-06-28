import React, { useState } from 'react';

export default function AutoVidCreator() {
  const [script, setScript] = useState('');
  const [voice, setVoice] = useState('female');
  const [isGenerating, setIsGenerating] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);

  const handleGenerate = () => {
    if (!script.trim()) {
      alert('Veuillez entrer un script.');
      return;
    }
    setIsGenerating(true);

    // Simulation de génération (à remplacer par appel API réel)
    setTimeout(() => {
      // Ici, on simule une URL vidéo créée
      setVideoUrl('https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4');
      setIsGenerating(false);
    }, 3000);
  };

  return (
    <div style={{ maxWidth: 700, margin: '2rem auto', fontFamily: 'Arial, sans-serif' }}>
      <h1>AutoVid AI - Création de vidéo</h1>

      <label>
        Script (texte) :
        <textarea
          rows={6}
          style={{ width: '100%', fontSize: 16, marginTop: 8 }}
          value={script}
          onChange={(e) => setScript(e.target.value)}
          placeholder="Entrez votre script ici..."
        />
      </label>

      <label style={{ display: 'block', marginTop: 16 }}>
        Choix de la voix :
        <select value={voice} onChange={(e) => setVoice(e.target.value)} style={{ marginLeft: 10, fontSize: 16 }}>
          <option value="female">Femme</option>
          <option value="male">Homme</option>
        </select>
      </label>

      <button
        onClick={handleGenerate}
        disabled={isGenerating}
        style={{
          marginTop: 20,
          padding: '10px 20px',
          fontSize: 18,
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer',
          opacity: isGenerating ? 0.6 : 1,
        }}
      >
        {isGenerating ? 'Génération en cours...' : 'Générer la vidéo'}
      </button>

      {videoUrl && (
        <div style={{ marginTop: 30 }}>
          <h2>Prévisualisation vidéo</h2>
          <video
            src={videoUrl}
            controls
            width="100%"
            style={{ borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.3)' }}
          />
        </div>
      )}
    </div>
  );
}

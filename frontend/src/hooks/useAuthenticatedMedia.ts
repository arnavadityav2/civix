import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export function useAuthenticatedMedia(artifactId?: string | null) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    if (!artifactId) {
      setObjectUrl(null);
      setLoading(false);
      setError(false);
      return;
    }

    let isMounted = true;
    let createdUrl: string | null = null;
    setLoading(true);
    setError(false);

    apiClient
      .get(`/evidence/artifacts/${artifactId}/content`, { responseType: 'blob' })
      .then((res) => {
        if (!isMounted) return;
        const contentType = res.headers['content-type'] || 'application/octet-stream';
        const blob = new Blob([res.data], { type: contentType });
        createdUrl = URL.createObjectURL(blob);
        setObjectUrl(createdUrl);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error(`Failed to load authenticated evidence blob for ${artifactId}:`, err);
        setError(true);
        setLoading(false);
      });

    return () => {
      isMounted = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [artifactId]);

  return { objectUrl, loading, error };
}

export async function downloadAuthenticatedEvidence(artifactId: string, fallbackFilename: string) {
  try {
    const res = await apiClient.get(`/evidence/artifacts/${artifactId}/content`, {
      responseType: 'blob',
    });

    const contentDisposition = res.headers['content-disposition'];
    let filename = fallbackFilename;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename\*?=['"]?(?:UTF-8'')?([^;'"\n]+)['"]?/i);
      if (match && match[1]) {
        filename = decodeURIComponent(match[1]);
      }
    }

    const contentType = res.headers['content-type'] || 'application/octet-stream';
    const blob = new Blob([res.data], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (err) {
    console.error(`Failed to download evidence artifact ${artifactId}:`, err);
    alert('Failed to download evidence file from vault.');
  }
}

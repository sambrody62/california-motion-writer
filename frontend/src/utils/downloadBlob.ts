// Trigger a browser download for an in-memory buffer
export function downloadBlob(buffer: ArrayBuffer, mimeType: string, filename: string): void {
  const blob = new Blob([buffer], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

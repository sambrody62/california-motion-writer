/** Returns true only when REACT_APP_GMAIL_ENABLED is exactly "true". Default off. */
export function gmailEnabled(): boolean {
  return process.env.REACT_APP_GMAIL_ENABLED === 'true';
}

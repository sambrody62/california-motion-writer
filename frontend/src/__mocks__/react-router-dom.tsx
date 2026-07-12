import React from 'react';

export const BrowserRouter = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
export const Router = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
export const Routes = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
export const Route = ({ element }: { element: React.ReactNode }) => <div>{element}</div>;
export const Link = ({ children, to }: { children: React.ReactNode; to: string }) => <a href={to}>{children}</a>;
export const Navigate = ({ to }: { to: string }) => <div>Navigate to {to}</div>;
export const useNavigate = () => jest.fn();
export const useLocation = () => ({ pathname: '/', search: '', hash: '', state: null });
export const useParams = () => ({});
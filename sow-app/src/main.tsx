import {StrictMode} from 'react'
import {createRoot} from 'react-dom/client'
import {AuthProvider} from "react-oidc-context";
import './style.css'
import App from './App.tsx'

const oidcConfig = {
    authority: `${import.meta.env.VITE_KEYCLOAK_URL}/realms/${import.meta.env.VITE_KEYCLOAK_REALM}`,
    client_id: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
    redirect_uri: `${window.location.origin}/`,
}

createRoot(document.getElementById('root')!).render(
    <AuthProvider {...oidcConfig}>
        <StrictMode>
            <div
                className="text-zinc-950 antialiased lg:bg-zinc-100 dark:bg-zinc-900 dark:text-white dark:lg:bg-zinc-950">
                <App/>
            </div>
        </StrictMode>
    </AuthProvider>
)

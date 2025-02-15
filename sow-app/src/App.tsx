import {useState, useEffect} from 'react';
import Keycloak from 'keycloak-js';

function App() {
    const [keycloak, setKeycloak] = useState<Keycloak | null>(null);
    const [authenticated, setAuthenticated] = useState(false);

    useEffect(() => {
        const keycloakInstance = new Keycloak({
            url: import.meta.env.VITE_KEYCLOAK_URL,
            realm: import.meta.env.VITE_KEYCLOAK_REALM,
            clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
        });

        keycloakInstance.init({onLoad: 'login-required'}) // 'login-required' or 'check-sso'
            .then(authenticated => {
                setKeycloak(keycloakInstance);
                setAuthenticated(authenticated);

                if (authenticated) {
                    console.log('User is authenticated');
                    // You can access the user's token: keycloakInstance.token
                    console.log(keycloakInstance.token);
                } else {
                    console.log('User is not authenticated');
                }
            })
            .catch(err => {
                console.error("Keycloak initialization failed:", err);
            });
    }, []);

    const handleLogin = () => {
        keycloak?.login();
    }

    const handleLogout = () => {
        keycloak?.logout();
    }

    if (!keycloak) {
        return <div
            className="flex justify-center items-center h-screen pt-20 text-xl font-bold underline">Loading...</div>;
    }

    return (
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
            <h1>Stunning Octo Waffel 🧇</h1>
            {authenticated ? (
                <div>
                    <p className="text-sm/6 text-gray-500">User is authenticated!</p>
                    <button
                        type="button"
                        className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        onClick={handleLogout}>Logout
                    </button>
                    <div
                        className="overflow-hidden rounded-lg pb-12 outline outline-1 -outline-offset-1 outline-gray-300 focus-within:outline focus-within:outline-2 focus-within:-outline-offset-2 focus-within:outline-indigo-600">
                        <label htmlFor="token" className="sr-only">
                            Token
                        </label>
                        <textarea
                            id="token"
                            name="token"
                            rows={5}
                            readOnly={true}
                            className="block w-full resize-none bg-transparent px-3 py-1.5 text-base text-gray-900 placeholder:text-gray-400 focus:outline focus:outline-0 sm:text-sm/6"
                            defaultValue={keycloak.token}
                        />
                    </div>
                </div>
            ) : (
                <div>
                    <p className="text-sm/6 text-gray-500">User is not authenticated.</p>
                    <button
                        type="button"
                        className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        onClick={handleLogin}
                    >
                        Login
                    </button>
                </div>

            )}
        </div>
    );
}

export default App;
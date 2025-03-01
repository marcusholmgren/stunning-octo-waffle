import {useState} from 'react';
import {useAuth} from "react-oidc-context";
import {Textarea} from './components/textarea';
import {Input} from './components/input'
import {Field, Label} from './components/fieldset'
import {Button} from './components/button';
import {Heading} from "./components/heading.tsx";

type Review = {
    restaurant: string;
    review: string;
}

function App() {
    const auth = useAuth();
    const [review, setReview] = useState<Review>({restaurant: '', review: ''});

    switch (auth.activeNavigator) {
        case "signinSilent":
            return <div>Signing you in...</div>;
        case "signoutRedirect":
            return <div>Signing you out...</div>;
    }


    if (auth.error) {
        return <div>Oops... {auth.error.message}</div>;
    }

    const handleLogin = () => {
        auth.signinRedirect();
    }

    const handleLogout = () => {
        auth.signoutRedirect();
    }

    // @ts-ignore
    const handleSubmit = async (event) => {
        event.preventDefault();

        if (!auth.isAuthenticated) {
            console.error("Not authenticated or no token available.");
            return;
        }

        try {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/waffle/reviews`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.user?.access_token}`
                },
                body: JSON.stringify(review)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Review submitted successfully:", data);
            alert("Review submitted! Response: " + JSON.stringify(data));
            setReview({restaurant: '', review: ''});
        } catch (error) {
            console.error("Error submitting review:", error);
            alert("Error submitting review: " + error);
        }
    };

    // @ts-ignore
    const handleChange = (event) => {
        const {name, value} = event.target;
        setReview(prevReview => ({...prevReview, [name]: value}));
    };

    if (auth.isLoading) {
        return <div className="p-5 h-screen"><Heading>Loading...</Heading></div>;
    }


    return (
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 h-screen">
            <Heading>Stunning Octo Waffel 🧇</Heading>
            {auth.isAuthenticated ? (
                <div>
                    <p className="text-sm/6 text-gray-500">User {auth.user?.profile.name} is authenticated!</p>
                    <ReviewForm review={review} handleSubmit={handleSubmit} handleChange={handleChange}/>
                    <Button
                        type="button"
                        color="indigo"
                        onClick={handleLogout}>Logout
                    </Button>
                    <Field>
                        <Label htmlFor="token" className="sr-only">
                            Token
                        </Label>
                        <Textarea
                            id="token"
                            name="token"
                            rows={14}
                            readOnly={true}
                            defaultValue={auth.user?.access_token}
                        />
                    </Field>
                </div>
            ) : (
                <div>
                    <p className="text-sm/6 text-gray-500">User is not authenticated.</p>
                    <Button
                        type="button" color="indigo"
                        onClick={handleLogin}>
                        Login
                    </Button>
                </div>

            )}
        </div>
    );
}

interface ReviewFormProps {
    review: Review;
    handleSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
    handleChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
}

function ReviewForm({review, handleSubmit, handleChange}: ReviewFormProps) {
    return (
        <form onSubmit={handleSubmit}>
            <Field>
                <Label>
                    Restaurant:
                    <Input type="text" name="restaurant" value={review.restaurant} onChange={handleChange} required/>
                </Label>
            </Field>
            <br/>
            <Field>
                <Label>
                    Review:
                    <Textarea name="review" value={review.review} onChange={handleChange} required/>
                </Label>
            </Field>
            <br/>
            <div className="flex justify-end gap-4">
                <Button type="reset" plain>
                    Reset
                </Button>
                <Button type="submit">Save changes</Button>
            </div>
        </form>
    )
}

export default App;
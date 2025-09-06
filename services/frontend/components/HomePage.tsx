"use client";

import { useSession } from 'next-auth/react';
import { LoadingSpinner } from './ui/LoadingSpinner';
import { LoggedInDashboard } from './dashboard/LoggedInDashboard';
import { LandingPage } from './landing/LandingPage';

export default function HomePage() {
    const { data: session, status } = useSession();

    if (status === "loading") {
        return <LoadingSpinner />;
    }

    return session ? <LoggedInDashboard /> : <LandingPage />;
}
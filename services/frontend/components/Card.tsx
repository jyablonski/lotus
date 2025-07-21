// components/Card.tsx
import React, { ReactNode } from 'react';

interface CardProps {
    children: ReactNode; // Accept any child components
}

const Card: React.FC<CardProps> = ({ children }) => {
    return (
        <div className="max-w-xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-md">
            {children}
        </div>
    );
};

export default Card;

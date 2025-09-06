// components/AboutCard.tsx
import React from 'react';
import Card from './Card'; // Import the Card component

const AboutCard: React.FC = () => {
    return (
        <Card>
            <h1 className="text-2xl font-bold mb-6 text-center">Lotus</h1>
            <p className="text-gray-600 mb-2">
                Lotus is a simple journaling app designed to help you track your thoughts, reflections, and progress over time.
            </p>
            <br />
            <p className="text-gray-600">
                Your entries stay secure and organized so you can focus on writing, not managing files or syncing across devices.
            </p>
        </Card>
    );
};

export default AboutCard;

import Link from 'next/link';
import { Lightbulb, Target, Rocket } from 'lucide-react';
import { Card } from '@/components/ui/Card';

export const LandingPage = () => {
    const features = [
        {
            title: 'Intelligent Analysis',
            description: 'AI-powered insights help you understand your thoughts, mood patterns, and topics over time.',
            icon: <Lightbulb size={32} className="text-yellow-500" />,
        },
        {
            title: 'Secure & Private',
            description: 'Your thoughts are yours alone. We use industry-standard security to keep your entries safe.',
            icon: <Target size={32} className="text-green-500" />,
        },
        {
            title: 'Seamless Experience',
            description: 'Write naturally with our clean interface, then discover insights about your journey.',
            icon: <Rocket size={32} className="text-blue-500" />,
        },
    ];

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">

            {/* Hero Section */}
            <div className="text-center space-y-6">
                <h1 className="text-5xl font-bold text-gray-900">
                    Your thoughts, <span className="text-blue-600">organized and understood</span>
                </h1>
                <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                    Lotus combines the simplicity of journaling with the power of AI to help you understand your patterns,
                    track your growth, and reflect on your journey.
                </p>
                <div className="flex justify-center">
                    <Link href="/api/auth/signin">
                        <button className="bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors">
                            Start Your Journey
                        </button>
                    </Link>
                </div>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {features.map((feature) => (
                    <Card key={feature.title} className="p-8 text-center">
                        <div className="flex justify-center mb-4">
                            {feature.icon}
                        </div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                        <p className="text-gray-600">{feature.description}</p>
                    </Card>
                ))}
            </div>

            {/* Sample Preview */}
            <div className="bg-gray-50 rounded-2xl p-8">
                <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">See Your Insights Come to Life</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <Card className="p-6">
                        <h3 className="font-semibold text-gray-900 mb-4">Sample Journal Entry</h3>
                        <div className="bg-gray-100 p-4 rounded-lg">
                            <p className="text-gray-600 italic blur-sm">
                                Today was challenging but rewarding. The project deadline is approaching and I felt stressed,
                                but the team really came together...
                            </p>
                        </div>
                    </Card>
                    <Card className="p-6">
                        <h3 className="font-semibold text-gray-900 mb-4">AI Analysis</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Sentiment:</span>
                                <span className="text-green-600 font-medium">Positive</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Topics:</span>
                                <span className="text-blue-600 font-medium">Work, Team, Growth</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Mood:</span>
                                <span className="text-purple-600 font-medium">Optimistic</span>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>

            {/* Bottom CTA */}
            <div className="text-center">
                <Link href="/api/auth/signin">
                    <button className="bg-gray-900 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-800 transition-colors">
                        Sign in with GitHub
                    </button>
                </Link>
            </div>
        </div>
    );
};
import React from "react";
import Link from "next/link";
import {
  Heart,
  Shield,
  Calendar,
  TrendingUp,
  Pen,
  Lightbulb,
} from "lucide-react";

const LandingPage = () => {
  const features = [
    {
      icon: <Pen className="w-6 h-6" />,
      title: "Simple Writing",
      description:
        "Clean, distraction-free interface designed to help you focus on your thoughts and reflections.",
    },
    {
      icon: <Calendar className="w-6 h-6" />,
      title: "Daily Tracking",
      description:
        "Build a consistent journaling habit with streak tracking and calendar visualization.",
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Mood Insights",
      description:
        "Track your emotional patterns and gain insights into your mental wellness journey.",
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Private & Secure",
      description:
        "Your thoughts are precious. All entries are securely stored and completely private.",
    },
  ];

  return (
    <div className="page-container">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="content-container py-20">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-lotus-gradient rounded-2xl mb-8 shadow-lg">
              <Heart className="w-10 h-10 text-white" />
            </div>
            <h1 className="heading-1 mb-6">
              Your thoughts,{" "}
              <span className="text-gradient">organized and understood</span>
            </h1>
            <p className="text-xl text-muted-dark max-w-3xl mx-auto leading-relaxed mb-8">
              Lotus combines the simplicity of journaling with the power of
              insights to help you understand your patterns, track your growth,
              and reflect on your journey.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/api/auth/signin">
                <button className="btn-primary">Start Your Journey</button>
              </Link>
              <Link href="#features">
                <button className="btn-secondary">Learn More</button>
              </Link>
            </div>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-20 left-10 w-20 h-20 bg-lotus-400 rounded-full opacity-30 animate-pulse-slow"></div>
        <div className="absolute bottom-20 right-10 w-32 h-32 bg-rose-400 rounded-full opacity-20 animate-float"></div>
      </div>

      {/* Features Section */}
      <div id="features" className="content-container py-16">
        <div className="text-center mb-16">
          <h2 className="heading-2 mb-4">Why Choose Lotus?</h2>
          <p className="text-muted-dark max-w-2xl mx-auto">
            We&apos;ve crafted every detail to make journaling a delightful and
            meaningful part of your daily routine.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card-hover p-6">
              <div className="w-12 h-12 bg-lotus-gradient rounded-xl flex items-center justify-center text-white mb-4">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold text-primary-dark mb-3">
                {feature.title}
              </h3>
              <p className="text-muted-dark leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Sample Preview Section */}
      <div className="bg-lotus-subtle py-16">
        <div className="content-container">
          <h2 className="heading-2 text-center mb-8">
            See Your Insights Come to Life
          </h2>
          <div className="grid lg:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="card p-6">
              <h3 className="font-semibold text-primary-dark mb-4 flex items-center">
                <Pen className="w-5 h-5 mr-2 text-lotus-400" />
                Sample Journal Entry
              </h3>
              <div className="bg-lotus-light p-4 rounded-lg">
                <p className="text-secondary-dark italic">
                  &quot;Today was challenging but rewarding. The project
                  deadline is approaching and I felt stressed, but the team
                  really came together. I&apos;m grateful for their support and
                  feel optimistic about tomorrow...&quot;
                </p>
              </div>
            </div>
            <div className="card p-6">
              <h3 className="font-semibold text-primary-dark mb-4 flex items-center">
                <Lightbulb className="w-5 h-5 mr-2 text-lotus-400" />
                Your Insights
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-dark">Sentiment:</span>
                  <span className="badge badge-success">Positive</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-dark">Topics:</span>
                  <span className="badge badge-lotus">Work, Team, Growth</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-dark">Mood:</span>
                  <div className="flex items-center">
                    <div className="mood-indicator mood-positive mr-2"></div>
                    <span className="text-secondary-dark font-medium">
                      Optimistic
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}

      {/* Footer */}
      <div className="bg-dark-950 text-white py-8">
        <div className="content-container text-center">
          <div className="text-dark-400 text-sm">© 2026 Lotus</div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;

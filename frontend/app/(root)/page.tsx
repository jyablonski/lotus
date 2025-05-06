import Link from 'next/link';
import { Rocket, Lightbulb, Cloud } from 'lucide-react'; // Example Lucide icons

const features = [
  {
    title: 'Powerful Features',
    description: 'Experience a suite of tools designed to boost your productivity and streamline your workflow.',
    icon: <Rocket size={32} color="#4F46E5" />,
  },
  {
    title: 'Intuitive Interface',
    description: 'Enjoy a clean and user-friendly design that makes navigation and interaction a breeze.',
    icon: <Lightbulb size={32} color="#10B981" />,
  },
  {
    title: 'Seamless Integration',
    description: 'Connect with your favorite apps and services for a cohesive and efficient experience.',
    icon: <Cloud size={32} color="#F59E0B" />,
  },
];

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((feature) => (
          <div key={feature.title} className="bg-gray-100 rounded-lg p-6 shadow-md hover:shadow-lg transition duration-300">
            <div className="flex items-center mb-4">
              <div className="mr-4">{feature.icon}</div> {/* Render the Lucide icon component */}
              <h3 className="text-xl font-semibold text-gray-800">{feature.title}</h3>
            </div>
            <p className="text-gray-600">{feature.description}</p>
          </div>
        ))}
      </div>
      <div className="mt-12 text-center">
        <Link href="/signup" className="bg-green-500 hover:bg-green-700 text-white font-bold py-4 px-8 rounded-full transition duration-300">
          Get Started Today
        </Link>
      </div>
    </div>
  );
}
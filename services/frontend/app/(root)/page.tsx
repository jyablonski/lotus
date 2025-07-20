import Link from 'next/link';
import { Rocket, Lightbulb, Cloud, BookOpen, User, PlusCircle, Info } from 'lucide-react';

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

const quickLinks = [
  {
    title: 'About',
    href: '/about',
    icon: <Info size={20} className="text-blue-600" />,
  },
  {
    title: 'Create Journal Entry',
    href: '/journal/create',
    icon: <PlusCircle size={20} className="text-green-600" />,
  },
  {
    title: 'View Journal History',
    href: '/journal/home',
    icon: <BookOpen size={20} className="text-purple-600" />,
  },
  {
    title: 'Profile',
    href: '/profile',
    icon: <User size={20} className="text-gray-700" />,
  },
];

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">

      {/* Features Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((feature) => (
          <div key={feature.title} className="bg-gray-100 rounded-lg p-6 shadow-md hover:shadow-lg transition duration-300">
            <div className="flex items-center mb-4">
              <div className="mr-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-gray-800">{feature.title}</h3>
            </div>
            <p className="text-gray-600">{feature.description}</p>
          </div>
        ))}
      </div>

      {/* Quick Links Section */}
      <div>
        <h2 className="text-2xl font-bold mb-6 text-gray-800">Quick Links</h2>
        <ul className="space-y-4">
          {quickLinks.map((link) => (
            <li key={link.href}>
              <Link href={link.href} className="flex items-center text-blue-700 hover:underline">
                <span className="mr-2">{link.icon}</span>
                {link.title}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

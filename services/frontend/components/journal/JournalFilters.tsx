import { Search, Filter } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';

interface MoodOption {
    key: string;
    label: string;
    emoji: string;
}

interface JournalFiltersProps {
    searchTerm: string;
    setSearchTerm: (term: string) => void;
    selectedMood: string;
    setSelectedMood: (mood: string) => void;
    uniqueMoods: MoodOption[];
    totalEntries: number;
    filteredCount: number;
    onClearFilters?: () => void; // Optional custom clear function
}

export function JournalFilters({
    searchTerm,
    setSearchTerm,
    selectedMood,
    setSelectedMood,
    uniqueMoods,
    totalEntries,
    filteredCount,
    onClearFilters
}: JournalFiltersProps) {
    const hasActiveFilters = searchTerm || selectedMood !== 'all';

    const handleClearFilters = () => {
        if (onClearFilters) {
            // Use custom clear function if provided (for pagination integration)
            onClearFilters();
        } else {
            // Default behavior
            setSearchTerm('');
            setSelectedMood('all');
        }
    };

    return (
        <Card className="mb-6">
            <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row gap-4">
                    {/* Search */}
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                        <input
                            type="text"
                            placeholder="Search your entries..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>

                    {/* Mood Filter */}
                    <div className="sm:w-48">
                        <div className="relative">
                            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                            <select
                                value={selectedMood}
                                onChange={(e) => setSelectedMood(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
                            >
                                <option value="all">All Moods</option>
                                {uniqueMoods.map((mood) => (
                                    <option key={mood.key} value={mood.key}>
                                        {mood.emoji} {mood.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Filter summary */}
                {hasActiveFilters && (
                    <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
                        <span>Showing {filteredCount} of {totalEntries} entries</span>
                        {searchTerm && (
                            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                Text: {searchTerm}
                            </span>
                        )}
                        {selectedMood !== 'all' && (
                            <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                                Mood: {uniqueMoods.find(m => m.key === selectedMood)?.label || selectedMood}
                            </span>
                        )}
                        <button
                            onClick={handleClearFilters}
                            className="text-blue-600 hover:text-blue-800 ml-2"
                        >
                            Clear filters
                        </button>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
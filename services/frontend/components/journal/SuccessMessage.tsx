import { CheckCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';

export function SuccessMessage() {
    return (
        <Card className="border-green-200 bg-green-50">
            <CardContent className="p-6 text-center">
                <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
                <h3 className="text-lg font-medium text-green-900 mb-2">
                    Entry Saved Successfully!
                </h3>
                <p className="text-green-700">
                    Your journal entry has been saved. Redirecting you back to your journal...
                </p>
            </CardContent>
        </Card>
    );
}
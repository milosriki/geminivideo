import React from 'react';

export const LoadingScreen: React.FC = () => {
    return (
        <div className="flex items-center justify-center h-screen bg-zinc-950 text-white">
            <div className="flex flex-col items-center gap-4">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
                <p className="text-gray-400 animate-pulse">Loading Gemini Video...</p>
            </div>
        </div>
    );
};

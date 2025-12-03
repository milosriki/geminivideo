import React, { useState, useRef, useEffect } from 'react';

interface Board {
  id: string;
  name: string;
  count?: number;
}

interface BoardSelectorProps {
  boards: Board[];
  selectedBoardId: string | null;
  onSelectBoard: (boardId: string) => void;
  onCreateBoard?: () => void;
}

const ChevronDownIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <polyline points="6 9 12 15 18 9"></polyline>
  </svg>
);

const CheckIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const PlusIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

const SearchIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="11" cy="11" r="8"></circle>
    <path d="m21 21-4.35-4.35"></path>
  </svg>
);

const FolderIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
  </svg>
);

export const BoardSelector: React.FC<BoardSelectorProps> = ({
  boards,
  selectedBoardId,
  onSelectBoard,
  onCreateBoard,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedBoard = boards.find((b) => b.id === selectedBoardId);

  const filteredBoards = boards.filter((board) =>
    board.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSelectBoard = (boardId: string) => {
    onSelectBoard(boardId);
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleCreateBoard = () => {
    if (onCreateBoard) {
      onCreateBoard();
    }
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors"
      >
        <FolderIcon className="w-4 h-4" />
        <span>{selectedBoard ? selectedBoard.name : 'Select Board'}</span>
        <ChevronDownIcon
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-72 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50 overflow-hidden">
          {/* Search Input */}
          <div className="p-3 border-b border-zinc-800">
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="text"
                placeholder="Search boards..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          </div>

          {/* Boards List */}
          <div className="max-h-64 overflow-y-auto">
            {filteredBoards.length > 0 ? (
              <div className="py-1">
                {filteredBoards.map((board) => (
                  <button
                    key={board.id}
                    onClick={() => handleSelectBoard(board.id)}
                    className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-zinc-800 transition-colors text-left"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <FolderIcon className="w-4 h-4 text-zinc-500" />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-white">{board.name}</div>
                        {board.count !== undefined && (
                          <div className="text-xs text-zinc-500">{board.count} ads</div>
                        )}
                      </div>
                    </div>
                    {selectedBoardId === board.id && (
                      <CheckIcon className="w-4 h-4 text-indigo-500" />
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-sm text-zinc-500">
                No boards found
              </div>
            )}
          </div>

          {/* Create New Board Button */}
          {onCreateBoard && (
            <div className="border-t border-zinc-800 p-2">
              <button
                onClick={handleCreateBoard}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-indigo-400 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <PlusIcon className="w-4 h-4" />
                Create New Board
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BoardSelector;

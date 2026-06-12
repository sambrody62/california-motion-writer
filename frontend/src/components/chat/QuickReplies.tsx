import React from 'react';

interface QuickRepliesProps {
  replies: string[];
  onReplyClick: (reply: string) => void;
}

const QuickReplies: React.FC<QuickRepliesProps> = ({ replies, onReplyClick }) => {
  return (
    <div className="px-4 pb-2">
      <div className="flex flex-wrap gap-2">
        {replies.map((reply, index) => (
          <button
            key={index}
            onClick={() => onReplyClick(reply)}
            className="px-3 py-1.5 text-sm bg-white border border-blue-600 text-blue-600 rounded-full hover:bg-blue-50 transition-colors"
          >
            {reply}
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickReplies;
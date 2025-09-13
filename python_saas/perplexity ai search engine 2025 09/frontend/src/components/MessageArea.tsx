import React from "react";

interface SearchInfo {
  stages: string[];
  query: string;
  urls: string[];
  error?: string;
}

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  type: string;
  isLoading?: boolean;
  searchInfo?: SearchInfo;
}

interface MessageAreaProps {
  messages: Message[];
}

export default function MessageArea({ messages }: MessageAreaProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-500 mt-20">
          <h2 className="text-xl mb-2">Welcome to Perplexity AI Search</h2>
          <p>Ask me anything and I'll search the web for you!</p>
        </div>
      )}
      
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.isUser ? "justify-end" : "justify-start"
          }`}
        >
          <div
            className={`max-w-3xl rounded-lg p-4 ${
              message.isUser
                ? "bg-blue-500 text-white"
                : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            }`}
          >
            {message.isUser ? (
              <p>{message.content}</p>
            ) : (
              <div>
                {message.isLoading && !message.content && (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    <span>Thinking...</span>
                  </div>
                )}
                
                {message.content && (
                  <div className="prose dark:prose-invert max-w-none">
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                )}
                
                {message.searchInfo && message.searchInfo.urls.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="font-semibold mb-2 text-sm text-gray-600 dark:text-gray-400">
                      Sources:
                    </h4>
                    <div className="space-y-1">
                      {message.searchInfo.urls.slice(0, 5).map((url, index) => (
                        <a
                          key={index}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-blue-600 dark:text-blue-400 hover:underline text-sm truncate"
                        >
                          {url}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

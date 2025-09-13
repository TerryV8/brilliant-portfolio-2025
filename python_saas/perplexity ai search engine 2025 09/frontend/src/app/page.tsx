"use client";
import React, { useState } from "react";
import Header from "@/components/Header";
import MessageArea from "@/components/MessageArea";
import InputBar from "@/components/InputBar";
import Footer from "@/components/Footer";

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

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [checkpointId, setCheckpointId] = useState<string | null>(null);

  const handleSubmit = async (userInput: string) => {
    if (!userInput.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: userInput,
      isUser: true,
      type: "user",
    };

    // Add AI loading message
    setMessages((prev) => [
      ...prev,
      userMessage,
      {
        id: (Date.now() + 1).toString(),
        content: "",
        isUser: false,
        type: "ai",
        isLoading: true,
        searchInfo: {
          stages: [],
          query: "",
          urls: [],
        },
      },
    ]);

    try {
      // Create URL with checkpoint ID if it exists
      let url = `https://perplexity-kyk3.onrender.com/chat_stream/${encodeURIComponent(
        userInput
      )}`;
      if (checkpointId) {
        url += `?checkpoint_id=${encodeURIComponent(checkpointId)}`;
      }

      // Connect to SSE endpoint using EventSource
      console.log("Connecting to SSE endpoint:", url);
      const eventSource = new EventSource(url);
      let streamedContent = "";
      let searchData: SearchInfo | null = null;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Received SSE data:", data);

          if (data.type === "content") {
            streamedContent += data.content;
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage && !lastMessage.isUser) {
                lastMessage.content = streamedContent;
                lastMessage.isLoading = false;
              }
              return newMessages;
            });
          } else if (data.type === "search_results") {
            searchData = {
              stages: ["Searching..."],
              query: userInput,
              urls: data.urls || [],
            };
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage && !lastMessage.isUser) {
                lastMessage.searchInfo = searchData;
              }
              return newMessages;
            });
          } else if (data.type === "done") {
            eventSource.close();
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage && !lastMessage.isUser) {
                lastMessage.isLoading = false;
              }
              return newMessages;
            });
          } else if (data.type === "error") {
            console.error("Error from server:", data.content);
            eventSource.close();
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage && !lastMessage.isUser) {
                lastMessage.content = `Error: ${data.content}`;
                lastMessage.isLoading = false;
              }
              return newMessages;
            });
          }
        } catch (error) {
          console.error("Error parsing SSE data:", error);
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE error:", error);
        eventSource.close();
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMessage = newMessages[newMessages.length - 1];
          if (lastMessage && !lastMessage.isUser) {
            lastMessage.content = "Error: Failed to get response. Please try again.";
            lastMessage.isLoading = false;
          }
          return newMessages;
        });
      };
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && !lastMessage.isUser) {
          lastMessage.content = "Error: Failed to get response. Please try again.";
          lastMessage.isLoading = false;
        }
        return newMessages;
      });
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-900">
      <Header />
      <MessageArea messages={messages} />
      <InputBar onSubmit={handleSubmit} />
      <Footer />
    </div>
  );
}

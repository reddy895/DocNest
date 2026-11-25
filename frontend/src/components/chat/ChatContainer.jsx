import React, { useEffect, useRef } from 'react';
import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';

export default function ChatContainer({
  messages = [],
  isLoading = false,
  currentStageKey = 'rewriting',
  onEditUserMessage,
  onRegenerate,
  onFeedback,
  onSaveNote,
  onCitationClick,
  onInspectSources,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="mx-auto w-full max-w-[800px] space-y-6 pb-8">
      {messages.map((msg, index) => {
        const isLast = index === messages.length - 1;
        if (msg.sender === 'user') {
          return (
            <UserMessage
              key={msg.id}
              message={msg}
              isStreaming={isLoading}
              onEditSubmit={onEditUserMessage}
            />
          );
        }
        return (
          <AssistantMessage
            key={msg.id}
            message={msg}
            isLast={isLast}
            isStreaming={isLoading}
            stageKey={currentStageKey}
            onRegenerate={onRegenerate}
            onFeedback={onFeedback}
            onSaveNote={onSaveNote}
            onCitationClick={onCitationClick}
            onInspectSources={onInspectSources}
          />
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}

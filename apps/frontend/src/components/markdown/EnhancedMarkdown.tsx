import React from "react";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import CodeBlock from "./CodeBlock";

interface EnhancedMarkdownProps {
  children: string;
}

export const EnhancedMarkdown: React.FC<EnhancedMarkdownProps> = ({
  children,
}) => {
  return (
    <div className="custom-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Heading styling
          h1: ({ node, ...props }) => (
            <h1 className="text-3xl font-bold mt-8 mb-4" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2
              className="text-2xl font-bold mt-6 mb-3 pb-2 border-b border-border"
              {...props}
            />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xl font-bold mt-5 mb-2" {...props} />
          ),
          h4: ({ node, ...props }) => (
            <h4 className="text-lg font-bold mt-4 mb-2" {...props} />
          ),

          // Paragraph styling
          p: ({ node, ...props }) => (
            <p className="my-3 leading-relaxed" {...props} />
          ),

          // List styling
          ul: ({ node, ...props }) => (
            <ul className="list-disc pl-6 my-4" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal pl-6 my-4" {...props} />
          ),
          li: ({ node, ...props }) => <li className="my-1" {...props} />,

          // Table styling
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-6">
              <table className="w-full border-collapse" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-muted" {...props} />
          ),
          tr: ({ node, ...props }) => (
            <tr className="border-b border-border" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th
              className="text-left p-3 font-bold text-foreground"
              {...props}
            />
          ),
          td: ({ node, ...props }) => <td className="p-3" {...props} />,

          // Code blocks - CSS will handle inline vs block styling
          code: ({ className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || "");
            return match ? (
              <CodeBlock className={className} children={children} {...props} />
            ) : (
              <code {...props}>{children}</code>
            );
          },

          // Link styling
          a: ({ node, ...props }) => (
            <a
              className="text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),

          // Blockquote styling
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-primary/30 pl-4 italic my-4"
              {...props}
            />
          ),

          // Horizontal rule
          hr: ({ node, ...props }) => (
            <hr className="my-6 border-border" {...props} />
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
};

export default EnhancedMarkdown;

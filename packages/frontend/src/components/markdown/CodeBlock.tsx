import { Highlight, Language, themes } from "prism-react-renderer";
import React, { ReactNode } from "react";

interface CodeBlockProps {
  children: ReactNode;
  className?: string;
  inline?: boolean;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  children,
  className,
  inline,
}) => {
  if (inline) {
    return (
      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    );
  }

  // Extract the language from the className (format: "language-xxx")
  const match = /language-(\w+)/.exec(className || "");
  // Default to typescript if no language is specified
  const lang = match ? match[1] : "typescript";

  // Convert to a valid Language type or fallback to typescript for unsupported languages
  const language = (
    [
      "jsx",
      "tsx",
      "typescript",
      "javascript",
      "css",
      "markup",
      "bash",
      "json",
    ].includes(lang)
      ? lang
      : "typescript"
  ) as Language;

  // Convert children to string for Highlight component
  const code = String(children || "").trim();

  return (
    <div className="rounded-md overflow-hidden my-4">
      <Highlight theme={themes.vsDark} code={code} language={language}>
        {({ className, style, tokens, getLineProps, getTokenProps }) => (
          <pre
            className={`${className} p-4 overflow-auto text-sm leading-relaxed`}
            style={{ ...style, backgroundColor: "rgb(30, 30, 30)" }}
          >
            {tokens.map((line, i) => (
              <div key={i} {...getLineProps({ line })}>
                <span className="text-gray-500 text-xs mr-4 select-none w-8 inline-block text-right">
                  {i + 1}
                </span>
                {line.map((token, key) => (
                  <span key={key} {...getTokenProps({ token })} />
                ))}
              </div>
            ))}
          </pre>
        )}
      </Highlight>
    </div>
  );
};

export default CodeBlock;

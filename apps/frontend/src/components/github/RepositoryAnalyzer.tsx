import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { GitBranch } from "lucide-react";
import { KeyboardEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { GithubTreeModal } from "./GithubTreeModal";

type AnalysisType = "fast" | "deep";

export function RepositoryAnalyzer() {
  const [inputUrl, setInputUrl] = useState<string>("");
  const [analysisType, setAnalysisType] = useState<AnalysisType>("fast");
  const [showTreeModal, setShowTreeModal] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleAnalyze = () => {
    if (!inputUrl.trim()) {
      toast.error("Please enter a GitHub repository URL");
      return;
    }

    // Check if it's a valid GitHub URL
    if (!inputUrl.includes("github.com")) {
      toast.error("Please enter a valid GitHub URL");
      return;
    }

    // Show GitHub tree modal
    setShowTreeModal(true);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && inputUrl.trim()) {
      if (inputUrl.includes("github.com")) {
        setShowTreeModal(true);
      } else {
        toast.error("Please enter a valid GitHub URL");
      }
    }
  };

  const handleCloseModal = () => {
    setShowTreeModal(false);
    // In a real app, we'd initiate the analysis here
    // For demo purposes, we'll just navigate to the reports page after a delay
    toast.success("Starting analysis of repository", {
      description: "Redirecting to reports page...",
    });
    setTimeout(() => {
      navigate("/reports");
    }, 2000);
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="bg-card border border-border rounded-lg p-8">
        <div className="space-y-6">
          {/* GitHub URL Input */}
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-start">
              <div className="md:col-span-3">
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground">
                    <GitBranch className="h-5 w-5" />
                  </div>
                  <Input
                    type="text"
                    placeholder="Paste a GitHub repository URL"
                    value={inputUrl}
                    onChange={(e) => setInputUrl(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="h-12 bg-secondary text-lg pl-12 border-border focus:border-primary/50 text-foreground"
                  />
                </div>
              </div>
              <Button
                onClick={handleAnalyze}
                className="h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-medium text-base transition-all"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="size-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
                  />
                </svg>
                Analyze
              </Button>
            </div>
          </div>

          {/* Analysis Type Selection */}
          <div className="bg-secondary rounded-lg p-3 border border-border">
            <RadioGroup
              value={analysisType}
              onValueChange={(value) => setAnalysisType(value as AnalysisType)}
              className="flex flex-col sm:flex-row gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem
                  value="fast"
                  id="fast"
                  className="text-primary"
                />
                <Label htmlFor="fast" className="font-medium text-foreground">
                  Fast Analysis
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem
                  value="deep"
                  id="deep"
                  className="text-primary"
                />
                <Label htmlFor="deep" className="font-medium text-foreground">
                  Deep Analysis
                </Label>
              </div>
            </RadioGroup>
          </div>
        </div>
      </div>

      {/* GitHub Tree Modal */}
      <GithubTreeModal
        isOpen={showTreeModal}
        onClose={handleCloseModal}
        repoUrl={inputUrl}
      />
    </div>
  );
}

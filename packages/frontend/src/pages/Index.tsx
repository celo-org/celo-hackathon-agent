import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { Button } from "@/components/ui/button";
import { GitBranch, Github, Sparkles, Star, Users, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "AI-Powered Analysis",
      description:
        "Get detailed insights about code quality, architecture, and best practices",
    },
    {
      icon: <GitBranch className="w-6 h-6" />,
      title: "Repository Insights",
      description:
        "Understand project structure, dependencies, and maintainability metrics",
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Interactive Chat",
      description:
        "Ask questions and get personalized recommendations about any repository",
    },
  ];

  const exampleRepos = [
    {
      name: "facebook/react",
      description:
        "A declarative, efficient, and flexible JavaScript library for building user interfaces",
      stars: "223k",
    },
    {
      name: "microsoft/vscode",
      description: 'Visual Studio Code - Open Source ("Code - OSS")',
      stars: "157k",
    },
    {
      name: "vercel/next.js",
      description: "The React Framework for the Web",
      stars: "120k",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <header className="flex items-center justify-between p-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-semibold text-foreground">RepoChat</h1>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Button onClick={() => navigate("/auth")} variant="outline">
            Sign In
          </Button>
          <Button
            onClick={() => navigate("/auth")}
            className="bg-primary hover:bg-primary/90"
          >
            Get Started
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <div className="flex-1 flex items-center justify-center px-6 py-20">
        <div className="w-full max-w-4xl text-center">
          {/* Hero Title */}
          <div className="mb-16">
            <h1 className="text-5xl md:text-7xl font-bold text-foreground mb-6 leading-tight">
              Analyze any
              <br />
              <span className="bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
                GitHub repository
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-8">
              Get AI-powered insights about code quality, architecture, and best
              practices. Chat with your repositories like never before.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Button
                size="lg"
                onClick={() => navigate("/auth")}
                className="bg-primary hover:bg-primary/90 h-12 px-8 text-lg"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Start Analyzing
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate("/auth")}
                className="h-12 px-8 text-lg"
              >
                <Github className="w-5 h-5 mr-2" />
                View Examples
              </Button>
            </div>
          </div>

          {/* Features */}
          <div className="mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-8">
              Powerful analysis features
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="p-6 bg-card/50 backdrop-blur-sm rounded-xl border border-border/50"
                >
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4 mx-auto">
                    <div className="text-primary">{feature.icon}</div>
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Example Repositories */}
          <div className="mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-8">
              Try analyzing popular repositories
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {exampleRepos.map((repo, index) => (
                <div
                  key={index}
                  className="p-6 bg-card/30 backdrop-blur-sm rounded-xl border border-border/50 hover:bg-card/50 transition-colors cursor-pointer"
                  onClick={() => navigate("/auth")}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Github className="w-5 h-5 text-muted-foreground" />
                      <span className="font-mono text-sm font-medium">
                        {repo.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Star className="w-4 h-4" />
                      <span>{repo.stars}</span>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground text-left">
                    {repo.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* CTA Section */}
          <div className="p-8 bg-gradient-to-r from-primary/10 to-primary/5 rounded-2xl border border-primary/20">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              Ready to get started?
            </h2>
            <p className="text-lg text-muted-foreground mb-6">
              Sign up now and start analyzing repositories in seconds.
            </p>
            <Button
              size="lg"
              onClick={() => navigate("/auth")}
              className="bg-primary hover:bg-primary/90 h-12 px-8 text-lg"
            >
              Create Free Account
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-border/50 p-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span>RepoChat - AI Repository Analysis</span>
          </div>
          <div className="flex items-center gap-6">
            <span>Built with ❤️ for developers</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;

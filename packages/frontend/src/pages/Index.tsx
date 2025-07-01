
import React from "react";
import { Layout } from "@/components/layout/Layout";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { ArrowRight, Star } from "lucide-react";
import { RepositoryAnalyzer } from "@/components/github/RepositoryAnalyzer";

const Index = () => {
  return (
    <Layout>
      {/* Hero Section */}
      <section className="py-24 md:py-32 relative">
        <div className="absolute top-0 left-0 w-full h-full bg-[url('https://media.lovable.dev/bf40b729-352d-48bf-b9a5-36cf201cbe25.png')] bg-cover bg-center bg-no-repeat opacity-10"></div>
        
        <div className="analyzer-container relative z-10">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-secondary rounded-full px-6 py-1.5 border border-border">
              <span className="text-white font-semibold text-sm mr-2">NEW</span>
              <span className="text-foreground/80 text-sm">Latest integration just arrived</span>
            </div>
          </div>
          
          <div className="max-w-4xl mx-auto text-center mb-12">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
              AI Project Analysis
              <span className="block">Made Simple</span>
            </h1>
            <p className="text-lg md:text-xl text-foreground/80 mb-8 max-w-2xl mx-auto">
              Analyze your AI projects quickly and efficiently with comprehensive reports, 
              insights, and recommendations.
            </p>
          </div>
          
          {/* Repository Analyzer Component */}
          <div className="my-12">
            <RepositoryAnalyzer />
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mt-10">
            <Button asChild size="lg" className="bg-white hover:bg-white/90 text-black font-medium">
              <Link to="/reports">
                Browse Reports <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="border-border bg-secondary hover:bg-muted text-foreground">
              <Link to="/auth">
                Sign Up Free
              </Link>
            </Button>
          </div>
        </div>
      </section>
      
      {/* Features */}
      <section className="py-20 bg-secondary border-y border-border">
        <div className="analyzer-container">
          <h2 className="text-3xl font-bold text-center mb-4">Key Features</h2>
          <p className="text-center text-foreground/70 mb-12 max-w-2xl mx-auto">
            Everything you need to optimize and understand your AI projects
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                title: "Advanced Analysis",
                description: "Get detailed analysis of your AI projects with benchmarks and metrics."
              },
              {
                title: "Categorized Reports",
                description: "Filter and search through reports based on various categories and tags."
              },
              {
                title: "Export & Share",
                description: "Download reports as markdown or export multiple reports as a zip archive."
              }
            ].map((feature, index) => (
              <div key={index} className="bg-card border border-border rounded-xl p-6 hover:border-white/30 transition-colors">
                <div className="w-12 h-12 rounded-full flex items-center justify-center mb-4 bg-white/10 text-white">
                  <Star className="h-5 w-5" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-foreground">{feature.title}</h3>
                <p className="text-foreground/70">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="py-24 relative">
        <div className="analyzer-container relative z-10">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to analyze your AI projects?</h2>
            <p className="text-lg opacity-80 mb-8 text-foreground/70">
              Sign up now and get access to our comprehensive AI project analysis tools.
            </p>
            <Button asChild size="lg" className="bg-white hover:bg-white/90 text-black font-medium">
              <Link to="/auth">Get Started Now</Link>
            </Button>
          </div>
        </div>
      </section>
    </Layout>
  );
}

export default Index;

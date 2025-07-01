# AI Project Analyzer - Frontend Package

React-based web interface for the AI Project Analyzer.

## Features

- Modern React application with TypeScript
- Responsive design with Tailwind CSS
- Dark/light theme support
- Real-time analysis progress tracking
- User authentication and management
- Repository analysis submission and results viewing

## Technology Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Shadcn/ui** for UI components
- **React Router** for navigation
- **TanStack Query** for API state management
- **Axios** for HTTP requests

## Development Setup

1. Install dependencies:

```bash
cd packages/frontend
npm install
```

2. Start development server:

```bash
npm run dev
```

3. Build for production:

```bash
npm run build
```

## Environment Variables

Create a `.env.local` file:

```env
VITE_API_URL=http://localhost:8000/api
```

## Features

### Pages

- **Home**: Repository analysis submission
- **Auth**: User login/registration
- **Reports**: Analysis results and history
- **Report Detail**: Individual report viewing

### Components

- Repository URL input with validation
- Analysis type selection (Fast/Deep)
- Real-time progress tracking
- Markdown report rendering with syntax highlighting
- User profile management

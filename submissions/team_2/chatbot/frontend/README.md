# GraphMind Frontend

A React-based frontend for the GraphMind chatbot interface for IIT Kharagpur.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Features

- Clean, modern chat interface
- Real-time messaging with loading states
- Example prompts for quick queries
- Integration with backend API at `http://localhost:8000/got/query`
- Responsive design for mobile and desktop
- Dark theme matching IIT Kharagpur branding

## API Integration

The app sends POST requests to `http://localhost:8000/got/query` with the following structure:

**Request:**
```json
{
  "query": "string"
}
```

**Response:**
```json
{
  "query": "string",
  "answer": "string",
  "confidence": 1,
  "nodes_explored": 0,
  "graph_json": "string",
  "html_visualization": "string",
  "error": "string"
}
```

## Development

The app runs on `http://localhost:3000` by default. Make sure the backend is running on `http://localhost:8000` for the API calls to work.

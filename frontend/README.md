# SE RASNA Mirror - Frontend

Clean, trust-focused frontend for sales call analysis.

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Environment

The frontend expects the backend API to be running at:
```
http://localhost:8000
```

To change this, update `API_BASE_URL` in `lib/api.ts`.

## Pages

- `/` - Upload page for new call submissions
- `/calls/[id]` - Call analysis page with RASNA evaluation

## Architecture

- **Next.js 15** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Fetch API** for backend communication

## Design Principles

- Calm, non-judgmental interface
- No marketing language or hype
- Focus on clarity and trust
- Neutral color palette
- Clear feedback on status and errors

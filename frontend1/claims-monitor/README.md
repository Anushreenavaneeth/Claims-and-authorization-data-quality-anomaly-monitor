# Claims & Authorization Data-Quality Anomaly Monitor

A comprehensive internal tool for monitoring data quality, reviewing detected anomalies, and managing resolution actions across claims, prescriber, pharmacy, and authorization data pipelines.

## Features

### 10 Main Modules

1. **Overview Dashboard** - Real-time summary cards, trend charts, and data source health monitoring
2. **Data Sources** - Monitor and manage data ingestion from Claims, Prescriber, Pharmacy, and Authorization sources
3. **Data Quality Checks** - View validation results across 5 check types with quarantine area
4. **Anomaly Detection & Analysis** - Comprehensive anomaly tracking with root cause and impact analysis
5. **SLA & Priority Dashboard** - Monitor SLA compliance and prioritize resolution efforts
6. **Recommendations (RAG)** - AI-generated recommendations with knowledge base references
7. **Human Review Queue** - Approve, reject, or modify recommended actions
8. **Execute Actions & Resolution Tracking** - Kanban-style board for tracking resolutions
9. **Monitoring Dashboard** - Consolidated reporting with exportable trends and metrics
10. **Feedback Loop** - Submit and review feedback to improve the system

## Tech Stack

- **React 19** with TypeScript
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Recharts** for data visualization
- **Zustand** for state management
- **Lucide React** for icons
- **Vite** for build tooling

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Navigate to the project directory
cd claims-monitor

# Install dependencies (if not already done)
npm install

# Start the development server
npm run dev
```

The application will open automatically at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
claims-monitor/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Base UI components (Button, Card, Modal, etc.)
│   │   ├── shared/         # Shared components (Sidebar, TopBar, StatusBadge)
│   │   └── Layout.tsx      # Main layout wrapper
│   ├── pages/              # Page components for each module
│   │   ├── Overview.tsx
│   │   ├── DataSources.tsx
│   │   ├── QualityChecks.tsx
│   │   ├── Anomalies.tsx
│   │   ├── SLA.tsx
│   │   ├── Recommendations.tsx
│   │   ├── Review.tsx
│   │   ├── Resolutions.tsx
│   │   ├── Monitoring.tsx
│   │   └── Feedback.tsx
│   ├── services/           # API service layer
│   │   ├── api.ts          # API functions (ready for backend integration)
│   │   └── mockData.ts     # Mock data for development
│   ├── store/              # Zustand state management
│   │   └── useStore.ts
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts
│   ├── lib/                # Utility functions
│   │   └── utils.ts
│   ├── App.tsx             # Main app component with routing
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles and Tailwind imports
├── public/                 # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## Integrating with Backend API

The application is structured for easy backend integration:

### 1. API Service Layer (`src/services/api.ts`)

All API calls are centralized in this file. Each function currently returns mock data but is structured to easily swap in real API calls:

```typescript
// Current (Mock):
export async function getAnomalies(): Promise<Anomaly[]> {
  await delay();
  return mockAnomalies;
}

// Replace with (Real API):
export async function getAnomalies(): Promise<Anomaly[]> {
  const response = await fetch('/api/anomalies');
  return response.json();
}
```

### 2. Expected API Endpoints

- `GET /api/dashboard/summary` - Dashboard summary metrics
- `GET /api/dashboard/anomaly-trends` - Time series anomaly data
- `GET /api/dashboard/severity-breakdown` - Severity distribution data
- `GET /api/sources` - All data sources
- `GET /api/sources/:id` - Single data source
- `GET /api/quality-checks` - All quality checks
- `GET /api/quality-checks/quarantine` - Quarantined records
- `GET /api/anomalies` - All anomalies
- `GET /api/anomalies/:id` - Single anomaly
- `GET /api/sla-items` - SLA tracking items
- `GET /api/recommendations` - All recommendations
- `GET /api/recommendations?anomalyId=:id` - Recommendations for anomaly
- `GET /api/knowledge-base` - Knowledge base articles
- `GET /api/knowledge-base/search?q=:query` - Search knowledge base
- `GET /api/resolutions` - All resolutions
- `PATCH /api/resolutions/:id` - Update resolution status
- `GET /api/reviews` - Review queue items
- `POST /api/reviews/:id/approve` - Approve action
- `POST /api/reviews/:id/reject` - Reject action
- `POST /api/reviews/:id/modify` - Modify action
- `GET /api/feedback` - All feedback
- `POST /api/feedback` - Submit new feedback

### 3. Type Definitions (`src/types/index.ts`)

All TypeScript interfaces match the expected API response shapes. Use these to validate your backend responses.

### 4. State Management (`src/store/useStore.ts`)

The Zustand store provides centralized state that can be easily populated from API calls.

## Mock Data

All mock data is defined in `src/services/mockData.ts` with realistic structures matching production data shapes. This allows development and testing without a backend.

## Customization

### Colors and Themes

Edit `src/index.css` and `tailwind.config.js` to customize the color scheme.

### Adding New Features

1. Create new page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/shared/Sidebar.tsx`
4. Add API functions in `src/services/api.ts`
5. Add types in `src/types/index.ts`

## Design Philosophy

- **Data-Dense Enterprise UI** - Inspired by Datadog/Retool with focus on information density
- **Clean & Professional** - Tailwind CSS with consistent spacing and typography
- **Responsive** - Mobile-friendly layouts with collapsible sidebar
- **Type-Safe** - Full TypeScript coverage for reliability
- **Modular** - Reusable components and clear separation of concerns
- **API-Ready** - Structured for seamless backend integration

## License

Internal use only.

## Support

For questions or issues, contact the development team.

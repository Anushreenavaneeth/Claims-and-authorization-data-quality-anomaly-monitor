# Quick Start Guide

## Running the Application

```bash
# Make sure you're in the claims-monitor directory
cd claims-monitor

# Start the development server
npm run dev
```

The application will automatically open in your browser at `http://localhost:3000`

## What You'll See

The application includes 10 fully functional pages with mock data:

1. **Overview Dashboard (/)** - Landing page with summary metrics, charts, and data source health
2. **Data Sources (/data-sources)** - Monitor all 4 data sources (Claims, Prescriber, Pharmacy, Authorization)
3. **Quality Checks (/quality-checks)** - View validation results and quarantined records
4. **Anomalies (/anomalies)** - Browse and analyze detected anomalies
5. **SLA & Priority (/sla)** - Track SLA compliance and prioritize work
6. **Recommendations (/recommendations)** - View AI-generated recommendations and search knowledge base
7. **Human Review (/review)** - Approve or reject recommended actions
8. **Execute Actions (/resolutions)** - Track resolution progress via Kanban board
9. **Monitoring (/monitoring)** - View consolidated reports and export data
10. **Feedback (/feedback)** - Submit and review system feedback

## Key Features to Explore

### Navigation
- **Collapsible Sidebar** - Click the arrow icon in the sidebar to collapse/expand
- **Responsive Design** - Resize your browser to see mobile-friendly layouts
- **Active State** - Currently selected page is highlighted in the sidebar

### Interactive Elements
- **Data Tables** - Click column headers to sort
- **Row Click** - Click table rows to see detailed views
- **Filters** - Use filter buttons on anomaly and quality check pages
- **Modals** - Click anomaly rows to see detailed analysis
- **Actions** - Try approve/reject buttons on the Review page

### Charts & Visualizations
- Line charts showing trends over time
- Bar charts for categorical data
- Pie charts for distribution analysis
- Color-coded severity indicators

### Mock Data
- All data is realistic but fabricated
- Anomalies have full root cause and impact analysis
- SLA items show time remaining calculations
- Resolution tracking with progress indicators

## Customization Tips

### Change Colors
Edit `src/index.css` - CSS variables control the entire color scheme

### Modify Mock Data
Edit `src/services/mockData.ts` - Add, remove, or change data items

### Add New Features
1. Create component in `src/pages/YourPage.tsx`
2. Add route in `src/App.tsx`
3. Add nav item in `src/components/shared/Sidebar.tsx`

## Backend Integration

When your backend is ready:

1. Open `src/services/api.ts`
2. Replace mock data returns with fetch calls
3. All TypeScript types are already defined in `src/types/index.ts`
4. Expected endpoints are documented in the README

Example:
```typescript
// Change from:
export async function getAnomalies(): Promise<Anomaly[]> {
  await delay();
  return mockAnomalies;
}

// To:
export async function getAnomalies(): Promise<Anomaly[]> {
  const response = await fetch('https://your-api.com/api/anomalies');
  if (!response.ok) throw new Error('Failed to fetch anomalies');
  return response.json();
}
```

## Build for Production

```bash
npm run build
```

Files will be in the `dist/` folder, ready to deploy to any static hosting service.

## Troubleshooting

### Port Already in Use
If port 3000 is taken, edit `vite.config.ts` and change the port number.

### Module Not Found
Run `npm install` to ensure all dependencies are installed.

### Type Errors
Make sure you're using TypeScript 5.0+ and have all type definitions installed.

## Next Steps

1. Explore all 10 pages to understand the workflow
2. Review the code structure in `src/`
3. Customize colors and branding
4. Plan backend API integration
5. Add authentication/authorization as needed

Enjoy building with the Claims Monitor!

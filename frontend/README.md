# jPOS Banking UI - Frontend

React + Ant Design frontend for the jPOS Core Banking Dashboard with SAP UI5 (Fiori) styling.

## 🎯 Features

- **Dashboard**: Overview of key banking metrics
- **Transactions**: Search, filter, and view transaction details
- **Reconciliation**: Monitor issues, missing transactions, and reversal candidates
- **Settlement**: Manage settlement batches and settlement operations
- **Net Settlement**: View net positions and batch summaries
- **Routing**: Inspect BIN/terminal routing and PAN route decisions
- **Fraud Phase 2**: Dashboard KPIs, Trends, Rule/Terminal breakdowns, rich Alerts actions, Rules with severity/action/priority, Blacklist with expiry metadata, Case timeline, Audit log, and live Fraud Check with score breakdown
- **JWT Authentication**: Secure login with JWT tokens from backend API
- **Responsive Design**: Mobile-friendly layout with Ant Design components
- **Compact UI**: Optimized for banking/fintech dashboards

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- npm 8+

### Installation

```bash
# Install dependencies
npm install

# Start development server (port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

If your environment uses SSL interception and install is slow/stuck at `idealTree`, use the project npm config in `.npmrc`:

- `strict-ssl=false`
- `progress=false`
- `audit=false`
- `fund=false`

You can then install with:

```bash
npm install --no-audit --no-fund
```

### Environment Variables

Create `.env.local` from `.env.example`:

```bash
cp .env.example .env.local
```

Update values as needed:
```
VITE_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
src/
├── pages/
│   ├── Login.jsx              # Login page with JWT authentication
│   ├── Dashboard.jsx          # Key metrics overview
│   ├── Transactions.jsx       # Transaction search and details
│   ├── Reconciliation.jsx     # Reconciliation dashboard with tabs
│   ├── Settlement.jsx         # Settlement batches and operations
│   ├── NetSettlement.jsx      # Net settlement positions and summary
│   ├── Routing.jsx            # BIN/terminal configuration and route checks
│   └── Fraud.jsx              # Fraud monitoring and operator actions
├── services/
│   └── api.js                 # Axios API client with JWT interceptors
├── components/                # Reusable components (coming soon)
├── theme.js                   # Ant Design SAP UI5 theme
├── App.jsx                    # Main app with routing and layout
├── main.jsx                   # React entry point
└── index.css                  # Global styles
```

## 🔐 Authentication

The frontend uses JWT authentication:

1. User logs in at `/login` with username/password (demo: admin/admin123)
2. Backend returns JWT token via `POST /auth/login`
3. Token stored in `localStorage` as `access_token`
4. Token automatically added to all API requests via Authorization header
5. Invalid/expired tokens trigger redirect to login

### API Client Setup

The `services/api.js` axios instance automatically:
- Adds `Authorization: Bearer <token>` to all requests
- Redirects to login on 401 responses
- Handles error responses in `{code, message}` format

## 🎨 Theming

The application uses a custom SAP UI5 (Fiori) inspired theme:
- **Primary Color**: `#0a6ed1` (SAP Blue)
- **Background**: `#f5f6f7` (Light neutral)
- **Text**: `#1d2d3e` (Dark)
- **Success**: `#107e3e` (Green)
- **Warning**: `#e3a821` (Orange)
- **Error**: `#bb0000` (Red)

Configured in `src/theme.js` with Ant Design token system.

## 📊 API Integration

The frontend integrates with the FastAPI backend on `http://localhost:8000`:

### Auth Endpoints
- `POST /auth/login` - Get JWT token

### Transaction Endpoints
- `GET /transactions` - List transactions with filters
- `GET /transactions/{id}` - Get transaction details

### Reconciliation Endpoints
- `GET /reconciliation/issues` - List reconciliation issues
- `GET /reconciliation/missing` - List missing transactions
- `GET /reconciliation/reversal-candidates` - List reversal candidates
- `GET /reconciliation/summary` - Get summary statistics

### Settlement Endpoints
- `POST /settlement/run` - Run settlement process
- `GET /settlement/batches` - List settlement batches
- `GET /settlement/batches/{batch_id}` - Get batch details

### Dashboard Endpoints
- `GET /dashboard/summary` - Get dashboard summary metrics
- `GET /dashboard/status` - Get status distribution
- `GET /dashboard/volume` - Get daily volume metrics

### Fraud Endpoints
- `GET /fraud/dashboard` - Fraud KPIs
- `GET /fraud/dashboard/trends` - Daily trends for analytics tab
- `GET /fraud/dashboard/breakdown` - Breakdown by rule and by terminal
- `GET /fraud/alerts` - Alerts queue
- `POST /fraud/alerts/{id}/action` - `ACK`, `CLOSE`, `ESCALATE`, `BLOCK_CARD`, `BLOCK_TERMINAL`, `APPROVE`
- `GET /fraud/rules` - Fraud rules list (priority-sorted)
- `POST /fraud/rules` - Create fraud rule with `severity`, `action`, `priority`
- `GET /fraud/blacklist` - Blacklist list (PAN values masked)
- `POST /fraud/blacklist` - Add blacklist entry with optional `expiry_date`
- `GET /fraud/cases` - Fraud cases list
- `POST /fraud/cases` - Create fraud case with notes
- `PATCH /fraud/cases/{id}` - Update case summary/assignee/notes
- `PATCH /fraud/cases/{id}/status` - Set case status (`OPEN` / `INVESTIGATING` / `CLOSED` plus legacy statuses)
- `GET /fraud/cases/{id}/timeline` - Fetch case action history
- `DELETE /fraud/cases/{id}` - Delete case
- `GET /fraud/audit-log` - Fetch fraud audit trail
- `GET /fraud/flagged-transactions` - List flagged/declined transactions with risk scores
- `POST /fraud/check` - Run rule check and return score breakdown

Fraud UI governance logic:
- Rules tab: create + list only (no edit/delete/status mutation).
- Blacklist tab: create + list only (no edit/delete/status mutation).
- Cases tab: supports edit, delete, status transitions, and timeline review.

## 🔧 Development

### Run with Hot Reload
```bash
npm run dev
```

The dev server proxies `/api/*` requests to the backend (configured in `vite.config.js`).

### Code Style
- React Hooks for state management
- Ant Design components with `size="small"` for compact layout
- Functional components with ES6 arrow functions

## 🐳 Docker

The frontend runs in the docker-compose stack:

```bash
docker-compose up
```

Frontend will be available at:
- Development: `http://localhost:5173`
- Production: `http://localhost:3000`

## 📝 Notes

- All components use Ant Design's `size="small"` for compact UI
- Tables use 50 item pages by default
- Forms use vertical layout for clarity
- Modal dialogs for detail views
- Status colors follow standard conventions (green=success, red=error, orange=warning)

## 🚧 Future Enhancements

- [ ] Add component library in `src/components/`
- [ ] Implement real-time updates via WebSocket
- [ ] Add more charts and visualizations
- [ ] Implement audit logs
- [ ] Add user management pages
- [ ] Export/download reports functionality

## 📄 License

Same as jPOS project

# Frontend Setup Guide

## 📋 Quick Summary

The jPOS Banking UI frontend has been fully created with all necessary files:

✅ **13 Files Created:**
1. `package.json` — React + Ant Design dependencies
2. `vite.config.js` — Vite development server with API proxy
3. `index.html` — HTML entry point
4. `src/theme.js` — SAP UI5 Fiori color theme
5. `src/main.jsx` — React app entry point with Ant Design theme provider
6. `src/index.css` — Global styles with component overrides
7. `src/App.jsx` — Main app layout with sidebar navigation, header, authentication
8. `src/pages/Dashboard.jsx` — Dashboard with 8 metrics cards and recent transactions
9. `src/pages/Transactions.jsx` — Transaction search, list, filter, and detail modal
10. `src/pages/Reconciliation.jsx` — 4 tabs: Summary, Issues, Missing, Reversals
11. `src/pages/Settlement.jsx` — Settlement batches, run operation, batch details
12. `src/pages/Login.jsx` — JWT login form with demo credentials (admin/admin123)
13. `src/services/api.js` — Axios HTTP client with JWT token interceptors

✅ **Additional Files:**
- `frontend/README.md` — Comprehensive documentation
- `.env.example` — Environment variables template
- `.gitignore` — Git ignore patterns
- `frontend/dockerfile` — Docker container setup

---

## 🚀 Installation & Setup

### Option 1: Docker (Recommended for corporate SSL environment)

```bash
# Start the entire stack (backend + frontend + database)
docker-compose up

# Frontend will be available at:
# - Development: http://localhost:5173
# - API backend: http://localhost:8000
```

The Docker container will:
- Install npm dependencies automatically
- Handle the corporate SSL certificate
- Run the Vite dev server with hot reload
- Proxy API calls to backend on http://localhost:8000

### Option 2: Local Installation (if SSL certificate is handled)

```bash
cd frontend

# Configure npm for SSL (if needed)
npm config set strict-ssl false
npm config set cafile /path/to/FG-SSL-INSPECTION.cer

# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🔐 Authentication

### Login Flow

1. Navigate to http://localhost:5173 (or http://localhost:3000 in production)
2. You'll be redirected to `/login` if not authenticated
3. Enter credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
4. Click "Sign In"
5. JWT token is received and stored in localStorage
6. Token is automatically added to all API requests

### How It Works

- `src/services/api.js` — Axios instance with interceptors
- Request interceptor adds: `Authorization: Bearer <token>`
- Response interceptor redirects to login on 401 errors
- Token stored as `access_token` in localStorage
- Username stored for display in header

---

## 🎨 UI Components & Pages

### Dashboard
- **Path**: `/`
- **Features**: 8 metrics cards (Total, Approved, Pending, Failed, Amount stats)
- **Data**: Calls `/dashboard/metrics` endpoint
- **Shows**: Recent transactions (last 10)

### Transactions
- **Path**: `/transactions`
- **Features**: 
  - Search/filter by ID, STAN, Status, Response Code
  - Table with 50-item pagination
  - Detail modal with full transaction info
  - Retry count visibility
- **Data**: Calls `/transactions` and `/transactions/{id}` endpoints

### Reconciliation
- **Path**: `/reconciliation`
- **Features**:
  - Summary tab: 4 statistics (Total Issues, Missing, Reversals, Amount at Risk)
  - Issues tab: List of reconciliation issues with retry count
  - Missing tab: Transactions missing in settlement
  - Reversals tab: Auto-reversal candidates
  - Refresh button for live data
- **Data**: Calls 4 reconciliation endpoints

### Settlement
- **Path**: `/settlement`
- **Features**:
  - Run Settlement button with confirmation modal
  - List all settlement batches with pagination
  - View batch details in modal
  - Status indicators (Completed/Pending/Failed)
  - Timestamps for all batches
- **Data**: Calls `/settlement/run`, `/settlement/batches`, `/settlement/batches/{id}` endpoints

---

## 📡 API Integration

All API calls are centralized in `src/services/api.js`:

```javascript
// Available API methods:

// Authentication
authAPI.login(username, password)

// Transactions
transactionAPI.list(params)
transactionAPI.get(id)

// Reconciliation
reconciliationAPI.getIssues(params)
reconciliationAPI.getMissing(params)
reconciliationAPI.getReversalCandidates(params)
reconciliationAPI.getSummary()

// Settlement
settlementAPI.run()
settlementAPI.getBatches(params)
settlementAPI.getBatch(batchId)

// Dashboard
dashboardAPI.getMetrics()
```

All endpoints automatically receive JWT bearer token in Authorization header.

---

## 🎯 Design System

### SAP UI5 (Fiori) Theme
- **Primary Color**: `#0a6ed1` (SAP Blue)
- **Background**: `#f5f6f7` (Light neutral)
- **Text**: `#1d2d3e` (Dark text)
- **Success**: `#107e3e` (Green)
- **Warning**: `#e3a821` (Orange)
- **Error**: `#bb0000` (Red)

### Component Sizing
- **Font**: 12px (compact for banking UIs)
- **Control Height**: 28px
- **Border Radius**: 4px (minimal)
- **Padding**: 16px margins/padding

### Styling Files
- `src/theme.js` — Ant Design token configuration
- `src/index.css` — Global styles and component overrides

---

## 🔧 Development

### Hot Reload

The Vite dev server automatically reloads when you save files:

```bash
npm run dev
# Changes to .jsx, .css, .js files are reflected instantly
```

### Environment Variables

Create `.env.local` in frontend directory:

```
VITE_API_URL=http://localhost:8000
```

Access in code:

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

---

## 📦 Dependencies

### Main Dependencies
- **React** 18.2.0 — UI framework
- **ReactDOM** 18.2.0 — DOM rendering
- **Ant Design** 5.10.0 — UI component library
- **@ant-design/icons** 5.2.6 — Icon library
- **Axios** 1.6.0 — HTTP client
- **Recharts** 2.10.3 — Chart library (ready for future use)

### Dev Dependencies
- **Vite** 5.0.4 — Build tool and dev server
- **@vitejs/plugin-react** 4.2.0 — React plugin for Vite

---

## 🐳 Docker Deployment

### Running in Docker

```bash
# Build and start all services
docker-compose up

# Rebuild frontend image
docker-compose build jpos-frontend

# Stop services
docker-compose down

# View logs
docker-compose logs -f jpos-frontend
```

### Frontend Service Configuration

- **Container**: `jpos-frontend`
- **Image**: `node:18-alpine`
- **Port**: `5173` (dev server)
- **Volume**: `./frontend:/app` (live source code)
- **Command**: `npm run dev --host` (Vite dev server)

---

## 🚨 Troubleshooting

### npm Install Issues (SSL Certificate)

**Symptom**: `unable to get issuer certificate` error

**Solution 1 - Docker (Recommended)**:
```bash
docker-compose up jpos-frontend
# Docker container will handle SSL automatically
```

**Solution 2 - Local**:
```bash
npm config set strict-ssl false
npm config set cafile /path/to/FG-SSL-INSPECTION.cer
npm install
```

### Frontend Can't Connect to Backend

**Check**:
1. Backend is running: `curl http://localhost:8000/health`
2. CORS is enabled (should be in backend configuration)
3. API URL in `.env.local` matches backend address

### Login Not Working

**Check**:
1. Backend `/auth/login` endpoint is accessible
2. Credentials are correct (admin/admin123)
3. Browser console for error messages
4. Check localStorage for `access_token`

---

## 📝 Project Structure

```
frontend/
├── public/                    # Static assets
├── src/
│   ├── pages/                 # Page components
│   │   ├── Login.jsx          # Login page
│   │   ├── Dashboard.jsx      # Dashboard overview
│   │   ├── Transactions.jsx   # Transaction management
│   │   ├── Reconciliation.jsx # Reconciliation dashboard
│   │   └── Settlement.jsx     # Settlement operations
│   ├── services/
│   │   └── api.js             # Axios HTTP client
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # React entry point
│   ├── theme.js               # Ant Design theme
│   └── index.css              # Global styles
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── index.html                 # HTML entry point
├── vite.config.js             # Vite configuration
├── package.json               # Dependencies
├── dockerfile                 # Docker image
└── README.md                  # This file
```

---

## ✅ Verification Checklist

- [x] All 13 source files created
- [x] Package.json with correct dependencies
- [x] Vite configuration with API proxy
- [x] SAP UI5 theme configured
- [x] All 4 main pages created
- [x] JWT authentication integrated
- [x] API service with interceptors
- [x] Docker container configuration
- [x] Documentation complete
- [ ] npm install completed locally (pending due to corporate SSL)
- [ ] npm install will complete in Docker container

---

## 🎯 Next Steps

1. **Run in Docker** (Recommended):
   ```bash
   docker-compose up
   ```

2. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Login: admin/admin123

3. **Verify functionality**:
   - Test login flow
   - Check Dashboard metrics
   - Browse Transactions
   - Check Reconciliation data
   - Try Settlement operations

4. **Development**:
   - Modify pages in `src/pages/`
   - Changes auto-reload via Vite
   - Add new components in `src/components/`

---

## 📚 Additional Resources

- **Vite Documentation**: https://vitejs.dev/guide/
- **React Documentation**: https://react.dev/
- **Ant Design Documentation**: https://ant.design/components/overview/
- **Axios Documentation**: https://axios-http.com/docs/intro

---

## 📄 License

Same as jPOS project.

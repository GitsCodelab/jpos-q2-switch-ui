# React + Ant Design (UI5 Style) Implementation Plan

## 🎯 Goal
Build a React application using Ant Design styled to resemble SAP UI5 (Fiori) for enterprise/core banking dashboards.

---

## 🧭 Target Stack
- React (Vite recommended)
- Ant Design
- Optional: Recharts / ECharts
- Backend: FastAPI / postgres /oracle

---

## 🚀 Phase 1 — Project Setup

### 1. Create project (Vite)
```bash
npm create vite@latest banking-ui -- --template react
cd banking-ui
npm install
```

### 2. Install dependencies
```bash
npm install antd @ant-design/icons
```

### 3. Run project
```bash
npm run dev
```

---

## 🎨 Phase 2 — UI5 Theme Setup

Create `src/theme.js`:
```javascript
export const ui5Theme = {
  token: {
    colorPrimary: "#0a6ed1",
    colorBgBase: "#f5f6f7",
    colorTextBase: "#1d2d3e",
    borderRadius: 4,
    fontSize: 12,
    controlHeight: 28,
  },
};
```

Apply theme in `main.jsx`:
```javascript
import { ConfigProvider } from "antd";
import { ui5Theme } from "./theme";

<ConfigProvider theme={ui5Theme}>
  <App />
</ConfigProvider>
```

---

## 🔤 Phase 3 — Fonts

Add to `index.css`:
```css
body {
  font-family: "Segoe UI", Roboto, Arial, sans-serif;
  background: #f5f6f7;
}
```

---

## 🧱 Phase 4 — Layout

Structure:
- Sidebar (Menu)
- Header
- Content

Example:
```javascript
import { Layout, Menu } from "antd";

const { Header, Sider, Content } = Layout;

<Layout style={{ minHeight: "100vh" }}>
  <Sider width={220}>
    <Menu items={[
      { key: "1", label: "Transactions" },
      { key: "2", label: "Reconciliation" },
      { key: "3", label: "Settlement" }
    ]}/>
  </Sider>

  <Layout>
    <Header style={{ background: "#fff" }}>
      Core Banking Dashboard
    </Header>

    <Content style={{ margin: 16 }}>
      {/* Pages */}
    </Content>
  </Layout>
</Layout>
```

---

## 📊 Phase 5 — Tables

```javascript
import { Table } from "antd";

<Table
  size="small"
  bordered
  pagination={{ pageSize: 50 }}
/>
```

---

## 🧾 Phase 6 — Forms

```javascript
import { Form, Input, Button } from "antd";

<Form layout="vertical">
  <Form.Item label="Account Number">
    <Input size="small" />
  </Form.Item>

  <Button type="primary" size="small">
    Search
  </Button>
</Form>
```

---

## 📁 Phase 7 — Project Structure

```
src/
 ├── components/
 ├── pages/
 │     ├── Transactions.jsx
 │     ├── Reconciliation.jsx
 │     └── Settlement.jsx
 ├── services/
 │     └── api.js
 ├── theme.js
 ├── App.jsx
 └── main.jsx
```

---

## ⚙️ Phase 8 — UI Guidelines

- Use compact components (`size="small"`)
- Keep spacing tight
- Neutral colors (grey/white/blue)
- Avoid animations
- Minimal icons

---

## 🏁 Final Outcome

- UI similar to SAP UI5 / Fiori
- Fast development with React
- Scalable for fintech dashboards

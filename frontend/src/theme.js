// SAP UI5 (Fiori) Inspired Theme for jPOS Banking UI
export const ui5Theme = {
  token: {
    colorPrimary: "#0a6ed1",        // SAP Blue
    colorBgBase: "#f5f6f7",          // Light neutral background
    colorTextBase: "#1d2d3e",        // Dark text
    colorBorder: "#d8dce6",          // Soft border
    borderRadius: 4,                 // Compact radius
    fontSize: 12,                    // Smaller font for banking UIs
    controlHeight: 28,               // Compact controls
    lineHeight: 1.5,
    colorInfo: "#0a6ed1",            // Info blue (same as primary)
    colorSuccess: "#107e3e",         // Success green
    colorWarning: "#e3a821",         // Warning orange
    colorError: "#bb0000",           // Error red
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
  },
  components: {
    Button: {
      fontWeight: 500,
      controlHeight: 28,
    },
    Table: {
      headerBg: "#ffffff",
      headerColor: "#1d2d3e",
      fontSize: 12,
      lineHeight: 1.5,
    },
    Form: {
      labelFontSize: 12,
    },
    Input: {
      fontSize: 12,
      controlHeight: 28,
    },
    Select: {
      fontSize: 12,
      controlHeight: 28,
    },
    Menu: {
      fontSize: 12,
      itemHeight: 32,
    },
  },
};

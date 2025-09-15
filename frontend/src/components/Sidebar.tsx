import React, { useState } from "react";
import { NavLink } from "react-router-dom";

const items = [
  { to: "/", label: "Home", icon: "fa-home" },
  { to: "/dashboard", label: "Dashboard", icon: "fa-chart-line" },
  { to: "/reports", label: "Reports", icon: "fa-file-alt" },
  { to: "/import", label: "Import", icon: "fa-file-import" },
  { to: "/users", label: "Users", icon: "fa-users" },
  { to: "/settings", label: "Settings", icon: "fa-cog" },
  { to: "/chat", label: "Chat", icon: "fa-comments" },
  { to: "/upload", label: "Upload CSV", icon: "fa-upload" }   // ✅ new item
];

export default function Sidebar(): JSX.Element {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`} aria-label="Main sidebar">
      <div className="brand">
        <div className="logo">M</div>
        <div style={{ fontWeight: 700 }}>{collapsed ? "" : "Monexa"}</div>
      </div>

      <div className="toggle" onClick={() => setCollapsed(!collapsed)} aria-hidden>
        <i className="fas fa-bars" />
      </div>

      <nav>
        <ul>
          {items.map((it) => (
            <li key={it.to}>
              <NavLink
                to={it.to}
                style={{
                  color: "inherit",
                  textDecoration: "none",
                  display: "flex",
                  alignItems: "center",
                  width: "100%",
                }}
              >
                <i className={`fas ${it.icon} icon`} style={{ width: 20 }} />
                <span style={{ display: collapsed ? "none" : "inline" }}>{it.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}

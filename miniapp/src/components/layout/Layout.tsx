import { useEffect } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Folder, House, Menu, Wallet, CalendarCheck } from "lucide-react";
import { telegram } from "../../telegram/webapp";
const primary = ["/", "/attendance", "/projects", "/finance", "/more"];
const links = [
  { to: "/", label: "Bosh sahifa", icon: House },
  { to: "/attendance", label: "Davomat", icon: CalendarCheck },
  { to: "/projects", label: "Loyihalar", icon: Folder },
  { to: "/finance", label: "Moliya", icon: Wallet },
  { to: "/more", label: "Ko'proq", icon: Menu },
];
export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    const app = telegram();
    const nested = !primary.includes(location.pathname);
    const back = () => {
      if (location.pathname.startsWith("/projects/")) navigate("/projects");
      else if (location.pathname.startsWith("/people/")) navigate("/workers");
      else navigate("/more");
    };
    if (nested) app?.BackButton.show();
    else app?.BackButton.hide();
    app?.BackButton.onClick(back);
    window.scrollTo(0, 0);
    return () => app?.BackButton.offClick(back);
  }, [location.pathname, navigate]);
  return (
    <div className="app-shell">
      <div className="brand">
        <span className="brand-symbol">h</span> hisobchi{" "}
        <span className="brand-label">ISH BOSHQARUVI</span>
      </div>
      <main id="main">
        <Outlet />
      </main>
      <nav className="bottom-nav" aria-label="Asosiy menyu">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              isActive ||
              (to === "/more" &&
                !["/", "/attendance", "/projects", "/finance"].some((p) =>
                  p === "/"
                    ? location.pathname === p
                    : location.pathname.startsWith(p),
                ))
                ? "active"
                : ""
            }
          >
            <Icon size={22} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

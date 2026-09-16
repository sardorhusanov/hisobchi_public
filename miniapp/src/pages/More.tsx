import { Link } from "react-router-dom";
import {
  Banknote,
  Calculator,
  ChartNoAxesCombined,
  ChevronRight,
  Handshake,
  Settings,
  Users,
} from "lucide-react";
import { Header } from "../components/common/ui";
const items = [
  {
    to: "/workers",
    label: "Ishchilar",
    description: "Jamoani boshqarish",
    icon: Users,
  },
  {
    to: "/partners",
    label: "Hamkorlar",
    description: "Hamkorlik va davomat",
    icon: Handshake,
  },
  {
    to: "/salary",
    label: "Oylik",
    description: "Oylik hisob-kitoblar",
    icon: Calculator,
  },
  {
    to: "/advances",
    label: "Avans",
    description: "Oldindan to'lovlar",
    icon: Banknote,
  },
  {
    to: "/reports",
    label: "Hisobotlar",
    description: "Batafsil tahlil",
    icon: ChartNoAxesCombined,
  },
  {
    to: "/settings",
    label: "Sozlamalar",
    description: "Hisob ma’lumotlari",
    icon: Settings,
  },
];
export default function More() {
  return (
    <>
      <Header title="Ko'proq" subtitle="Biznesingizni boshqaring" />
      <div className="list">
        {items.map(({ to, label, description, icon: Icon }) => (
          <Link className="card person-line" to={to} key={to}>
            <span className="icon-tile">
              <Icon size={21} />
            </span>
            <div>
              <h3>{label}</h3>
              <p className="muted">{description}</p>
            </div>
            <ChevronRight className="trailing" size={18} />
          </Link>
        ))}
      </div>
    </>
  );
}

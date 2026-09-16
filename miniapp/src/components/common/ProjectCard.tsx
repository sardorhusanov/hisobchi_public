import { ArrowUpRight, Folder } from "lucide-react";
import { Link } from "react-router-dom";
import type { ProjectSummary } from "../../types/models";
import { formatMoney } from "../../utils/format";
export function ProjectCard({
  data,
  compact = false,
}: {
  data: ProjectSummary;
  compact?: boolean;
}) {
  return (
    <Link to={`/projects/${data.project.id}`} className="card project-card">
      <div className="project-heading">
        <span className="icon-tile">
          <Folder size={19} />
        </span>
        <div>
          <h3>{data.project.name}</h3>
          <span className="muted">
            {data.project.status === "ACTIVE" ? "Faol loyiha" : "Tugallangan"}
          </span>
        </div>
        <ArrowUpRight className="trailing" size={18} />
      </div>
      {!compact && (
        <div className="split muted">
          <span>
            Tushum
            <br />
            <b>{formatMoney(data.income)}</b>
          </span>
          <span>
            Xarajat
            <br />
            <b>{formatMoney(data.expenses)}</b>
          </span>
        </div>
      )}
      <div className="balance-row">
        <span>Qoldiq</span>
        <strong>{formatMoney(data.balance)}</strong>
      </div>
    </Link>
  );
}

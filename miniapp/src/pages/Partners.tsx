import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ChevronRight, Plus } from "lucide-react";
import { api } from "../api";
import { PersonForm } from "../components/forms/PersonForm";
import { Empty, ErrorState, Header, Loading } from "../components/common/ui";
export default function Partners() {
  const [add, setAdd] = useState(false);
  const [archive, setArchive] = useState(false);
  const data = useQuery({
    queryKey: ["partners", archive],
    queryFn: () => api.people("PARTNER", !archive),
  });
  return (
    <>
      <Header
        title="Hamkorlar"
        subtitle="Davomat va olingan mablag'lar"
        action={
          <button className="primary" onClick={() => setAdd(true)}>
            <Plus size={18} /> Qo'shish
          </button>
        }
      />
      <label className="check">
        <input
          type="checkbox"
          checked={archive}
          onChange={(e) => setArchive(e.target.checked)}
        />{" "}
        Arxivlanganlarni ko'rsatish
      </label>
      {data.isPending ? (
        <Loading />
      ) : data.error ? (
        <ErrorState error={data.error} retry={() => void data.refetch()} />
      ) : !data.data.length ? (
        <Empty
          text="Hozircha hamkorlar yo'q."
          action={
            <button className="secondary" onClick={() => setAdd(true)}>
              Hamkor qo'shish
            </button>
          }
        />
      ) : (
        <div className="list">
          {data.data.map((p) => (
            <Link
              className="card person-line"
              to={`/people/${p.id}`}
              key={p.id}
            >
              <span className="avatar small">{p.name.charAt(0)}</span>
              <div>
                <h3>{p.name}</h3>
                <p className="muted">
                  {p.is_active ? "Hamkor" : "Arxivlangan"}
                </p>
              </div>
              <ChevronRight className="trailing" size={18} />
            </Link>
          ))}
        </div>
      )}
      {add && <PersonForm role="PARTNER" onClose={() => setAdd(false)} />}
    </>
  );
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api";
import { useRefresh } from "../../hooks/data";
import type { Category } from "../../types/models";
import { categoryLabel, normalizeMoney, today } from "../../utils/format";
import { ErrorState, Form, Loading, Modal } from "../common/ui";
export function TransactionForm({
  kind,
  projectId = "",
  workerId = "",
  onClose,
}: {
  kind: "advance" | "income" | "expense";
  projectId?: string;
  workerId?: string;
  onClose: () => void;
}) {
  const people = useQuery({
    queryKey: ["people"],
    queryFn: () => api.people(),
  });
  const projects = useQuery({
    queryKey: ["projects", "ACTIVE"],
    queryFn: () => api.projects(),
  });
  const [amount, setAmount] = useState("");
  const [day, setDay] = useState(today());
  const [month, setMonth] = useState(today().slice(0, 7));
  const [project, setProject] = useState(projectId);
  const [person, setPerson] = useState(workerId);
  const [category, setCategory] = useState<Category>("BUSINESS");
  const [note, setNote] = useState("");
  const refresh = useRefresh();
  const selectable = people.data?.filter(
    (p) => p.role === (kind === "advance" ? "WORKER" : category),
  );
  async function save() {
    const value = normalizeMoney(amount);
    const common = {
      amount: value,
      project_id: project || null,
      note: note.trim() || null,
    };
    if (kind === "advance")
      await api.addAdvance({
        ...common,
        worker_id: person,
        paid_at: day,
        salary_month: month + "-01",
      });
    else if (kind === "income") {
      if (!project) throw new Error("Loyihani tanlang.");
      await api.addIncome(project, {
        amount: value,
        received_at: day,
        note: common.note,
      });
    } else
      await api.addExpense({
        ...common,
        expense_date: day,
        category,
        beneficiary_person_id: ["OWNER", "PARTNER"].includes(category)
          ? person
          : null,
      });
    await refresh();
    onClose();
  }
  return (
    <Modal
      title={
        {
          advance: "Avans berish",
          income: "Pul tushumi",
          expense: "Xarajat kiritish",
        }[kind]
      }
      onClose={onClose}
    >
      {people.isPending || projects.isPending ? (
        <Loading />
      ) : people.error || projects.error ? (
        <ErrorState
          error={(people.error || projects.error)!}
          retry={() => {
            void people.refetch();
            void projects.refetch();
          }}
        />
      ) : (
        <Form submit={save}>
          {kind === "expense" && (
            <label>
              Toifa
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value as Category);
                  setPerson("");
                }}
              >
                {Object.entries(categoryLabel).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          )}
          {(kind === "advance" ||
            (kind === "expense" &&
              ["OWNER", "PARTNER"].includes(category))) && (
            <label>
              {kind === "advance" ? "Ishchi" : "Pul oluvchi"}
              <select
                required
                value={person}
                onChange={(e) => setPerson(e.target.value)}
              >
                <option value="">Tanlang</option>
                {selectable?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              {!selectable?.length && (
                <small>
                  Avval {kind === "advance" ? "ishchi" : "hamkor"} qo'shing.
                </small>
              )}
            </label>
          )}
          <label>
            Summa, so'm
            <input
              required
              inputMode="decimal"
              placeholder="500 000"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </label>
          <label>
            Sana
            <input
              required
              type="date"
              value={day}
              onChange={(e) => setDay(e.target.value)}
            />
          </label>
          {kind === "advance" && (
            <label>
              Oylik davri
              <input
                required
                type="month"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
              />
            </label>
          )}
          <label>
            Loyiha{" "}
            {kind !== "income" && <span className="muted">(ixtiyoriy)</span>}
            <select
              required={kind === "income"}
              disabled={!!projectId}
              value={project}
              onChange={(e) => setProject(e.target.value)}
            >
              <option value="">
                {kind === "income" ? "Tanlang" : "Umumiy / loyihasiz"}
              </option>
              {projects.data?.map((p) => (
                <option key={p.project.id} value={p.project.id}>
                  {p.project.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Izoh <span className="muted">(ixtiyoriy)</span>
            <textarea
              maxLength={500}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
        </Form>
      )}
    </Modal>
  );
}

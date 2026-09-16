import { useState } from "react";
import { api } from "../../api";
import { useRefresh } from "../../hooks/data";
import type { Person } from "../../types/models";
import { normalizeMoney } from "../../utils/format";
import { Form, Modal } from "../common/ui";
export function PersonForm({
  role,
  person,
  onClose,
}: {
  role: "WORKER" | "PARTNER" | "OWNER";
  person?: Person;
  onClose: () => void;
}) {
  const [name, setName] = useState(person?.name ?? "");
  const [salary, setSalary] = useState(person?.monthly_salary ?? "");
  const [confirmed, setConfirmed] = useState(false);
  const refresh = useRefresh();
  const salaryChanged =
    !!person && role === "WORKER" && salary !== person.monthly_salary;
  async function save() {
    const amount = role === "WORKER" ? normalizeMoney(salary) : undefined;
    if (salaryChanged && !confirmed)
      throw new Error("Oylik o'zgarishini tasdiqlang.");
    if (person)
      await api.editPerson(person.id, { name, monthly_salary: amount });
    else if (role !== "OWNER")
      await api.addPerson({ name, role, monthly_salary: amount });
    await refresh();
    onClose();
  }
  return (
    <Modal
      title={
        person
          ? "Ma'lumotni tahrirlash"
          : role === "WORKER"
            ? "Ishchi qo'shish"
            : "Hamkor qo'shish"
      }
      onClose={onClose}
    >
      <Form submit={save}>
        <label>
          Ism
          <input
            required
            maxLength={120}
            autoComplete="off"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        {role === "WORKER" && (
          <label>
            Oylik, so'm
            <input
              required
              inputMode="decimal"
              placeholder="6 000 000"
              value={salary}
              onChange={(e) => {
                setSalary(e.target.value);
                setConfirmed(false);
              }}
            />
          </label>
        )}
        {salaryChanged && (
          <div className="notice">
            <p>
              Yangi oylik avvalgi oylarning hisob-kitoblariga ham qo'llanadi.
              Avanslar saqlanadi.
            </p>
            <label className="check">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />{" "}
              O'zgarishni tasdiqlayman
            </label>
          </div>
        )}
      </Form>
    </Modal>
  );
}

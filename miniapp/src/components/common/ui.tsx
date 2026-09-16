import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { AlertCircle, ArrowLeft, Inbox, LoaderCircle, X } from "lucide-react";
import { Link } from "react-router-dom";
import { formatMoney, monthLabel } from "../../utils/format";
export function Header({
  title,
  subtitle,
  action,
  back,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  back?: string;
}) {
  return (
    <header className="page-header">
      <div>
        {back && (
          <Link className="back-link" to={back}>
            <ArrowLeft size={17} /> Orqaga
          </Link>
        )}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}
export function Loading() {
  return (
    <div className="skeletons" role="status" aria-label="Yuklanmoqda">
      <div />
      <div />
      <div />
    </div>
  );
}
export function ErrorState({
  error,
  retry,
}: {
  error: Error;
  retry?: () => void;
}) {
  return (
    <div className="empty error" role="alert">
      <AlertCircle />
      <h3>Ma'lumot yuklanmadi</h3>
      <p>{error.message}</p>
      {retry && (
        <button className="secondary" onClick={retry}>
          Qayta urinish
        </button>
      )}
    </div>
  );
}
export function Empty({
  text = "Hozircha ma'lumot yo'q.",
  action,
}: {
  text?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <Inbox />
      <p>{text}</p>
      {action}
    </div>
  );
}
export function Stat({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className={`stat ${accent ? "accent" : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
export function MoneyStat({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return <Stat label={label} value={formatMoney(value)} accent={accent} />;
}
export function MonthPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="filter">
      Oy
      <span className="month-control">
        <span aria-hidden="true">{monthLabel(value)}</span>
        <input
          aria-label="Oy"
          type="month"
          required
          value={value}
          onChange={(e) => e.target.value && onChange(e.target.value)}
        />
      </span>
    </label>
  );
}
export function Select({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  children: ReactNode;
}) {
  return (
    <label className="filter">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {children}
      </select>
    </label>
  );
}
export function Tabs({
  value,
  items,
  onChange,
}: {
  value: string;
  items: [string, string][];
  onChange: (value: string) => void;
}) {
  return (
    <div className="tabs">
      {items.map(([key, label]) => (
        <button
          key={key}
          aria-pressed={value === key}
          onClick={() => onChange(key)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  return (
    <dialog ref={dialog} onCancel={onClose} className="modal">
      <div className="modal-header">
        <h2>{title}</h2>
        <button
          type="button"
          className="icon-button"
          onClick={onClose}
          aria-label="Yopish"
        >
          <X />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function Form({
  submit,
  children,
  label = "Saqlash",
}: {
  submit: () => Promise<void>;
  children: ReactNode;
  label?: string;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await submit();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Saqlab bo'lmadi.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={onSubmit}>
      <fieldset disabled={busy}>{children}</fieldset>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <button className="primary full" disabled={busy} type="submit">
        {busy && <LoaderCircle className="spin" size={18} />}{" "}
        {busy ? "Saqlanmoqda…" : label}
      </button>
    </form>
  );
}
export function Confirm({
  title,
  description,
  confirm,
  onClose,
}: {
  title: string;
  description: string;
  confirm: () => Promise<void>;
  onClose: () => void;
}) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="muted">{description}</p>
      <Form label="Tasdiqlash" submit={confirm}>
        <button type="button" className="secondary full" onClick={onClose}>
          Bekor qilish
        </button>
      </Form>
    </Modal>
  );
}
export function Pagination({
  offset,
  total,
  limit = 30,
  onChange,
}: {
  offset: number;
  total: number;
  limit?: number;
  onChange: (v: number) => void;
}) {
  return (
    total > limit && (
      <div className="pagination">
        <button
          className="secondary"
          disabled={!offset}
          onClick={() => onChange(Math.max(0, offset - limit))}
        >
          Oldingi
        </button>
        <span>
          {offset + 1}–{Math.min(offset + limit, total)} / {total}
        </span>
        <button
          className="secondary"
          disabled={offset + limit >= total}
          onClick={() => onChange(offset + limit)}
        >
          Keyingi
        </button>
      </div>
    )
  );
}

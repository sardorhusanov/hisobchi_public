export type Money = string;
export type Role = "OWNER" | "PARTNER" | "WORKER";
export type Category = "BUSINESS" | "OWNER" | "PARTNER" | "OTHER";
export interface Person {
  id: string;
  name: string;
  role: Role;
  monthly_salary: Money | null;
  is_active: boolean;
}
export interface Identity {
  owner: Person;
  telegram_user_id: number;
  today: string;
  version: string;
}
export interface Salary {
  monthly_salary: Money;
  daily_rate: Money;
  worked_days: string;
  gross: Money;
  advances: Money;
  remaining: Money;
}
export interface WorkerSalary extends Salary {
  person: Person;
}
export interface Salaries {
  month: string;
  items: WorkerSalary[];
  worker_count: number;
  gross: Money;
  advances: Money;
  remaining: Money;
}
export type AttendanceValue = "1" | "0.5" | null;
export interface DayAttendance {
  date: string;
  items: { person: Person; value: string | null }[];
}
export interface MonthlyAttendance {
  person_id: string;
  month: string;
  worked_days: string;
  full_days: number;
  half_days: number;
  items: { date: string; value: string | null }[];
}
export interface AttendanceReport {
  month: string;
  worked_days: string;
  items: { person: Person; worked_days: string }[];
}
export interface PersonDetail {
  person: Person;
  salary: Salary | null;
  attendance: MonthlyAttendance;
}
export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: "ACTIVE" | "COMPLETED";
}
export interface ProjectSummary {
  project: Project;
  income: Money;
  expenses: Money;
  balance: Money;
}
export interface Income {
  id: string;
  project_id: string;
  amount: Money;
  received_at: string;
  note: string | null;
}
export interface Expense {
  id: string;
  project_id: string | null;
  amount: Money;
  expense_date: string;
  category: Category;
  beneficiary_person_id: string | null;
  note: string | null;
}
export interface Advance {
  id: string;
  worker_id: string;
  amount: Money;
  paid_at: string;
  salary_month: string;
  project_id: string | null;
  note: string | null;
}
export interface Page<T> {
  items: T[];
  total: number;
  amount: Money;
  offset: number;
  limit: number;
}
export interface FinanceSummary {
  income: Money;
  expenses: Money;
  business_expenses: Money;
  owner_withdrawals: Money;
  partner_withdrawals: Money;
  other_expenses: Money;
  advances: Money;
  net_cash_flow: Money;
}
export interface ChartPoint {
  date: string;
  income: Money;
  expenses: Money;
  advances: Money;
}
export interface FinanceReport {
  start: string;
  end: string;
  summary: FinanceSummary;
  chart: ChartPoint[];
}
export interface Dashboard extends Identity {
  month: string;
  summary: FinanceSummary;
  cash_flow_chart: ChartPoint[];
  attendance: { date: string; total_people: number; marked: number };
  projects: ProjectSummary[];
}
export interface PersonInput {
  name: string;
  role: "WORKER" | "PARTNER";
  monthly_salary?: Money;
}
export interface PersonPatch {
  name?: string;
  monthly_salary?: Money;
  is_active?: boolean;
}
export interface ProjectInput {
  name: string;
  description: string;
}
export interface AdvanceInput {
  worker_id: string;
  amount: Money;
  paid_at: string;
  salary_month: string;
  project_id: string | null;
  note: string | null;
}
export interface ExpenseInput {
  amount: Money;
  expense_date: string;
  category: Category;
  project_id: string | null;
  beneficiary_person_id: string | null;
  note: string | null;
}
export interface IncomeInput {
  amount: Money;
  received_at: string;
  note: string | null;
}

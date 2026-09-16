import { request, query, json } from "./client";
import type * as T from "../types/models";
export type Filters = Record<string, string | number | boolean | undefined>;
export const api = {
  me: () => request<T.Identity>("/auth/telegram", { method: "POST" }),
  dashboard: (month: string) =>
    request<T.Dashboard>("/dashboard" + query({ month })),
  people: (role?: T.Role, active = true) =>
    request<T.Person[]>("/people" + query({ role, active })),
  person: (id: string, month: string) =>
    request<T.PersonDetail>(`/people/${id}` + query({ month })),
  addPerson: (body: T.PersonInput) =>
    request<T.Person>("/people", json("POST", body)),
  editPerson: (id: string, body: T.PersonPatch) =>
    request<T.Person>(`/people/${id}`, json("PATCH", body)),
  salaries: (month: string, active = false) =>
    request<T.Salaries>("/salaries" + query({ month, active })),
  attendance: (date: string) =>
    request<T.DayAttendance>("/attendance" + query({ date })),
  saveAttendance: (
    date: string,
    items: { person_id: string; value: T.AttendanceValue }[],
  ) => request<T.DayAttendance>("/attendance", json("PUT", { date, items })),
  attendanceMonth: (person_id: string, month: string) =>
    request<T.MonthlyAttendance>(
      "/attendance/monthly" + query({ person_id, month }),
    ),
  attendanceReport: (month: string) =>
    request<T.AttendanceReport>("/attendance/report" + query({ month })),
  projects: (status: T.Project["status"] = "ACTIVE") =>
    request<T.ProjectSummary[]>("/projects" + query({ status })),
  project: (id: string) => request<T.ProjectSummary>(`/projects/${id}`),
  addProject: (body: T.ProjectInput) =>
    request<T.Project>("/projects", json("POST", body)),
  editProject: (
    id: string,
    body: Partial<T.ProjectInput> & { status?: T.Project["status"] },
  ) => request<T.Project>(`/projects/${id}`, json("PATCH", body)),
  income: (filters: Filters) =>
    request<T.Page<T.Income>>("/finance/income" + query(filters)),
  projectIncome: (id: string, offset: number) =>
    request<T.Page<T.Income>>(`/projects/${id}/income` + query({ offset })),
  projectExpenses: (id: string, offset: number) =>
    request<T.Page<T.Expense>>(`/projects/${id}/expenses` + query({ offset })),
  addIncome: (id: string, body: T.IncomeInput) =>
    request<T.Income>(`/projects/${id}/income`, json("POST", body)),
  expenses: (filters: Filters) =>
    request<T.Page<T.Expense>>("/expenses" + query(filters)),
  addExpense: (body: T.ExpenseInput) =>
    request<T.Expense>("/expenses", json("POST", body)),
  advances: (filters: Filters) =>
    request<T.Page<T.Advance>>("/advances" + query(filters)),
  cashAdvances: (filters: Filters) =>
    request<T.Page<T.Advance>>("/finance/advances" + query(filters)),
  addAdvance: (body: T.AdvanceInput) =>
    request<T.Advance>("/advances", json("POST", body)),
  deleteAdvance: (id: string) =>
    request<void>(`/advances/${id}`, { method: "DELETE" }),
  finance: (filters: Filters) =>
    request<T.FinanceReport>("/finance/summary" + query(filters)),
};

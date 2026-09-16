import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { Empty, Loading } from "../components/common/ui";
const Dashboard = lazy(() => import("../pages/Dashboard"));
const Attendance = lazy(() => import("../pages/Attendance"));
const Workers = lazy(() => import("../pages/Workers"));
const Partners = lazy(() => import("../pages/Partners"));
const WorkerDetails = lazy(() => import("../pages/WorkerDetails"));
const Salary = lazy(() => import("../pages/Salary"));
const Advances = lazy(() => import("../pages/Advances"));
const Projects = lazy(() => import("../pages/Projects"));
const ProjectDetails = lazy(() => import("../pages/ProjectDetails"));
const Finance = lazy(() => import("../pages/Finance"));
const Reports = lazy(() => import("../pages/Reports"));
const Settings = lazy(() => import("../pages/Settings"));
const More = lazy(() => import("../pages/More"));
export default function Router() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="attendance" element={<Attendance />} />
          <Route path="workers" element={<Workers />} />
          <Route path="partners" element={<Partners />} />
          <Route path="people/:id" element={<WorkerDetails />} />
          <Route path="salary" element={<Salary />} />
          <Route path="advances" element={<Advances />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectDetails />} />
          <Route path="finance" element={<Finance />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
          <Route path="more" element={<More />} />
          <Route path="*" element={<Empty text="Sahifa topilmadi." />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

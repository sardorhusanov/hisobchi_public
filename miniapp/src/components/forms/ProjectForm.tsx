import { useState } from "react";
import { api } from "../../api";
import { useRefresh } from "../../hooks/data";
import type { Project } from "../../types/models";
import { Form, Modal } from "../common/ui";
export function ProjectForm({
  project,
  onClose,
}: {
  project?: Project;
  onClose: () => void;
}) {
  const [name, setName] = useState(project?.name ?? "");
  const [description, setDescription] = useState(project?.description ?? "");
  const refresh = useRefresh();
  return (
    <Modal
      title={project ? "Loyihani tahrirlash" : "Loyiha qo'shish"}
      onClose={onClose}
    >
      <Form
        submit={async () => {
          if (project) await api.editProject(project.id, { name, description });
          else await api.addProject({ name, description });
          await refresh();
          onClose();
        }}
      >
        <label>
          Loyiha nomi
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength={120}
          />
        </label>
        <label>
          Tavsif <span className="muted">(ixtiyoriy)</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={1000}
          />
        </label>
      </Form>
    </Modal>
  );
}

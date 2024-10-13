interface ProjectSelectorProps {
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onAddNewProject: () => void;
}

const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  projects,
  selectedProjectId,
  onSelectProject,
  onAddNewProject
}) => {
  return (
    <div>
      <select
        value={selectedProjectId || ''}
        onChange={(e) => onSelectProject(Number(e.target.value))}
      >
        <option value="">Select a project</option>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
      <button onClick={onAddNewProject}>Add New Project</button>
    </div>
  );
};

export default ProjectSelector;

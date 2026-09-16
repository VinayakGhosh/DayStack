import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { projectsApi, Project } from '@/lib/api';
import { Plus, FolderKanban } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ProjectCard from '@/components/projects/ProjectCard';
import ProjectModal from '@/components/projects/ProjectModal';
import { useToast } from '@/hooks/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';


const ProjectsPage = () => {
  const { toast } = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProjects = async () => {
    const { data, error } = await projectsApi.getAll();
    if (data) {
      setProjects(data);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async (data: { name: string; description?: string }) => {
    setIsSubmitting(true);
    const { data: newProject, error } = await projectsApi.create(data);
    setIsSubmitting(false);

    if (newProject) {
      setProjects([newProject, ...projects]);
      setModalOpen(false);
      toast({ title: 'Project created successfully' });
    } if (error) {
      console.log('error is', error)
      toast({ title: error });
    }
  };

  const handleEdit = async (data: { name: string; description?: string }) => {
    if (!editingProject) return;
    setIsSubmitting(true);
    const { data: updatedProject, error } = await projectsApi.update(editingProject.project_id, data);
    setIsSubmitting(false);

    if (updatedProject) {
      setProjects(projects.map((p) => (p.project_id === editingProject.project_id ? updatedProject : p)));
      setEditingProject(null);
      toast({ title: 'Project updated successfully' });
    } else if (error) {
      toast({ title: 'Failed to update project', description: error, variant: 'destructive' });
    }
  };

  const handleDelete = async () => {
    if (!deletingProject) return;
    const { error } = await projectsApi.delete(deletingProject.project_id);

    if (!error) {
      setProjects(projects.filter((p) => p.project_id !== deletingProject.project_id));
      toast({ title: 'Project deleted successfully' });
    } else {
      toast({ title: 'Failed to delete project', description: error, variant: 'destructive' });
    }
    setDeletingProject(null);
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Projects</h1>
            <p className="text-muted-foreground mt-1">
              Manage and organize your projects
            </p>
          </div>
          <Button onClick={() => setModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </div>

        {/* Projects Grid */}
        {projects.length === 0 ? (
          <div className="text-center py-16">
            <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
              <FolderKanban className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">No projects yet</h3>
            <p className="text-muted-foreground mb-4">
              Get started by creating your first project
            </p>
            <Button onClick={() => setModalOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Project
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.project_id}
                project={project}
                onEdit={(p) => setEditingProject(p)}
                onDelete={(p) => setDeletingProject(p)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <ProjectModal
        open={modalOpen || !!editingProject}
        onClose={() => {
          setModalOpen(false);
          setEditingProject(null);
        }}
        onSubmit={editingProject ? handleEdit : handleCreate}
        project={editingProject}
        isLoading={isSubmitting}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deletingProject} onOpenChange={() => setDeletingProject(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deletingProject?.name}"? This action cannot be
              undone and all tasks in this project will be deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DashboardLayout>
  );
};

export default ProjectsPage;

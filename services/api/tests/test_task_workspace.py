import unittest
from uuid import uuid4

from task_workspace.service import TaskWorkspace


class InMemoryWorkspaceRepository:
    def __init__(self):
        self.projects = {}

    def list_projects(self, member_id):
        return [project for project in self.projects.values() if project["member_id"] == member_id]

    def create_project(self, member_id, name, description):
        project = {
            "project_id": uuid4(),
            "member_id": member_id,
            "name": name,
            "description": description,
        }
        self.projects[project["project_id"]] = project
        return project

    def update_project(self, member_id, project_id, name, description):
        project = self.projects[project_id]
        if project["member_id"] != member_id:
            raise PermissionError("Not authorized to access this project")
        if name is not None:
            project["name"] = name
        if description is not None:
            project["description"] = description
        return project

    def delete_project(self, member_id, project_id):
        project = self.projects[project_id]
        if project["member_id"] != member_id:
            raise PermissionError("Not authorized to access this project")
        del self.projects[project_id]

    def attachment_keys_for_project(self, member_id, project_id):
        project = self.projects[project_id]
        if project["member_id"] != member_id:
            raise PermissionError("Not authorized to access this project")
        return []

    def move_task_to_status(self, member_id, task_id, status_id):
        return {
            "task_id": task_id,
            "status_id": status_id,
            "status_name": "In Progress",
            "member_id": member_id,
        }


class TaskWorkspaceTests(unittest.TestCase):
    def test_member_sees_only_their_projects_and_empty_collections_are_valid(self):
        repository = InMemoryWorkspaceRepository()
        workspace = TaskWorkspace(repository)
        first_member = uuid4()
        second_member = uuid4()

        self.assertEqual(workspace.list_projects(first_member), [])

        project = workspace.create_project(first_member, "Client launch", "Prepare the launch")

        self.assertEqual(workspace.list_projects(first_member), [project])
        self.assertEqual(workspace.list_projects(second_member), [])

    def test_member_moves_a_task_through_the_workspace(self):
        repository = InMemoryWorkspaceRepository()
        workspace = TaskWorkspace(repository)
        member_id = uuid4()
        task_id = uuid4()
        status_id = uuid4()

        result = workspace.move_task_to_status(member_id, task_id, status_id)

        self.assertEqual(result["task_id"], task_id)
        self.assertEqual(result["status_id"], status_id)
        self.assertEqual(result["status_name"], "In Progress")
        self.assertEqual(result["member_id"], member_id)

    def test_member_can_update_and_delete_their_project_through_the_workspace(self):
        repository = InMemoryWorkspaceRepository()
        workspace = TaskWorkspace(repository)
        member_id = uuid4()
        project = workspace.create_project(member_id, "Client launch", None)

        updated = workspace.update_project(member_id, project["project_id"], "Product launch", None)
        workspace.delete_project(member_id, project["project_id"])

        self.assertEqual(updated["name"], "Product launch")
        self.assertEqual(workspace.list_projects(member_id), [])

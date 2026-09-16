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

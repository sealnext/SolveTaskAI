from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.repository.project_repository import ProjectRepository
from app.schema.project import ProjectCreate, ProjectUpdate, Project
from app.model.project import ProjectDB
from fastapi import HTTPException
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
    ):
        self.project_repository = project_repository

    async def get_all_for_user(self, user_id: int) -> List[Project]:
        projects_db = await self.project_repository.get_all_for_user(user_id)
        return [Project.model_validate(p) for p in projects_db]

    async def _handle_existing_project(
        self, existing_project: ProjectDB, project_data: ProjectCreate, user_id: int
    ) -> ProjectDB:
        """Handles logic when a project with unique attributes already exists."""
        logger.info(
            f"Project with key {project_data.key} already exists (ID: {existing_project.id}). Checking user link."
        )
        is_linked = await self.project_repository.check_user_project_link(
            user_id=user_id, project_id=existing_project.id
        )
        if is_linked:
            logger.warning(
                f"User {user_id} is already linked to existing project {existing_project.id}."
            )
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"You are already associated with project '{existing_project.name}'.",
            )

        logger.info(
            f"Linking user {user_id} to existing project {existing_project.id}."
        )
        await self.project_repository.link_user_to_project(
            user_id=user_id, project_id=existing_project.id
        )
        if project_data.api_key_id:
            await self.project_repository.link_api_key_to_project(
                api_key_id=project_data.api_key_id, project_id=existing_project.id
            )

        final_project_db = (
            await self.project_repository.get_project_by_id_with_relations(
                project_id=existing_project.id
            )
        )
        if not final_project_db:
            logger.error(
                f"Failed to retrieve project {existing_project.id} after linking user {user_id}."
            )
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve project after linking user.",
            )
        return final_project_db

    async def _create_new_project(
        self, project_data: ProjectCreate, user_id: int
    ) -> ProjectDB:
        """Handles logic for creating a new project."""
        logger.info(f"Creating new project '{project_data.name}' for user {user_id}.")
        if not project_data.api_key_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="API Key ID is required to create a new project.",
            )

        db_project_data = project_data.model_dump(exclude={"api_key_id"})

        new_project_db = await self.project_repository._add_project_db(
            project_data=db_project_data
        )
        logger.info(f"Created new project record with ID: {new_project_db.id}")

        await self.project_repository.link_user_to_project(
            user_id=user_id, project_id=new_project_db.id
        )

        await self.project_repository.link_api_key_to_project(
            api_key_id=project_data.api_key_id, project_id=new_project_db.id
        )

        final_project_db = (
            await self.project_repository.get_project_by_id_with_relations(
                project_id=new_project_db.id
            )
        )
        if not final_project_db:
            logger.error(
                f"Failed to retrieve newly created project {new_project_db.id}."
            )
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve newly created project.",
            )
        return final_project_db

    async def save_project(self, project_data: ProjectCreate, user_id: int) -> Project:
        """
        Saves a new project or links the user to an existing one.
        Handles project existence checks, user/API key linking, and transactions.
        """
        try:
            existing_project = (
                await self.project_repository.get_project_by_unique_attributes(
                    name=project_data.name,
                    service_type=project_data.service_type,
                    key=project_data.key,
                )
            )

            if existing_project:
                final_project_db = await self._handle_existing_project(
                    existing_project, project_data, user_id
                )
            else:
                final_project_db = await self._create_new_project(
                    project_data, user_id
                )

            return Project.model_validate(final_project_db)

        except IntegrityError as e:
            error_detail = f"Database integrity error: {e}"
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            error_str = str(e).lower()

            if "unique constraint" in error_str:
                status_code = HTTP_409_CONFLICT
                if "user_project_association" in error_str:
                    error_detail = (
                        f"User {user_id} is already linked to this project."
                    )
                elif (
                    "projects_name_service_type_key_key" in error_str
                ):
                    error_detail = f"A project with the name '{project_data.name}', service type '{project_data.service_type}', and key '{project_data.key}' already exists."
                else:
                    error_detail = (
                        "A project with conflicting details already exists."
                    )

            elif "foreign key constraint" in error_str:
                status_code = HTTP_400_BAD_REQUEST
                if "api_keys" in error_str:
                    error_detail = (
                        f"Invalid API Key ID '{project_data.api_key_id}' provided."
                    )
                elif "users" in error_str:
                    error_detail = f"Invalid User ID '{user_id}' provided."
                else:
                    error_detail = "Invalid reference provided (e.g., API Key or User not found)."

            logger.error(
                f"Database integrity error during project save: {e}", exc_info=True
            )
            raise HTTPException(status_code=status_code, detail=error_detail) from e

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during project save: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred during project saving.",
            ) from e

    async def get_project_by_id(self, user_id: int, project_id: int) -> Project:
        project_db = await self.project_repository.get_by_id(user_id, project_id)
        if not project_db:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )

        return Project.model_validate(project_db)

    # TODO: check if user_id is needed or not - Likely not needed if external_id is globally unique
    async def get_project_by_external_id(
        self, external_project_id: int
    ) -> Optional[Project]:
        project_db = await self.project_repository.get_by_external_id(
            external_project_id
        )
        if not project_db:
            return None
        return Project.model_validate(project_db)

    async def delete_project_by_external_id(
        self, user_id: int, external_project_id: int
    ) -> bool:
        """
        Deletes the user's link to a project identified by its external ID.
        If it's the last user, the project and associated DB resources are deleted by the repository.
        Returns the boolean result from the repository delete operation (True if project was deleted, False otherwise).
        """
        project_id = await self.project_repository.get_project_id_by_external_id(
            external_project_id
        )
        if not project_id:
            raise HTTPException(
                HTTP_404_NOT_FOUND, "Project with specified external ID not found."
            )

        # Optional: Check linkage first, although repo delete does too
        is_linked = await self.project_repository.check_user_project_link(user_id, project_id)
        if not is_linked:
             raise HTTPException(HTTP_404_NOT_FOUND, "User is not associated with this project.")

        try:
            # Call repository delete, which handles unlinking and potential project deletion
            # It returns True if the project record itself was deleted.
            project_was_deleted = await self.project_repository.delete(
                user_id=user_id, project_id=project_id
            )

            if project_was_deleted:
                 logger.info(f"Project {project_id} (External: {external_project_id}) deleted by repository.")
            else:
                 logger.info(f"User {user_id} unlinked from project {project_id} (External: {external_project_id}). Project remains.")

            # Return the status from the repository operation
            return project_was_deleted

        except HTTPException:
            # Re-raise specific HTTP exceptions if needed (though repo delete doesn't raise them now)
            raise
        except Exception as e:
            # Catch unexpected errors during the process
            logger.error(
                f"Unexpected error during project deletion for external ID {external_project_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                HTTP_500_INTERNAL_SERVER_ERROR, "Failed to complete project deletion operation."
            ) from e


    async def is_project_still_in_use(self, external_project_id: int) -> bool:
        project_id = await self.project_repository.get_project_id_by_external_id(
            external_project_id
        )
        if not project_id:
            raise HTTPException(
                HTTP_404_NOT_FOUND, "Project with specified external ID not found."
            )

        return await self.project_repository.is_project_associated(project_id)

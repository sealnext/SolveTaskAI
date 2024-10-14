from repositories.apikey_repository import APIKeyRepository
from validation_models.api_key_schema import APIKeyCreate, APIKeyResponse
from models.apikey import APIKey
from exceptions import APIKeyAlreadyExistsError

class APIKeyService:
    def __init__(self, apikey_repository: APIKeyRepository):
        self.apikey_repository = apikey_repository

    async def create_api_key(self, user_id: int, api_key_data: APIKeyCreate) -> APIKeyResponse:
        # Verifică dacă există deja o cheie API cu aceeași valoare
        existing_key = await self.apikey_repository.get_api_key_by_value(api_key_data.api_key)
        if existing_key:
            raise APIKeyAlreadyExistsError("An API key with this value already exists")

        new_api_key = APIKey(
            user_id=user_id,
            service_type=api_key_data.service_type,
            api_key=api_key_data.api_key,
            domain=api_key_data.domain,
            domain_email=api_key_data.domain_email
        )
        created_key = await self.apikey_repository.create_api_key(new_api_key)
        return APIKeyResponse.model_validate(created_key)

    async def get_api_keys_by_user(self, user_id: int) -> list[APIKeyResponse]:
        api_keys = await self.apikey_repository.get_api_keys_by_user(user_id)
        return [APIKeyResponse.model_validate(key) for key in api_keys]

    async def delete_api_key(self, user_id: int, api_key_id: int):
        await self.apikey_repository.delete_api_key(user_id, api_key_id)

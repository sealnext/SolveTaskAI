from logging import getLogger

from fastapi import APIRouter, HTTPException, status

from app.dependency import HealthServiceDep

logger = getLogger(__name__)

router = APIRouter()


@router.get(
	'/',
	summary='Performs health checks on the backend dependencies',
	responses={
		status.HTTP_200_OK: {'description': 'Dependencies are healthy'},
		status.HTTP_503_SERVICE_UNAVAILABLE: {
			'description': 'One or more dependencies is unhealthy'
		},
	},
)
async def health(health_service: HealthServiceDep):
	is_db_healthy = await health_service.check_db_health()
	is_redis_healthy = await health_service.check_redis_health()

	if is_db_healthy and is_redis_healthy:
		return {'status': 'ok'}
	else:
		details = {}
		if not is_db_healthy:
			details['database'] = 'unhealthy'
		if not is_redis_healthy:
			details['redis'] = 'unhealthy'

		raise HTTPException(
			status.HTTP_503_SERVICE_UNAVAILABLE, {'status': 'unhealthy', 'dependencies': details}
		)

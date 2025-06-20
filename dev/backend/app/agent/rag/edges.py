from app.misc.logger import logger

RETRIES_ALLOWED = 2


def decide_after_grading(state):
	"""
	Determines whether to retry document retrieval or end the process

	Args:
	    state (dict): The current graph state

	Returns:
	    str: Decision for next node to call
	"""
	logger.info('---ASSESS GRADED DOCUMENTS---')
	documents = state.get('documents', [])
	retry_retrieve_count = state.get('retry_retrieve_count', 0)

	if not documents and retry_retrieve_count < RETRIES_ALLOWED:
		logger.info('---DECISION: NO RELEVANT DOCUMENTS FOUND, RETRY RETRIEVAL---')
		return 'retry'

	if not documents:
		logger.info('---DECISION: MAX RETRIES REACHED---')
		return 'max retries'

	logger.info('---DECISION: %s RELEVANT DOCUMENTS FOUND, END PROCESS---', len(documents))
	return 'generate'

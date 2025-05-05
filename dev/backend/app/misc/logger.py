import datetime
import logging

from fastapi.logger import logger


# ANSI color codes with styles
class Colors:
	# Reset
	RESET = '\033[0m'

	# Regular colors
	BLACK = '\033[30m'
	RED = '\033[31m'
	GREEN = '\033[32m'
	YELLOW = '\033[33m'
	BLUE = '\033[34m'
	MAGENTA = '\033[35m'
	CYAN = '\033[36m'
	WHITE = '\033[37m'

	# Bold
	BOLD_RED = '\033[1;31m'
	BOLD_GREEN = '\033[1;32m'
	BOLD_YELLOW = '\033[1;33m'
	BOLD_BLUE = '\033[1;34m'

	# Background
	BG_RED = '\033[41m'
	BG_GREEN = '\033[42m'


# Custom formatter with enhanced colors and formatting
class EnhancedColoredFormatter(logging.Formatter):
	LEVEL_FORMATS = {
		'DEBUG': f'{Colors.CYAN}DEBUG{Colors.RESET}',
		'INFO': f'{Colors.GREEN}INFO{Colors.RESET}',
		'WARNING': f'{Colors.BOLD_YELLOW}WARNING{Colors.RESET}',
		'ERROR': f'{Colors.BOLD_RED}ERROR{Colors.RESET}',
		'CRITICAL': f'{Colors.BG_RED}{Colors.WHITE}CRITICAL{Colors.RESET}',
	}

	def format(self, record):
		# Create high-precision timestamp with milliseconds
		dt = datetime.datetime.fromtimestamp(record.created)
		timestamp = dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Truncate to milliseconds

		# Format level name with color
		colored_levelname = self.LEVEL_FORMATS.get(record.levelname, record.levelname)

		# Color the message based on level
		if record.levelno >= logging.ERROR:
			record.msg = f'{Colors.RED}{record.msg}{Colors.RESET}'
		elif record.levelno >= logging.WARNING:
			record.msg = f'{Colors.YELLOW}{record.msg}{Colors.RESET}'
		elif record.levelno >= logging.INFO:
			record.msg = f'{Colors.WHITE}{record.msg}{Colors.RESET}'
		else:
			record.msg = f'{Colors.CYAN}{record.msg}{Colors.RESET}'

		# Add the caller info (filepath and line number)
		filepath = record.pathname
		filename = record.filename
		file_color = Colors.BOLD_BLUE  # Define file_color here

		# Get just the directory path (without the filename)
		path_only = filepath[: -len(filename)] if filepath.endswith(filename) else ''

		# If path is too long, truncate the middle
		max_path_length = 30
		if len(path_only) > max_path_length:
			# Keep beginning and end, replace middle with ...
			truncated_path = path_only[:15] + '...' + path_only[-15:]
			path_display = f'{Colors.BLUE}{truncated_path}{Colors.RESET}'
		else:
			path_display = f'{Colors.BLUE}{path_only}{Colors.RESET}'

		# Combine path with bold filename and line number
		caller_info = f'{path_display}{file_color}{filename}{Colors.RESET}:{Colors.YELLOW}{record.lineno}{Colors.RESET}'

		# Format the log message with enhanced timestamp
		log_message = f'{Colors.MAGENTA}{timestamp}{Colors.RESET} [{colored_levelname}] {caller_info} - {record.msg}'

		# Replace the message with our custom formatted one
		record.msg = log_message
		record.levelname = ''  # Clear levelname since we included it in the message

		return super().format(record)


# Configure logger
handler = logging.StreamHandler()
formatter = EnhancedColoredFormatter('%(levelname)s%(message)s')
handler.setFormatter(formatter)

# Replace logger handlers and set level
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)  # Set to DEBUG to see all levels

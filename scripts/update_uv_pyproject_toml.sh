#!/bin/bash

PROJECT_ROOT="$(realpath "$(dirname "$0")/..")"

PYPROJECT_TOML_PATH="$(find "$PROJECT_ROOT" -name "pyproject.toml" -print -quit)"

if [ -z "$PYPROJECT_TOML_PATH" ]; then
	echo "pyproject.toml not found"
	exit 1
fi

# Extract main dependencies
DEPS=$(awk '
BEGIN { 
	in_deps = 0; 
	bracket_count = 0;
}

# Identify the main dependencies section
/dependencies = \[/ && !/dependency-groups/ { 
	in_deps = 1; 
	bracket_count = 1;
	next; 
}

# Exit dependency section when we hit dependency-groups
/\[dependency-groups\]/ { in_deps = 0; }

# Count opening brackets
/\[/ && in_deps { 
	bracket_count += gsub(/\[/, "[");
}

# Count closing brackets
/\]/ && in_deps { 
	bracket_count -= gsub(/\]/, "]");
	if (bracket_count == 0) {
		in_deps = 0;
	}
}

# Process dependencies
in_deps && /^[ \t]*"[^"]+"/ { 
	if (match($0, /"([^"]+)"/)) {
		full_dep = substr($0, RSTART+1, RLENGTH-2);
		# Extract just the package part with optional extras, but remove version constraints
		if (match(full_dep, /^([^><=~!]+)/)) {
			package_spec = substr(full_dep, RSTART, RLENGTH);
			# Remove trailing whitespace
			sub(/[ \t]*$/, "", package_spec);
			printf "%s ", package_spec;
		}
	}
}
' "$PYPROJECT_TOML_PATH")

# Extract dev dependencies
DEV_DEPS=$(awk '
BEGIN { 
	in_dev_deps = 0; 
	bracket_count = 0;
}

# Identify the dev dependencies section
/dev = \[/ { 
	in_dev_deps = 1; 
	bracket_count = 1;
	next; 
}

# Count opening brackets
/\[/ && in_dev_deps { 
	bracket_count += gsub(/\[/, "[");
}

# Count closing brackets
/\]/ && in_dev_deps { 
	bracket_count -= gsub(/\]/, "]");
	if (bracket_count == 0) {
		in_dev_deps = 0;
	}
}

# Process dev dependencies
in_dev_deps && /^[ \t]*"[^"]+"/ { 
	if (match($0, /"([^"]+)"/)) {
		full_dep = substr($0, RSTART+1, RLENGTH-2);
		# Extract just the package part with optional extras, but remove version constraints
		if (match(full_dep, /^([^><=~!]+)/)) {
			package_spec = substr(full_dep, RSTART, RLENGTH);
			# Remove trailing whitespace
			sub(/[ \t]*$/, "", package_spec);
			printf "%s ", package_spec;
		}
	}
}
' "$PYPROJECT_TOML_PATH")

# Trim trailing spaces
DEPS=$(echo "$DEPS" | sed 's/ $//')
DEV_DEPS=$(echo "$DEV_DEPS" | sed 's/ $//')

(
	cd $(dirname "$PYPROJECT_TOML_PATH")
	printf "\n[DEPENDENCIES]\n\n"
	for item in $DEPS; do
		printf "\n-- Updating: $item --\n"
		uv remove "$item"
		uv add "$item"
		printf "\n\n" 
	done

	printf "\n[DEV-DEPENDENCIES]\n\n"
	for item in $DEV_DEPS; do
		printf "\n-- Updating: $item --\n"
		uv remove --dev "$item"
		uv add --dev "$item"
		printf "\n\n" 
	done
)

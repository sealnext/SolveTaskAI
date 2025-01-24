import json
from typing import Dict, List, Any, Tuple

def extract_json_from_llm_response(content: str) -> str:
    """Extract JSON content from LLM response, handling any prefix or suffix text.
    Also handles markdown code blocks.
    
    Args:
        content: Raw LLM response that should contain JSON
        
    Returns:
        Clean JSON string
        
    Raises:
        ValueError: If no valid JSON content is found
    """
    # First try to find and extract content from code blocks
    code_block_starts = ["```json", "```"]
    for block_start in code_block_starts:
        start_idx = content.find(block_start)
        if start_idx != -1:
            # Find the end of the code block
            end_idx = content.find("```", start_idx + len(block_start))
            if end_idx != -1:
                # Extract content between the markers
                block_content = content[start_idx + len(block_start):end_idx].strip()
                if block_content:  # If we found content, try to parse it
                    try:
                        # Verify it's valid JSON
                        json.loads(block_content)
                        return block_content
                    except json.JSONDecodeError:
                        pass  # If invalid, continue searching
    
    # If no valid JSON found in code blocks, try to find JSON in the raw text
    json_start = content.find('{')
    if json_start == -1:
        raise ValueError("No JSON found in response")
    
    # Try to parse JSON starting from each { until we find valid JSON
    while json_start != -1:
        try:
            # Find matching closing brace
            stack = []
            i = json_start
            while i < len(content):
                if content[i] == '{':
                    stack.append('{')
                elif content[i] == '}':
                    if not stack:
                        break
                    stack.pop()
                    if not stack:  # Found matching brace
                        potential_json = content[json_start:i+1]
                        json.loads(potential_json)  # Validate JSON
                        return potential_json
                i += 1
            
            # If we didn't find valid JSON, try next {
            json_start = content.find('{', json_start + 1)
        except json.JSONDecodeError:
            # Try next {
            json_start = content.find('{', json_start + 1)
    
    raise ValueError("No valid JSON found in response")

def validate_field_values(parsed_response: Dict[str, Dict[str, Any]]) -> None:
    """Validate that all fields have correct confidence and validation values.
    
    Args:
        parsed_response: Dictionary of field data from LLM
        
    Raises:
        ValueError: If any field has invalid confidence or validation values
    """
    for field_name, field_data in parsed_response.items():
        if field_data["confidence"] not in ["High", "Medium", "Low"]:
            raise ValueError(f"Invalid confidence value for field {field_name}")
        if field_data["validation"] not in ["Valid", "Needs Validation"]:
            raise ValueError(f"Invalid validation value for field {field_name}")

def normalize_field_values(parsed_response: Dict[str, Dict[str, Any]]) -> None:
    """Convert any complex values (lists, dicts) to JSON strings in-place.
    
    Args:
        parsed_response: Dictionary of field data to normalize
    """
    for field_data in parsed_response.values():
        if isinstance(field_data["value"], (list, dict)):
            field_data["value"] = json.dumps(field_data["value"])
        else:
            field_data["value"] = str(field_data["value"])

def get_invalid_fields(fields_data: Dict[str, Dict[str, str]]) -> List[str]:
    """Get list of fields that still need validation.
    
    Args:
        fields_data: Dictionary of field data
        
    Returns:
        List of field names that need validation
    """
    return [
        field for field, data in fields_data.items()
        if data["validation"] == "Needs Validation"
    ]

def process_field_update(field_name: str, new_value: Any) -> Tuple[str, str]:
    """Process a field update and return the result.
    
    Args:
        field_name: Name of the field being updated
        new_value: New value to set
        
    Returns:
        Tuple of (result_message, formatted_value)
        result_message will be prefixed with ✅ for success or ❌ for failure
    """
    try:
        str_value = json.dumps(new_value) if isinstance(new_value, (list, dict)) else str(new_value)
        return f"✅ {field_name}: Updated to '{str_value}'", str_value
    except Exception as e:
        return f"❌ {field_name}: {str(e)}", ""

def format_operation_results(results: List[str], operation_type: str) -> str:
    """Format operation results into a readable message.
    
    Args:
        results: List of operation results (prefixed with ✅ or ❌)
        operation_type: Type of operation (e.g., "updated", "remapped")
        
    Returns:
        Formatted message string
        
    Raises:
        ValueError: If no successful operations were found
    """
    if not any(r.startswith("✅") for r in results):
        raise ValueError(f"No fields were {operation_type} successfully")
    return "\n".join(results)

def remap_fields(
    source_data: Dict[str, Dict[str, Any]], 
    field_mappings: Dict[str, str]
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Remap fields according to the mapping and track results.
    
    Args:
        source_data: Original field data
        field_mappings: Dictionary mapping old field names to new ones
        
    Returns:
        Tuple of (remapped data dictionary, list of result messages)
    """
    results = []
    remapped = {}
    
    # Copy unchanged fields
    for field, data in source_data.items():
        if field not in field_mappings:
            remapped[field] = data
    
    # Process remappings
    for old_field, new_field in field_mappings.items():
        if old_field not in source_data:
            results.append(f"❌ {old_field}: Source field not found")
            continue
        if not isinstance(new_field, str):
            results.append(f"❌ {old_field}: Invalid target field name")
            continue
        
        remapped[new_field] = source_data[old_field]
        results.append(f"✅ {old_field} -> {new_field}")
    
    return remapped, results

def format_json_response(data: Dict) -> str:
    """Format dictionary as indented JSON string.
    
    Args:
        data: Dictionary to format
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=2)
import json
import re
from typing import Dict, List, Any, Tuple

def extract_json_from_llm_response(content: str) -> str:
    """Extract JSON content from LLM response."""
    try:
        # delete all comments from the content
        content = re.sub(r'//.*', '', content)
        
        # First try to parse the entire content as JSON
        json.loads(content)
        return content
    except json.JSONDecodeError:
        # If that fails, try to find JSON between curly braces
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_content = content[start_idx:end_idx]
            # Validate that we extracted valid JSON
            json.loads(json_content)  # This will raise JSONDecodeError if invalid
            return json_content
            
        raise ValueError("No valid JSON found in response")

def validate_field_values(parsed_response: Dict[str, Dict[str, Any]]) -> None:
    """Validate that all fields have correct confidence and validation values.
    
    Args:
        parsed_response: Dictionary containing 'update' and 'validation' sections
        
    Raises:
        ValueError: If any field has invalid confidence or validation values
        TypeError: If response structure is invalid
    """
    if not isinstance(parsed_response, dict):
        raise TypeError(f"Expected dictionary, got {type(parsed_response)}")
        
    if "update" not in parsed_response or "validation" not in parsed_response:
        raise ValueError("Response must contain both 'update' and 'validation' sections")
        
    update_section = parsed_response["update"]
    validation_section = parsed_response["validation"]
    
    if not isinstance(update_section, dict) or not isinstance(validation_section, dict):
        raise TypeError("Both 'update' and 'validation' sections must be dictionaries")
    
    # Validate that each field in update has corresponding validation
    for field_name in update_section:
        if field_name not in validation_section:
            raise ValueError(f"Missing validation info for field '{field_name}'")
            
        field_validation = validation_section[field_name]
        if not isinstance(field_validation, dict):
            raise TypeError(f"Validation data for '{field_name}' must be a dictionary")
            
        if "confidence" not in field_validation:
            raise ValueError(f"Missing 'confidence' in validation for '{field_name}'")
            
        if "validation" not in field_validation:
            raise ValueError(f"Missing 'validation' in validation for '{field_name}'")
            
        if field_validation["confidence"] not in ["High", "Medium", "Low"]:
            raise ValueError(f"Invalid confidence value '{field_validation['confidence']}' for field '{field_name}'. Must be one of: High, Medium, Low")
            
        if field_validation["validation"] not in ["Valid", "Needs Validation"]:
            raise ValueError(f"Invalid validation value '{field_validation['validation']}' for field '{field_name}'. Must be one of: Valid, Needs Validation")

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
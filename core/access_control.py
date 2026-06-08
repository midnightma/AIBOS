from storage.database import get_unit

class AccessControl:
    @staticmethod
    def validate_source(source_id: str, requested_security_level: int) -> bool:
        unit = get_unit(source_id)
        if not unit:
            return False
        
        max_level = unit.get('max_security_level', 0)
        
        # Lower score means less risk. If the requested level exceeds max allowed level, reject.
        # Wait, security score 0-2 is safe, 9-10 is high risk.
        # So a source max_security_level=4 means they cannot approve operations rated 5 or above.
        if requested_security_level > max_level:
            return False
            
        return True
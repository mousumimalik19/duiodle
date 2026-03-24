"""
Duiodle Validator Service

Validates input data and processing parameters.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class ValidationErrorType(str, Enum):
    """Types of validation errors."""
    INVALID_FILE = "invalid_file"
    FILE_NOT_FOUND = "file_not_found"
    INVALID_FORMAT = "invalid_format"
    INVALID_THEME = "invalid_theme"
    INVALID_PRESET = "invalid_preset"
    FILE_TOO_LARGE = "file_too_large"
    INVALID_DIMENSIONS = "invalid_dimensions"


@dataclass
class ValidationError:
    """Represents a validation error."""
    error_type: ValidationErrorType
    message: str
    field: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: List[ValidationError]
    
    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, errors=[])
    
    @classmethod
    def failure(cls, errors: List[ValidationError]) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(is_valid=False, errors=errors)


class InputValidator:
    """
    Validates input parameters for the Duiodle pipeline.
    
    Checks file paths, themes, motion presets, and other
    processing parameters.
    """
    
    # Valid file extensions
    VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    
    # Valid themes
    VALID_THEMES = {
        "minimal", "professional", "aesthetic", "playful",
        "portfolio", "tropical", "gradient", "animated"
    }
    
    # Valid motion presets
    VALID_PRESETS = {
        "fade_in", "fade_in_slow", "slide_up", "slide_down",
        "slide_left", "slide_right", "scale_in", "scale_up",
        "spring_pop", "spring_bounce", "spring_gentle",
        "stagger_children", "stagger_fast"
    }
    
    # Max file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(
        self,
        max_file_size: int = MAX_FILE_SIZE,
        allowed_extensions: Optional[set] = None,
    ):
        """
        Initialize the validator.
        
        Args:
            max_file_size: Maximum allowed file size in bytes
            allowed_extensions: Set of allowed file extensions
        """
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or self.VALID_EXTENSIONS
    
    def validate_image_path(self, path: str) -> ValidationResult:
        """
        Validate an image file path.
        
        Args:
            path: Path to the image file
            
        Returns:
            ValidationResult with any errors found
        """
        errors = []
        
        # Check if path is provided
        if not path or not path.strip():
            errors.append(ValidationError(
                error_type=ValidationErrorType.INVALID_FILE,
                message="Image path is required",
                field="image_path"
            ))
            return ValidationResult.failure(errors)
        
        # Check if file exists
        if not os.path.exists(path):
            errors.append(ValidationError(
                error_type=ValidationErrorType.FILE_NOT_FOUND,
                message=f"File not found: {path}",
                field="image_path"
            ))
            return ValidationResult.failure(errors)
        
        # Check file extension
        _, ext = os.path.splitext(path)
        if ext.lower() not in self.allowed_extensions:
            errors.append(ValidationError(
                error_type=ValidationErrorType.INVALID_FORMAT,
                message=f"Invalid file format: {ext}. Allowed: {self.allowed_extensions}",
                field="image_path"
            ))
        
        # Check file size
        try:
            file_size = os.path.getsize(path)
            if file_size > self.max_file_size:
                errors.append(ValidationError(
                    error_type=ValidationErrorType.FILE_TOO_LARGE,
                    message=f"File too large: {file_size} bytes. Max: {self.max_file_size}",
                    field="image_path"
                ))
        except OSError as e:
            errors.append(ValidationError(
                error_type=ValidationErrorType.INVALID_FILE,
                message=f"Cannot read file: {str(e)}",
                field="image_path"
            ))
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success()
    
    def validate_theme(self, theme: str) -> ValidationResult:
        """
        Validate a theme name.
        
        Args:
            theme: Theme name to validate
            
        Returns:
            ValidationResult with any errors found
        """
        if not theme or theme.lower() not in self.VALID_THEMES:
            return ValidationResult.failure([
                ValidationError(
                    error_type=ValidationErrorType.INVALID_THEME,
                    message=f"Invalid theme: {theme}. Valid themes: {self.VALID_THEMES}",
                    field="theme"
                )
            ])
        
        return ValidationResult.success()
    
    def validate_motion_preset(self, preset: str) -> ValidationResult:
        """
        Validate a motion preset name.
        
        Args:
            preset: Motion preset name to validate
            
        Returns:
            ValidationResult with any errors found
        """
        if not preset or preset.lower() not in self.VALID_PRESETS:
            return ValidationResult.failure([
                ValidationError(
                    error_type=ValidationErrorType.INVALID_PRESET,
                    message=f"Invalid preset: {preset}. Valid presets: {self.VALID_PRESETS}",
                    field="motion_preset"
                )
            ])
        
        return ValidationResult.success()
    
    def validate_processing_request(
        self,
        image_path: str,
        theme: str = "minimal",
        motion_preset: str = "fade_in",
    ) -> ValidationResult:
        """
        Validate all parameters for a processing request.
        
        Args:
            image_path: Path to the image file
            theme: Theme name
            motion_preset: Motion preset name
            
        Returns:
            ValidationResult with all errors found
        """
        all_errors = []
        
        # Validate image
        image_result = self.validate_image_path(image_path)
        all_errors.extend(image_result.errors)
        
        # Validate theme
        theme_result = self.validate_theme(theme)
        all_errors.extend(theme_result.errors)
        
        # Validate motion preset
        preset_result = self.validate_motion_preset(motion_preset)
        all_errors.extend(preset_result.errors)
        
        if all_errors:
            return ValidationResult.failure(all_errors)
        
        return ValidationResult.success()


# Convenience function
def validate_request(
    image_path: str,
    theme: str = "minimal",
    motion_preset: str = "fade_in",
) -> Tuple[bool, List[str]]:
    """
    Quick validation of processing request.
    
    Args:
        image_path: Path to the image file
        theme: Theme name
        motion_preset: Motion preset name
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = InputValidator()
    result = validator.validate_processing_request(image_path, theme, motion_preset)
    
    if result.is_valid:
        return True, []
    
    return False, [err.message for err in result.errors]

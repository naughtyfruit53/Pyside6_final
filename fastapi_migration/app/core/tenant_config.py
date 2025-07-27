"""
Multi-tenant configuration management
"""
from typing import Dict, Any, Optional
from app.core.config import settings
import os
import json

class TenantConfig:
    """Configuration management for multi-tenant application"""
    
    # Default feature flags for different plan types
    PLAN_FEATURES = {
        "trial": {
            "max_users": 5,
            "storage_limit_gb": 1,
            "api_calls_per_hour": 100,
            "features": {
                "advanced_reporting": False,
                "custom_fields": False,
                "api_access": False,
                "email_notifications": True,
                "audit_logs": False,
                "custom_branding": False,
                "integrations": False,
                "backup_restore": False
            }
        },
        "basic": {
            "max_users": 10,
            "storage_limit_gb": 5,
            "api_calls_per_hour": 500,
            "features": {
                "advanced_reporting": True,
                "custom_fields": False,
                "api_access": True,
                "email_notifications": True,
                "audit_logs": True,
                "custom_branding": False,
                "integrations": False,
                "backup_restore": True
            }
        },
        "premium": {
            "max_users": 50,
            "storage_limit_gb": 25,
            "api_calls_per_hour": 2000,
            "features": {
                "advanced_reporting": True,
                "custom_fields": True,
                "api_access": True,
                "email_notifications": True,
                "audit_logs": True,
                "custom_branding": True,
                "integrations": True,
                "backup_restore": True
            }
        },
        "enterprise": {
            "max_users": 999,
            "storage_limit_gb": 100,
            "api_calls_per_hour": 10000,
            "features": {
                "advanced_reporting": True,
                "custom_fields": True,
                "api_access": True,
                "email_notifications": True,
                "audit_logs": True,
                "custom_branding": True,
                "integrations": True,
                "backup_restore": True,
                "white_label": True,
                "priority_support": True,
                "custom_integrations": True
            }
        }
    }
    
    # Security settings by plan
    SECURITY_SETTINGS = {
        "trial": {
            "session_timeout_minutes": 60,
            "password_expiry_days": 90,
            "max_login_attempts": 5,
            "require_2fa": False,
            "ip_whitelist_enabled": False
        },
        "basic": {
            "session_timeout_minutes": 120,
            "password_expiry_days": 90,
            "max_login_attempts": 5,
            "require_2fa": False,
            "ip_whitelist_enabled": False
        },
        "premium": {
            "session_timeout_minutes": 240,
            "password_expiry_days": 60,
            "max_login_attempts": 3,
            "require_2fa": True,
            "ip_whitelist_enabled": True
        },
        "enterprise": {
            "session_timeout_minutes": 480,
            "password_expiry_days": 30,
            "max_login_attempts": 3,
            "require_2fa": True,
            "ip_whitelist_enabled": True,
            "sso_enabled": True
        }
    }
    
    @classmethod
    def get_plan_config(cls, plan_type: str) -> Dict[str, Any]:
        """Get configuration for a specific plan type"""
        return cls.PLAN_FEATURES.get(plan_type, cls.PLAN_FEATURES["trial"])
    
    @classmethod
    def get_security_config(cls, plan_type: str) -> Dict[str, Any]:
        """Get security configuration for a specific plan type"""
        return cls.SECURITY_SETTINGS.get(plan_type, cls.SECURITY_SETTINGS["trial"])
    
    @classmethod
    def has_feature(cls, plan_type: str, feature_name: str) -> bool:
        """Check if a plan has a specific feature"""
        plan_config = cls.get_plan_config(plan_type)
        return plan_config.get("features", {}).get(feature_name, False)
    
    @classmethod
    def get_limit(cls, plan_type: str, limit_name: str) -> Optional[int]:
        """Get a specific limit for a plan"""
        plan_config = cls.get_plan_config(plan_type)
        return plan_config.get(limit_name)
    
    @classmethod
    def load_custom_config(cls, org_id: int) -> Dict[str, Any]:
        """Load custom configuration for an organization"""
        config_file = f"configs/org_{org_id}.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    @classmethod
    def save_custom_config(cls, org_id: int, config: Dict[str, Any]) -> bool:
        """Save custom configuration for an organization"""
        try:
            os.makedirs("configs", exist_ok=True)
            config_file = f"configs/org_{org_id}.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception:
            return False

class EnvironmentConfig:
    """Environment-specific configuration"""
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return settings.ENVIRONMENT.lower() == "development"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return settings.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_testing(cls) -> bool:
        """Check if running in testing environment"""
        return settings.ENVIRONMENT.lower() == "testing"
    
    @classmethod
    def get_log_level(cls) -> str:
        """Get appropriate log level for environment"""
        if cls.is_development():
            return "DEBUG"
        elif cls.is_testing():
            return "WARNING"
        else:
            return "INFO"
    
    @classmethod
    def should_send_emails(cls) -> bool:
        """Check if emails should be sent in current environment"""
        return not cls.is_testing() and bool(settings.SMTP_USERNAME)
    
    @classmethod
    def get_database_pool_size(cls) -> int:
        """Get appropriate database pool size for environment"""
        if cls.is_production():
            return 20
        elif cls.is_development():
            return 5
        else:
            return 2

# Validation rules for organization data
ORGANIZATION_VALIDATION = {
    "name": {
        "min_length": 2,
        "max_length": 100,
        "required": True
    },
    "subdomain": {
        "min_length": 3,
        "max_length": 50,
        "pattern": r"^[a-z0-9-]+$",
        "required": True,
        "reserved": ["www", "api", "admin", "mail", "ftp", "blog", "shop", "app"]
    },
    "primary_email": {
        "required": True,
        "format": "email"
    },
    "primary_phone": {
        "required": True,
        "min_length": 10,
        "max_length": 15
    }
}

# Default settings for new organizations
DEFAULT_ORG_SETTINGS = {
    "timezone": "Asia/Kolkata",
    "currency": "INR",
    "date_format": "DD/MM/YYYY",
    "financial_year_start": "04/01",
    "language": "en",
    "theme": "light"
}

# Allowed file types and sizes
FILE_UPLOAD_CONFIG = {
    "logos": {
        "allowed_types": ["image/jpeg", "image/png", "image/gif"],
        "max_size_mb": 5
    },
    "documents": {
        "allowed_types": ["application/pdf", "image/jpeg", "image/png"],
        "max_size_mb": 10
    },
    "imports": {
        "allowed_types": ["text/csv", "application/vnd.ms-excel", 
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        "max_size_mb": 50
    }
}
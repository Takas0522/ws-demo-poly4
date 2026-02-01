"""ServiceAssignment Model テスト"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.service_assignment import ServiceAssignment


class Test正常系:
    """正常系テスト"""
    
    def test_should_create_assignment_with_valid_data(self, test_assignment):
        """MT_SA001: 有効なServiceAssignmentモデルが作成できる"""
        # Arrange
        # Act
        assignment = ServiceAssignment(**test_assignment)
        
        # Assert
        assert assignment.tenant_id == "tenant_acme"
        assert assignment.service_id == "file-service"
        assert assignment.status == "active"
    
    def test_should_create_assignment_without_config(self):
        """MT_SA002: configがNoneでも作成できる"""
        # Arrange
        # Act
        assignment = ServiceAssignment(
            id="assignment_tenant_test_service-test",
            tenant_id="tenant_test",
            service_id="service-test",
            status="active",
            assigned_at=datetime.utcnow(),
            assigned_by="user_test"
        )
        
        # Assert
        assert assignment.config is None


class Test異常系:
    """異常系テスト"""
    
    def test_should_raise_validation_error_when_tenant_id_has_invalid_format(self):
        """MT_SA003: tenant_idが不正な形式でエラー"""
        # Arrange
        # Act & Assert
        with pytest.raises(ValidationError):
            ServiceAssignment(
                id="assignment_invalid_service-test",
                tenant_id="invalid_tenant",
                service_id="service-test",
                status="active",
                assigned_at=datetime.utcnow(),
                assigned_by="user_test"
            )
    
    def test_should_raise_validation_error_when_service_id_has_invalid_format(self):
        """MT_SA004: service_idが不正な形式でエラー"""
        # Arrange
        # Act & Assert
        with pytest.raises(ValidationError):
            ServiceAssignment(
                id="assignment_tenant_test_INVALID",
                tenant_id="tenant_test",
                service_id="INVALID_SERVICE",
                status="active",
                assigned_at=datetime.utcnow(),
                assigned_by="user_test"
            )
    
    def test_should_raise_validation_error_when_status_is_invalid(self):
        """MT_SA005: statusが不正な値でエラー"""
        # Arrange
        # Act & Assert
        with pytest.raises(ValidationError):
            ServiceAssignment(
                id="assignment_tenant_test_service-test",
                tenant_id="tenant_test",
                service_id="service-test",
                status="invalid_status",
                assigned_at=datetime.utcnow(),
                assigned_by="user_test"
            )


class Test境界値:
    """境界値テスト"""
    
    def test_should_accept_id_with_255_characters(self):
        """MT_SA006: idが255文字でOK"""
        # Arrange
        long_id = "a" * 255
        
        # Act
        assignment = ServiceAssignment(
            id=long_id,
            tenant_id="tenant_test",
            service_id="service-test",
            status="active",
            assigned_at=datetime.utcnow(),
            assigned_by="user_test"
        )
        
        # Assert
        assert len(assignment.id) == 255
    
    def test_should_raise_validation_error_when_id_exceeds_255_characters(self):
        """MT_SA007: idが256文字でエラー"""
        # Arrange
        long_id = "a" * 256
        
        # Act & Assert
        with pytest.raises(ValidationError):
            ServiceAssignment(
                id=long_id,
                tenant_id="tenant_test",
                service_id="service-test",
                status="active",
                assigned_at=datetime.utcnow(),
                assigned_by="user_test"
            )

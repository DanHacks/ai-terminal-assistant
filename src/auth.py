"""
ElectroPOS - Authentication Module
Employee PIN-based authentication and role management.
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from models import Employee, EmployeeRole
from database import get_session, hash_pin, verify_pin


class AuthManager:
    """Handles employee authentication and session management."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        self.current_employee = None
        security = self.settings.get("security", {})
        self.max_attempts = security.get("max_login_attempts", 3)

    def login(self, employee_id_or_name: str, pin: str) -> dict:
        session = get_session()
        try:
            employee = (
                session.query(Employee)
                .filter(
                    (Employee.employee_id == employee_id_or_name) |
                    (Employee.first_name == employee_id_or_name)
                )
                .filter(Employee.is_active == True)
                .first()
            )

            if not employee:
                return {"success": False, "error": "Employee not found or inactive."}

            if employee.login_attempts >= self.max_attempts:
                return {"success": False, "error": "Account locked. Too many failed attempts. Contact admin."}

            if not verify_pin(pin, employee.pin_hash):
                employee.login_attempts += 1
                session.commit()
                remaining = self.max_attempts - employee.login_attempts
                return {"success": False, "error": f"Invalid PIN. {remaining} attempts remaining."}

            employee.login_attempts = 0
            employee.last_login = datetime.now(timezone.utc)
            session.commit()

            self.current_employee = {
                "id": employee.id,
                "employee_id": employee.employee_id,
                "name": employee.full_name,
                "role": employee.role,
                "email": employee.email,
            }

            return {"success": True, "employee": self.current_employee}
        finally:
            session.close()

    def logout(self):
        name = self.current_employee["name"] if self.current_employee else "Unknown"
        self.current_employee = None
        return name

    def is_logged_in(self) -> bool:
        return self.current_employee is not None

    def get_current_employee(self) -> dict:
        return self.current_employee

    def has_role(self, *roles: EmployeeRole) -> bool:
        if not self.current_employee:
            return False
        return self.current_employee["role"] in roles

    def is_admin(self) -> bool:
        return self.has_role(EmployeeRole.ADMIN)

    def is_manager_or_above(self) -> bool:
        return self.has_role(EmployeeRole.ADMIN, EmployeeRole.MANAGER)

    def require_role(self, *roles: EmployeeRole) -> bool:
        if not self.is_logged_in():
            return False
        return self.has_role(*roles)

    def unlock_employee(self, employee_id: str) -> dict:
        if not self.is_admin():
            return {"success": False, "error": "Admin access required."}

        session = get_session()
        try:
            employee = session.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                return {"success": False, "error": "Employee not found."}
            employee.login_attempts = 0
            session.commit()
            return {"success": True, "message": f"Account unlocked for {employee.full_name}."}
        finally:
            session.close()

    def change_pin(self, employee_id: str, old_pin: str, new_pin: str) -> dict:
        session = get_session()
        try:
            employee = session.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                return {"success": False, "error": "Employee not found."}
            if not verify_pin(old_pin, employee.pin_hash):
                return {"success": False, "error": "Current PIN is incorrect."}
            if len(new_pin) < 4:
                return {"success": False, "error": "New PIN must be at least 4 digits."}
            employee.pin_hash = hash_pin(new_pin)
            session.commit()
            return {"success": True, "message": "PIN changed successfully."}
        finally:
            session.close()

    def list_employees(self) -> list:
        session = get_session()
        try:
            employees = session.query(Employee).filter(Employee.is_active == True).all()
            return [
                {
                    "id": e.id,
                    "employee_id": e.employee_id,
                    "name": e.full_name,
                    "role": e.role.value,
                    "email": e.email,
                    "last_login": str(e.last_login) if e.last_login else "Never",
                }
                for e in employees
            ]
        finally:
            session.close()

    def create_employee(self, first_name: str, last_name: str, pin: str,
                        role: str = "cashier", email: str = None, phone: str = None) -> dict:
        if not self.is_admin():
            return {"success": False, "error": "Admin access required."}

        session = get_session()
        try:
            role_enum = EmployeeRole(role)
            employee = Employee(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                pin_hash=hash_pin(pin),
                role=role_enum,
            )
            session.add(employee)
            session.commit()
            return {
                "success": True,
                "employee_id": employee.employee_id,
                "message": f"Employee {employee.full_name} created with ID {employee.employee_id}."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

# backend/src/models/__init__.py

from .base import Base
from .role import Role
from .user import User
from .section import Section
from .line import Line
from .machine import Machine
from .supplier import Supplier
from .inventory import Inventory
from .format import Format
from .warehouse import Warehouse
from .work_order import WorkOrder, FailureCode, CauseCode, RemedyCode
from .maintenance import Maintenance
from .document import Document
from .supplier_product_price import SupplierProductPrice
from .task_list import TaskList
from .task_step import TaskStep
from .shift_pattern import ShiftPattern
from .shift_assignment import ShiftAssignment
from .absence import Absence
from .shift_override import ShiftOverride
from .maintenance_backlog import MaintenanceBacklog, BacklogPriority, BacklogStatus
from .vacation_request import VacationRequest
from .alert import Alert
from .work_order_technician import WorkOrderTechnician
from .gamification import (
    Achievement, 
    UserPoints, 
    PointTransaction, 
    UserAchievement,
    Challenge, 
    ChallengeParticipation,
    AchievementType, 
    BadgeRarity
)

# ✅ AÑADIDOS LOS DOS IMPORTS QUE FALTABAN PARA SOLUCIONAR EL ERROR
from .audit_log import AuditLog
from .checklist_progress import ChecklistProgress
from .work_order_material import WorkOrderMaterial
from .maintenance_request import MaintenanceRequest

# scripts/migrate_technicians.py (Versión final con todos los imports)

from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models.work_order import WorkOrder
from src.models.work_order_technician import WorkOrderTechnician
from src.models.user import User
from src.models.audit_log import AuditLog
from src.models.checklist_progress import ChecklistProgress # ✅ AÑADIDO: Resuelve el último error

def run_migration(db: Session):
    """
    Busca órdenes con un técnico asignado en el campo antiguo (`assigned_to_id`)
    pero sin una entrada correspondiente en la tabla nueva (`work_order_technicians`)
    y crea esa entrada.
    """
    print("Iniciando migración de técnicos asignados...")

    orders_to_migrate = db.query(WorkOrder).filter(WorkOrder.assigned_to_id != None).all()
    
    if not orders_to_migrate:
        print("No se encontraron órdenes para migrar. Todo parece estar correcto.")
        return

    print(f"Se encontraron {len(orders_to_migrate)} órdenes con asignación antigua para revisar.")
    
    migrated_count = 0
    already_ok_count = 0
    
    for order in orders_to_migrate:
        existing_assignment = db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == order.id,
            WorkOrderTechnician.user_id == order.assigned_to_id
        ).first()
        
        if not existing_assignment:
            print(f"  -> Arreglando Orden ID {order.id}: Asignando técnico ID {order.assigned_to_id} al nuevo sistema.")
            new_assignment = WorkOrderTechnician(
                work_order_id=order.id,
                user_id=order.assigned_to_id,
                role='principal',
                assigned_by_id=1,
                notes='Asignación migrada desde el sistema antiguo.'
            )
            db.add(new_assignment)
            migrated_count += 1
        else:
            already_ok_count += 1
            
    if migrated_count > 0:
        print(f"Se van a guardar {migrated_count} nuevas asignaciones en la base de datos...")
        db.commit()
        print("¡Cambios guardados!")
    else:
        print("No fue necesario realizar ninguna migración.")

    print("\n--- Resumen de la Migración ---")
    print(f"Órdenes arregladas: {migrated_count}")
    print(f"Órdenes que ya estaban correctas: {already_ok_count}")
    print(f"Total de órdenes revisadas: {len(orders_to_migrate)}")
    print("---------------------------------")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        run_migration(db)
    except Exception as e:
        print(f"\n❌ Ocurrió un error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
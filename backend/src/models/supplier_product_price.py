# backend/src/models/supplier_product_price.py
import datetime
# --- DateTime ahora se importa desde sqlalchemy ---
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Numeric, Text
# -----------------------------------------------
from sqlalchemy.orm import relationship
from .base import Base
# from .supplier import Supplier
# from .warehouse import Warehouse

class SupplierProductPrice(Base):
    """
    Modelo para almacenar los precios ofrecidos por proveedores
    para productos específicos, independiente del stock actual.
    Utilizado para comparación de precios.
    """
    __tablename__ = "supplier_product_prices"

    id = Column(Integer, primary_key=True, index=True) # index=True está bien

    # --- MODIFICADO: Añadir index=True ---
    product_name = Column(String(255), index=True, nullable=False)
    # -----------------------------------

    # --- MODIFICADO: Añadir index=True ---
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True, nullable=False)
    # -----------------------------------
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True) # Opcional

    price = Column(Numeric(10, 2), nullable=False) # OK
    discount = Column(Numeric(5, 2), default=0.0, nullable=False) # OK, mantenemos nullable=False

    # --- MODIFICADO: Añadir timezone=True ---
    last_updated = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc))
    # ------------------------------------

    # Relaciones
    # Asegúrate que Supplier/Warehouse tienen relaciones inversas si usas back_populates
    supplier = relationship("Supplier") # Asume relación simple o configúrala con back_populates
    warehouse = relationship("Warehouse") # Asume relación simple o configúrala con back_populates

    def __repr__(self):
        return f"<SupplierProductPrice(id={self.id}, product='{self.product_name}', supplier_id={self.supplier_id}, price={self.price})>"
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class MachinePrediction(Base):
    """Predicciones de mantenimiento generadas por IA"""
    __tablename__ = "machine_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_type = Column(String(50), nullable=False, default='failure')  # 'failure', 'maintenance', 'optimization'
    
    # Datos de la predicción
    probability = Column(Float, CheckConstraint('probability >= 0 AND probability <= 100'))  # Probabilidad de fallo (0-100%)
    confidence = Column(Float, CheckConstraint('confidence >= 0 AND confidence <= 100'))   # Confianza del modelo (0-100%)
    predicted_date = Column(DateTime, nullable=True, index=True)  # Fecha predicha del evento
    
    # Detalles de la predicción (almacenados como JSON)
    prediction_data = Column(JSON, nullable=True)  # Datos completos de la predicción
    components_at_risk = Column(JSON, nullable=True)  # Lista de componentes en riesgo
    recommended_actions = Column(JSON, nullable=True)  # ✅ CORREGIDO
    # Metadatos del modelo
    model_used = Column(String(100), nullable=True)  # Modelo de IA usado (ej: 'llama3:8b')
    data_points_used = Column(Integer, nullable=True)  # Cantidad de datos históricos usados
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Estado de la predicción
    status = Column(String(20), default="active", index=True)  # active, validated, expired, cancelled
    actual_outcome = Column(String(50), nullable=True)  # correct, false_positive, false_negative
    outcome_date = Column(DateTime, nullable=True)
    
    # Relaciones
    machine = relationship("Machine")
    created_by = relationship("User")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'validated', 'expired', 'cancelled')", name='check_prediction_status'),
        CheckConstraint("actual_outcome IN ('correct', 'false_positive', 'false_negative') OR actual_outcome IS NULL", name='check_actual_outcome'),
    )

class MaintenanceOptimization(Base):
    """Optimizaciones de cronogramas generadas por IA"""
    __tablename__ = "maintenance_optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Cronograma original vs optimizado
    original_schedule = Column(JSON, nullable=False)
    optimized_schedule = Column(JSON, nullable=False)
    optimization_criteria = Column(JSON, nullable=True)
    
    # Métricas de mejora
    estimated_downtime_reduction = Column(Float, nullable=True)  # Horas ahorradas
    cost_savings = Column(Float, nullable=True)  # Ahorro estimado en euros
    efficiency_improvement = Column(Float, nullable=True)  # % de mejora
    
    # Metadatos
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    generated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending, approved, implemented, rejected
    
    # Relaciones
    section = relationship("Section")
    generated_by = relationship("User")    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'implemented', 'rejected')", name='check_optimization_status'),
    )

class FailurePattern(Base):
    """Patrones de fallo identificados por IA"""
    __tablename__ = "failure_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Máquinas y códigos afectados
    machines_affected = Column(JSON, nullable=True)  # Lista de IDs de máquinas
    failure_codes = Column(JSON, nullable=True)      # Códigos de fallo relacionados
    
    # Análisis del patrón
    frequency = Column(String(50), nullable=True)    # daily, weekly, monthly, seasonal, random
    conditions = Column(JSON, nullable=True)         # Condiciones que disparan el patrón
    root_causes = Column(JSON, nullable=True)        # Causas raíz identificadas
    
    # Recomendaciones
    preventive_actions = Column(JSON, nullable=True)
    recommended_frequency = Column(String(50), nullable=True)
    estimated_impact = Column(Float, nullable=True)
    
    # Validación del patrón
    confidence_score = Column(Float, CheckConstraint('confidence_score >= 0 AND confidence_score <= 100'))
    occurrences_analyzed = Column(Integer, nullable=True)
    last_occurrence = Column(DateTime, nullable=True)
    
    # Metadatos
    discovered_at = Column(DateTime, default=datetime.utcnow, index=True)
    discovered_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="active", index=True)  # active, validated, obsolete
    
    # Relaciones
    discovered_by = relationship("User")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("frequency IN ('daily', 'weekly', 'monthly', 'seasonal', 'random') OR frequency IS NULL", name='check_pattern_frequency'),
        CheckConstraint("status IN ('active', 'validated', 'obsolete')", name='check_pattern_status'),
    )

class AIModelPerformance(Base):
    """Tracking del rendimiento de los modelos de IA"""
    __tablename__ = "ai_model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=True)
    
    # Métricas de rendimiento
    accuracy = Column(Float, CheckConstraint('accuracy >= 0 AND accuracy <= 100'))          # Precisión general
    precision_score = Column(Float, CheckConstraint('precision_score >= 0 AND precision_score <= 100')) # Precisión de predicciones positivas
    recall_score = Column(Float, CheckConstraint('recall_score >= 0 AND recall_score <= 100'))    # Cobertura de casos reales
    f1_score = Column(Float, CheckConstraint('f1_score >= 0 AND f1_score <= 100'))          # Media armónica de precisión y recall
    
    # Datos de evaluación
    predictions_made = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    
    # Período de evaluación
    evaluation_period_start = Column(DateTime, nullable=False, index=True)
    evaluation_period_end = Column(DateTime, nullable=False, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Notas y observaciones
    notes = Column(Text, nullable=True)
    improvements_needed = Column(Text, nullable=True)

class AIConfiguration(Base):
    """Configuración global del sistema de IA"""
    __tablename__ = "ai_configuration"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), nullable=False, unique=True, index=True)
    config_value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    config_type = Column(String(50), nullable=False, default='general', index=True)  # 'model', 'prediction', 'performance', 'general'
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relaciones
    updated_by = relationship("User")
    
    @classmethod
    def get_config(cls, session, key, default=None):
        """Método helper para obtener configuración"""
        config = session.query(cls).filter(cls.config_key == key).first()
        return config.config_value if config else default
    
    @classmethod
    def set_config(cls, session, key, value, description=None, config_type='general', user_id=None):
        """Método helper para establecer configuración"""
        config = session.query(cls).filter(cls.config_key == key).first()
        if config:
            config.config_value = value
            config.updated_by_id = user_id
            if description:
                config.description = description
        else:
            config = cls(
                config_key=key,
                config_value=value,
                description=description,
                config_type=config_type,
                updated_by_id=user_id
            )
            session.add(config)
        session.commit()
        return config
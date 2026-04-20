from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class HCP(Base):
    __tablename__ = "hcps"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(255), nullable=False)
    specialty     = Column(String(255))
    hospital      = Column(String(255))
    city          = Column(String(100))
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    notes         = Column(Text)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())
    interactions  = relationship("Interaction", back_populates="hcp")

class Interaction(Base):
    __tablename__ = "interactions"
    id                = Column(Integer, primary_key=True, autoincrement=True)
    hcp_id            = Column(Integer, ForeignKey("hcps.id", ondelete="CASCADE"))
    rep_name          = Column(String(255), default="Field Rep")
    interaction_date  = Column(Date, nullable=False)
    mode              = Column(String(50))        
    product_discussed = Column(String(255))
    key_topics        = Column(Text)
    sentiment         = Column(String(50))        
    materials_shared  = Column(String(255))       
    outcome           = Column(Text)       
    follow_up_date    = Column(Date)
    follow_up_notes   = Column(Text)
    raw_notes         = Column(Text)              
    ai_summary        = Column(Text)              
    entities_json     = Column(JSON)              
    compliance_flag   = Column(String(50))        
    next_best_action  = Column(Text)              
    source            = Column(String(20), default="chat")
    status            = Column(String(50), default="completed")
    created_at        = Column(DateTime, server_default=func.now())
    updated_at        = Column(DateTime, server_default=func.now(), onupdate=func.now())
    hcp               = relationship("HCP", back_populates="interactions")

class Followup(Base):
    __tablename__ = "followups"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True)
    hcp_id         = Column(Integer, ForeignKey("hcps.id", ondelete="CASCADE"), nullable=False)
    due_date       = Column(Date, nullable=False)
    notes          = Column(Text)
    status         = Column(String(50), default="pending")   
    created_at     = Column(DateTime, server_default=func.now())

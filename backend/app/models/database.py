from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    video_path = Column(String)
    thumbnail_path = Column(String, nullable=True)
    status = Column(String, default="processing")  # processing, ready, error
    emotional_vibe = Column(String)  # luxury, energy, drama, etc
    estimated_duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoAnalysis(Base):
    __tablename__ = "video_analysis"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    emotional_analysis = Column(JSON)
    visual_style = Column(String)
    detected_aesthetic = Column(String)
    color_palette = Column(JSON)
    pacing_analysis = Column(JSON)
    retention_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EditingTask(Base):
    __tablename__ = "editing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    task_type = Column(String)  # silence_removal, color_grading, subtitles, etc
    status = Column(String, default="pending")  # pending, processing, completed, error
    progress = Column(Float, default=0.0)
    result_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Reference(Base):
    __tablename__ = "references"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    reference_type = Column(String)  # visual, audio, style
    file_path = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

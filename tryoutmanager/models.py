#!/usr/bin/env python3.6

import os
import uuid
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Table, \
                       ForeignKey, Enum, Index
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

db = sa.create_engine(os.environ['DATABASE_URL'])
metadata = sa.MetaData()

Base = declarative_base(metadata)
Session = sessionmaker(bind=db)


# Association tables for many-to-many relationships
markers_challenges = Table(
        'markers_challenges',
        Base.metadata,
        Column('marker_email', String, ForeignKey('markers.email')),
        Column('challenge_id', UUID, ForeignKey('challenges.id')))

challenges_submissions = Table(
        'challenges_submissions',
        Base.metadata,
        Column(
            'challenge_id',
            UUID,
            ForeignKey('challenges.id')),
        Column(
            'submission_id',
            UUID,
            ForeignKey('submissions.id')))


# Tables corresponding to concrete models
class AdminUser(Base):
    __tablename__ = 'admin_users'

    email = Column(String, nullable=False, unique=True, primary_key=True)
    password = Column(String, nullable=False)
    github_slug = Column(String)
    public_keys = relationship('AdminUserPublicKey', back_populates='user')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Marker(Base):
    __tablename__ = 'markers'

    email = Column(String, nullable=False, unique=True, primary_key=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    challenges = relationship(
            'Challenges',
            secondary=markers_challenges,
            back_populates='markers')
    github_slug = Column(String)
    public_keys = relationship('MarkerPublicKey', back_populates='user')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class User(Base):
    __tablename__ = 'users'

    email = Column(String, primary_key=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    github_slug = Column(String)
    public_keys = relationship('UserPublicKey', back_populates='user')
    confirmed = Column(Boolean, nullable=False, default=False)
    email_confirmation_slug = Column(String, unique=True)
    email_confirmation_expiry = Column(DateTime(timezone=True))


class UserKey(Base):
    __tablename__ = 'user_keys'

    key = Column(String, nullable=False, primary_key=True)
    owner = relationship('User', back_populates='public_keys')
    owner_email = Column(String, ForeignKey('users.email'), nullable=False)


class MarkerKey(Base):
    __tablename__ = 'marker_keys'

    key = Column(String, nullable=False, primary_key=True)
    owner = relationship('Marker', back_populates='public_keys')
    owner_email = Column(String, ForeignKey('markers.email'), nullable=False)


class AdminUserKey(Base):
    __tablename__ = 'admin_user_keys'

    key = Column(String, nullable=False, primary_key=True)
    owner = relationship('AdminUser', back_populates='public_keys')
    owner_email = Column(
                    String,
                    ForeignKey('admin_users.email'),
                    nullable=False)


class Challenge(Base):
    __tablename__ = 'challenges'

    id = Column(UUID, default=uuid.uuid4, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    repository = Column(String, nullable=False, unique=True)
    markers = relationship(
            'Marker',
            secondary=markers_challenges,
            back_populates='challenges')
    submissions = relationship(
            'Submission',
            secondary=challenges_submissions,
            back_populates='submissions')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Submission(Base):
    __tablename__ = 'submissions'

    id = Column(UUID, default=uuid.uuid4, primary_key=True)
    contestant = relationship('User', back_populates='submissions')
    contestant_email = Column(
            String, ForeignKey('users.email'), nullable=False)
    challenge = relationship('Challenge', back_populates='submissions')
    challenge_id = Column(UUID, ForeignKey('challenges.id'), nullable=False)
    reservation = relationship('Reservation')
    status = Column(
            Enum(
                'in_progress',
                'late',
                'submitted',
                name='submission_status'),
            default='closed', nullable=False)

    # A contestant may only have one submission per challenge
    __table_args__ = (
                Index(
                    'index_submissions_on_contestant_and_challenge',
                    'contestant_email', 'challenge_id', unique=True),
            )


class Reservation(Base):
    __tablename__ = 'reservations'

    id = Column(UUID, default=uuid.uuid4, primary_key=True)
    submission = relationship(
            'Submission', back_populates='reservation', uselist=False)
    submission_id = Column(UUID, ForeignKey('submissions.id'), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    closes_at = Column(DateTime(timezone=True), nullable=False)
    cancelled = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
            Enum(
                'open',
                'closed',
                'cancelled',
                name='reservation_status'),
            default='closed', nullable=False)
    created_at = Column(
            DateTime(timezone=True), nullable=False, default=datetime.utcnow)


if __name__ == '__main__':
    Base.metadata.create_all(db)

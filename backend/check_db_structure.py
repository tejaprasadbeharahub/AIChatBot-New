#!/usr/bin/env python3
from sqlalchemy import inspect, create_engine, text
from app.core.config import settings

engine = create_engine(settings.supabase_database_url or settings.database_url)

with engine.connect() as conn:
    # Check for triggers
    result = conn.execute(text("SELECT trigger_name, event_manipulation, event_object_table FROM information_schema.triggers WHERE event_object_table='farm_tickets' LIMIT 10"))
    triggers = result.fetchall()
    print(f"Triggers on farm_tickets: {triggers if triggers else 'None'}")
    
    # Check for rules
    result = conn.execute(text("SELECT rule_name, event FROM information_schema.rules WHERE table_name='farm_tickets' LIMIT 10"))
    rules = result.fetchall()
    print(f"Rules on farm_tickets: {rules if rules else 'None'}")
    
    # Get table structure
    inspector = inspect(engine)
    columns = inspector.get_columns('farm_tickets')
    print(f"\nfarm_tickets columns: {[col['name'] for col in columns]}")
